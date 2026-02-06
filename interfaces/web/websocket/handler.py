"""WebSocket 핸들러 - 실시간 채팅 및 그래프 업데이트."""

import json
import asyncio
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect

from core.orchestrator import Orchestrator
from ..services.graph_service import graph_service
from ..services.node_extractor import NodeExtractor


class ConnectionManager:
    """WebSocket 연결 관리자."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """새 연결 수락."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """연결 종료."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, websocket: WebSocket, message: dict):
        """특정 클라이언트에 메시지 전송."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """모든 클라이언트에 메시지 브로드캐스트."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


class WebSocketHandler:
    """WebSocket 메시지 처리 핸들러."""

    def __init__(self):
        self.manager = ConnectionManager()
        self.orchestrators: dict[str, Orchestrator] = {}
        self.node_extractor = NodeExtractor(graph_service)
        self._greeted_sessions: set[str] = set()  # 인사 완료한 세션

    def _get_or_create_orchestrator(self, session_id: str) -> Orchestrator:
        """세션별 Orchestrator 반환."""
        if session_id not in self.orchestrators:
            self.orchestrators[session_id] = Orchestrator()
        return self.orchestrators[session_id]

    async def handle_connection(self, websocket: WebSocket, session_id: str):
        """WebSocket 연결 처리."""
        await self.manager.connect(websocket)

        try:
            # 연결 시 현재 그래프 데이터 전송
            await self.manager.send_message(websocket, {
                "type": "graph_init",
                "data": graph_service.get_graph_data().model_dump()
            })

            # AI 첫 인사 메시지
            await self._send_greeting(websocket, session_id)

            while True:
                # 메시지 수신
                data = await websocket.receive_json()
                await self._handle_message(websocket, session_id, data)

        except WebSocketDisconnect:
            self.manager.disconnect(websocket)
        except Exception as e:
            await self.manager.send_message(websocket, {
                "type": "error",
                "message": str(e)
            })
            self.manager.disconnect(websocket)

    async def _handle_message(self, websocket: WebSocket, session_id: str, data: dict):
        """수신된 메시지 처리."""
        msg_type = data.get("type")

        if msg_type == "chat":
            await self._handle_chat(websocket, session_id, data.get("message", ""))
        elif msg_type == "get_graph":
            await self._send_graph_data(websocket)
        elif msg_type == "get_cost":
            await self._send_cost_info(websocket, session_id)
        elif msg_type == "clear_history":
            self._clear_session(session_id)
            await self.manager.send_message(websocket, {
                "type": "history_cleared"
            })

    async def _handle_chat(self, websocket: WebSocket, session_id: str, message: str):
        """채팅 메시지 처리."""
        if not message.strip():
            return

        orchestrator = self._get_or_create_orchestrator(session_id)

        # 사용자 메시지에서 노드 추출
        user_nodes = self.node_extractor.extract_from_user_message(message)
        for node in user_nodes:
            await self._broadcast_new_node(node)

        # 처리 시작 알림
        await self.manager.send_message(websocket, {
            "type": "processing",
            "status": "started"
        })

        try:
            # Orchestrator로 처리
            response = await orchestrator.process(message)

            # AI 응답에서 노드 추출
            response_nodes = self.node_extractor.extract_from_assistant_response(response)
            for node in response_nodes:
                await self._broadcast_new_node(node)

            # 응답 전송
            await self.manager.send_message(websocket, {
                "type": "response",
                "message": response
            })

            # 비용 정보 전송
            await self._send_cost_info(websocket, session_id)

        except Exception as e:
            await self.manager.send_message(websocket, {
                "type": "error",
                "message": f"처리 중 오류: {str(e)}"
            })

        finally:
            await self.manager.send_message(websocket, {
                "type": "processing",
                "status": "completed"
            })

    async def _send_graph_data(self, websocket: WebSocket):
        """그래프 데이터 전송."""
        await self.manager.send_message(websocket, {
            "type": "graph_update",
            "data": graph_service.get_graph_data().model_dump()
        })

    async def _send_cost_info(self, websocket: WebSocket, session_id: str):
        """비용 정보 전송."""
        orchestrator = self._get_or_create_orchestrator(session_id)
        cost_info = orchestrator.get_cost_info()

        await self.manager.send_message(websocket, {
            "type": "cost_update",
            "data": cost_info
        })

    async def _broadcast_new_node(self, node):
        """새 노드 브로드캐스트."""
        await self.manager.broadcast({
            "type": "node_added",
            "node": node.to_graph_node()
        })

        # 약간의 딜레이로 애니메이션 효과
        await asyncio.sleep(0.1)

        # 전체 그래프 업데이트도 전송
        await self.manager.broadcast({
            "type": "graph_update",
            "data": graph_service.get_graph_data().model_dump()
        })

    def _clear_session(self, session_id: str):
        """세션 초기화."""
        if session_id in self.orchestrators:
            self.orchestrators[session_id].clear_history()
        self._greeted_sessions.discard(session_id)

    async def _send_greeting(self, websocket: WebSocket, session_id: str):
        """연결 시 AI 첫 인사 메시지 전송 (세션당 1회)."""
        # 이미 인사한 세션이면 스킵
        if session_id in self._greeted_sessions:
            return

        self._greeted_sessions.add(session_id)

        # 클라이언트 준비 대기
        await asyncio.sleep(0.3)

        greeting = "안녕하세요! 저는 당신의 Second Brain입니다.\n\n무엇이든 물어보세요. 대화하면서 지식 그래프가 만들어집니다."

        # 인사 노드 생성
        from ..models.node import NodeType
        greeting_node, _ = graph_service.find_or_create_node(
            NodeType.INSIGHT,
            label="대화 시작",
            content="새로운 세션이 시작되었습니다"
        )
        await self._broadcast_new_node(greeting_node)

        # 인사 메시지 전송
        await self.manager.send_message(websocket, {
            "type": "response",
            "message": greeting
        })


# 전역 핸들러 인스턴스
ws_handler = WebSocketHandler()
