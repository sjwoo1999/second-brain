"""WebSocket 핸들러 단위 테스트."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from interfaces.web.websocket.handler import ConnectionManager, WebSocketHandler


class TestConnectionManager:
    """ConnectionManager 테스트."""

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect(self, manager):
        """연결 수락."""
        ws = AsyncMock()
        await manager.connect(ws)
        assert ws in manager.active_connections
        ws.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, manager):
        """연결 종료."""
        ws = AsyncMock()
        manager.active_connections.append(ws)
        manager.disconnect(ws)
        assert ws not in manager.active_connections

    def test_disconnect_not_connected(self, manager):
        """연결되지 않은 소켓 종료 → 에러 없음."""
        ws = AsyncMock()
        manager.disconnect(ws)  # no error

    @pytest.mark.asyncio
    async def test_send_message(self, manager):
        """메시지 전송."""
        ws = AsyncMock()
        await manager.send_message(ws, {"type": "test"})
        ws.send_json.assert_awaited_once_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """브로드캐스트."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections = [ws1, ws2]
        await manager.broadcast({"type": "update"})
        ws1.send_json.assert_awaited_once()
        ws2.send_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_error_ignored(self, manager):
        """브로드캐스트 중 에러 무시."""
        ws1 = AsyncMock()
        ws1.send_json.side_effect = Exception("연결 끊김")
        ws2 = AsyncMock()
        manager.active_connections = [ws1, ws2]
        await manager.broadcast({"type": "update"})
        ws2.send_json.assert_awaited_once()  # ws2는 정상 전송


class TestWebSocketHandler:
    """WebSocketHandler 테스트."""

    @pytest.fixture
    def handler(self):
        with patch("interfaces.web.websocket.handler.graph_service") as mock_gs, \
             patch("interfaces.web.websocket.handler.memory_service") as mock_ms, \
             patch("interfaces.web.websocket.handler.memory_extractor") as mock_me:
            mock_gs.get_graph_data.return_value = MagicMock(
                model_dump=lambda: {"nodes": [], "links": []}
            )
            mock_gs.find_or_create_node.return_value = (MagicMock(), True)
            mock_ms.get_stats.return_value = MagicMock(active=0, model_dump=lambda: {})
            mock_ms.save_conversation = MagicMock()
            mock_me.extract_and_save = AsyncMock(return_value=[])

            h = WebSocketHandler()
            h.manager = MagicMock(spec=ConnectionManager)
            h.manager.connect = AsyncMock()
            h.manager.send_message = AsyncMock()
            h.manager.broadcast = AsyncMock()
            h.manager.disconnect = MagicMock()

            yield h

    def test_get_or_create_orchestrator_new(self, handler):
        """새 세션 Orchestrator 생성."""
        with patch("interfaces.web.websocket.handler.Orchestrator") as mock_orch_cls:
            orch = handler._get_or_create_orchestrator("new-session")
            mock_orch_cls.assert_called_once()
            assert "new-session" in handler.orchestrators

    def test_get_or_create_orchestrator_existing(self, handler):
        """기존 세션 Orchestrator 반환."""
        mock_orch = MagicMock()
        handler.orchestrators["existing"] = mock_orch
        result = handler._get_or_create_orchestrator("existing")
        assert result is mock_orch

    @pytest.mark.asyncio
    async def test_handle_message_chat(self, handler):
        """chat 타입 메시지 처리."""
        handler._handle_chat = AsyncMock()
        ws = AsyncMock()
        await handler._handle_message(ws, "s1", {"type": "chat", "message": "hello"})
        handler._handle_chat.assert_awaited_once_with(ws, "s1", "hello")

    @pytest.mark.asyncio
    async def test_handle_message_get_graph(self, handler):
        """get_graph 타입 메시지 처리."""
        handler._send_graph_data = AsyncMock()
        ws = AsyncMock()
        await handler._handle_message(ws, "s1", {"type": "get_graph"})
        handler._send_graph_data.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_message_get_cost(self, handler):
        """get_cost 타입 메시지 처리."""
        handler._send_cost_info = AsyncMock()
        ws = AsyncMock()
        await handler._handle_message(ws, "s1", {"type": "get_cost"})
        handler._send_cost_info.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_message_clear_history(self, handler):
        """clear_history 타입 메시지 처리."""
        handler._clear_session = MagicMock()
        ws = AsyncMock()
        await handler._handle_message(ws, "s1", {"type": "clear_history"})
        handler._clear_session.assert_called_once_with("s1")
        handler.manager.send_message.assert_awaited()

    @pytest.mark.asyncio
    async def test_handle_chat_empty_message(self, handler):
        """빈 메시지 스킵."""
        ws = AsyncMock()
        handler._get_or_create_orchestrator = MagicMock()
        await handler._handle_chat(ws, "s1", "   ")
        handler._get_or_create_orchestrator.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_chat_success(self, handler):
        """채팅 성공 흐름."""
        ws = AsyncMock()
        mock_orch = MagicMock()
        mock_orch.process = AsyncMock(return_value="응답입니다")
        mock_orch.get_cost_info.return_value = {}
        handler._get_or_create_orchestrator = MagicMock(return_value=mock_orch)
        handler.node_extractor = MagicMock()
        handler.node_extractor.extract_from_user_message.return_value = []
        handler.node_extractor.extract_from_assistant_response.return_value = []

        with patch("interfaces.web.websocket.handler.memory_service") as mock_ms, \
             patch("interfaces.web.websocket.handler.memory_extractor"), \
             patch("asyncio.create_task"):
            mock_ms.save_conversation = MagicMock()
            await handler._handle_chat(ws, "s1", "안녕하세요")

        # processing started + response + cost_update + processing completed
        assert handler.manager.send_message.await_count >= 3

    @pytest.mark.asyncio
    async def test_handle_chat_error(self, handler):
        """채팅 처리 중 에러."""
        ws = AsyncMock()
        mock_orch = MagicMock()
        mock_orch.process = AsyncMock(side_effect=Exception("API 오류"))
        handler._get_or_create_orchestrator = MagicMock(return_value=mock_orch)
        handler.node_extractor = MagicMock()
        handler.node_extractor.extract_from_user_message.return_value = []

        await handler._handle_chat(ws, "s1", "테스트")
        # error message sent
        error_calls = [
            call for call in handler.manager.send_message.call_args_list
            if call[0][1].get("type") == "error"
        ]
        assert len(error_calls) >= 1

    def test_clear_session(self, handler):
        """세션 초기화."""
        mock_orch = MagicMock()
        handler.orchestrators["s1"] = mock_orch
        handler._greeted_sessions.add("s1")

        handler._clear_session("s1")
        mock_orch.clear_history.assert_called_once()
        assert "s1" not in handler._greeted_sessions

    def test_clear_session_not_exists(self, handler):
        """존재하지 않는 세션 초기화 → 에러 없음."""
        handler._clear_session("nonexistent")

    @pytest.mark.asyncio
    async def test_send_graph_data(self, handler):
        """그래프 데이터 전송."""
        with patch("interfaces.web.websocket.handler.graph_service") as mock_gs:
            mock_gs.get_graph_data.return_value = MagicMock(
                model_dump=lambda: {"nodes": [], "links": []}
            )
            ws = AsyncMock()
            await handler._send_graph_data(ws)
            handler.manager.send_message.assert_awaited_once()
            msg = handler.manager.send_message.call_args[0][1]
            assert msg["type"] == "graph_update"

    @pytest.mark.asyncio
    async def test_send_cost_info(self, handler):
        """비용 정보 전송."""
        mock_orch = MagicMock()
        mock_orch.get_cost_info.return_value = {"total": 0}
        handler._get_or_create_orchestrator = MagicMock(return_value=mock_orch)

        ws = AsyncMock()
        with patch("interfaces.web.websocket.handler.Orchestrator"):
            await handler._send_cost_info(ws, "s1")
        handler.manager.send_message.assert_awaited_once()
        msg = handler.manager.send_message.call_args[0][1]
        assert msg["type"] == "cost_update"

    @pytest.mark.asyncio
    async def test_broadcast_new_node(self, handler):
        """새 노드 브로드캐스트."""
        with patch("interfaces.web.websocket.handler.graph_service") as mock_gs, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_gs.get_graph_data.return_value = MagicMock(
                model_dump=lambda: {"nodes": [], "links": []}
            )
            node = MagicMock()
            node.to_graph_node.return_value = {"id": "n1", "label": "test"}
            await handler._broadcast_new_node(node)
            assert handler.manager.broadcast.await_count == 2  # node_added + graph_update

    @pytest.mark.asyncio
    async def test_send_greeting_first_time(self, handler):
        """첫 인사 메시지 전송."""
        with patch("interfaces.web.websocket.handler.memory_service") as mock_ms, \
             patch("interfaces.web.websocket.handler.graph_service") as mock_gs, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_ms.get_stats.return_value = MagicMock(active=0)
            mock_node = MagicMock()
            mock_gs.find_or_create_node.return_value = (mock_node, True)
            mock_gs.get_graph_data.return_value = MagicMock(
                model_dump=lambda: {"nodes": [], "links": []}
            )

            ws = AsyncMock()
            await handler._send_greeting(ws, "new-session")
            assert "new-session" in handler._greeted_sessions

    @pytest.mark.asyncio
    async def test_send_greeting_already_greeted(self, handler):
        """이미 인사한 세션 → 스킵."""
        handler._greeted_sessions.add("s1")
        ws = AsyncMock()
        await handler._send_greeting(ws, "s1")
        handler.manager.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_greeting_with_memories(self, handler):
        """메모리가 있는 경우 인사."""
        with patch("interfaces.web.websocket.handler.memory_service") as mock_ms, \
             patch("interfaces.web.websocket.handler.graph_service") as mock_gs, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_ms.get_stats.return_value = MagicMock(active=5)
            mock_node = MagicMock()
            mock_gs.find_or_create_node.return_value = (mock_node, True)
            mock_gs.get_graph_data.return_value = MagicMock(
                model_dump=lambda: {"nodes": [], "links": []}
            )

            ws = AsyncMock()
            await handler._send_greeting(ws, "mem-session")
            # 인사 메시지에 메모리 수 포함
            greeting_call = [
                c for c in handler.manager.send_message.call_args_list
                if c[0][1].get("type") == "response"
            ]
            assert len(greeting_call) >= 1
            assert "5" in greeting_call[0][0][1]["message"]

    @pytest.mark.asyncio
    async def test_extract_memory_success(self, handler):
        """메모리 추출 성공."""
        with patch("interfaces.web.websocket.handler.memory_extractor") as mock_me, \
             patch("interfaces.web.websocket.handler.memory_service") as mock_ms:
            mock_me.extract_and_save = AsyncMock(return_value=[{"summary": "test"}])
            mock_ms.get_stats.return_value = MagicMock(model_dump=lambda: {"total": 1})

            ws = AsyncMock()
            await handler._extract_memory(ws, "msg", "resp")
            # memory_added + memory_stats
            assert handler.manager.send_message.await_count == 2

    @pytest.mark.asyncio
    async def test_extract_memory_none(self, handler):
        """메모리 추출 결과 없음."""
        with patch("interfaces.web.websocket.handler.memory_extractor") as mock_me:
            mock_me.extract_and_save = AsyncMock(return_value=[])

            ws = AsyncMock()
            await handler._extract_memory(ws, "msg", "resp")
            handler.manager.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_extract_memory_error_ignored(self, handler):
        """메모리 추출 에러 무시."""
        with patch("interfaces.web.websocket.handler.memory_extractor") as mock_me:
            mock_me.extract_and_save = AsyncMock(side_effect=Exception("오류"))

            ws = AsyncMock()
            await handler._extract_memory(ws, "msg", "resp")
            # 에러 발생해도 무시됨 (pass)
