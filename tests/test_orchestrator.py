"""Orchestrator 단위 테스트."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from core.orchestrator import Orchestrator
from core.base_tool import ToolResult


@pytest.fixture
def mock_deps():
    """Orchestrator 의존성 mock."""
    with patch("core.orchestrator.Anthropic") as mock_anthropic_cls, \
         patch("core.orchestrator.memory_service") as mock_memory, \
         patch("core.orchestrator.cache_service") as mock_cache, \
         patch("core.orchestrator.cost_tracker") as mock_cost, \
         patch("core.orchestrator.model_router") as mock_router, \
         patch("core.orchestrator.summarizer") as mock_summarizer:

        mock_memory.build_context.return_value = ""
        mock_cache.get.return_value = None
        mock_summarizer.summarize_history.side_effect = lambda h: h

        mock_routing = MagicMock()
        mock_routing.model = "claude-sonnet"
        mock_router.route.return_value = mock_routing

        mock_usage = MagicMock()
        mock_usage.model = "claude-sonnet"
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20
        mock_usage.cost_usd = 0.001
        mock_usage.cached = False
        mock_usage.from_local_cache = False
        mock_cost.track_usage.return_value = mock_usage

        client_instance = mock_anthropic_cls.return_value
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.text = "테스트 응답"
        text_block.type = "text"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.usage.cache_creation_input_tokens = 0
        mock_response.usage.cache_read_input_tokens = 0
        client_instance.messages.create.return_value = mock_response

        orchestrator = Orchestrator(api_key="test-key")

        yield {
            "orchestrator": orchestrator,
            "client": client_instance,
            "memory": mock_memory,
            "cache": mock_cache,
            "cost": mock_cost,
            "router": mock_router,
            "summarizer": mock_summarizer,
            "response": mock_response,
        }


class TestOrchestratorInit:
    """초기화 테스트."""

    def test_init_with_api_key(self):
        """API 키로 초기화."""
        with patch("core.orchestrator.Anthropic"):
            orch = Orchestrator(api_key="test-key")
            assert orch.api_key == "test-key"
            assert orch.conversation_history == []

    def test_init_without_api_key_raises(self):
        """API 키 없이 초기화 시 에러."""
        with patch.dict("os.environ", {}, clear=True), \
             patch("core.orchestrator.Anthropic"):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                Orchestrator(api_key=None)

    def test_init_with_env_key(self):
        """환경변수로 초기화."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}), \
             patch("core.orchestrator.Anthropic"):
            orch = Orchestrator()
            assert orch.api_key == "env-key"


class TestOrchestratorSystemPrompt:
    """시스템 프롬프트 생성 테스트."""

    def test_build_system_prompt_no_memory(self, mock_deps):
        """메모리 없으면 기본 프롬프트만."""
        orch = mock_deps["orchestrator"]
        mock_deps["memory"].build_context.return_value = ""
        result = orch._build_system_prompt("hello")
        assert result == orch.base_system_prompt

    def test_build_system_prompt_with_memory(self, mock_deps):
        """메모리 있으면 기본 프롬프트 + 메모리."""
        orch = mock_deps["orchestrator"]
        mock_deps["memory"].build_context.return_value = "[Memory] Python 선호"
        result = orch._build_system_prompt("hello")
        assert orch.base_system_prompt in result
        assert "[Memory] Python 선호" in result

    def test_get_system_config_caching_enabled(self, mock_deps):
        """프롬프트 캐싱 활성화 시 블록 리스트 반환."""
        orch = mock_deps["orchestrator"]
        from config.settings import settings
        original = settings.cost_optimization.prompt_caching_enabled
        try:
            settings.cost_optimization.prompt_caching_enabled = True
            result = orch._get_system_config("test")
            assert isinstance(result, list)
            assert result[0]["cache_control"] == {"type": "ephemeral"}
        finally:
            settings.cost_optimization.prompt_caching_enabled = original

    def test_get_system_config_caching_disabled(self, mock_deps):
        """프롬프트 캐싱 비활성화 시 문자열 반환."""
        orch = mock_deps["orchestrator"]
        from config.settings import settings
        original = settings.cost_optimization.prompt_caching_enabled
        try:
            settings.cost_optimization.prompt_caching_enabled = False
            result = orch._get_system_config("test")
            assert isinstance(result, str)
        finally:
            settings.cost_optimization.prompt_caching_enabled = original

    def test_get_system_config_with_memory_block(self, mock_deps):
        """메모리 컨텍스트가 있으면 블록이 2개."""
        orch = mock_deps["orchestrator"]
        mock_deps["memory"].build_context.return_value = "메모리 컨텍스트"
        from config.settings import settings
        original = settings.cost_optimization.prompt_caching_enabled
        try:
            settings.cost_optimization.prompt_caching_enabled = True
            result = orch._get_system_config("test")
            assert len(result) == 2
        finally:
            settings.cost_optimization.prompt_caching_enabled = original


class TestOrchestratorProcess:
    """process() 메인 플로우 테스트."""

    @pytest.mark.asyncio
    async def test_process_basic(self, mock_deps):
        """기본 처리 흐름."""
        orch = mock_deps["orchestrator"]
        result = await orch.process("안녕하세요")
        assert result == "테스트 응답"
        assert len(orch.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_process_cache_hit(self, mock_deps):
        """캐시 히트 시 API 호출 없이 반환."""
        orch = mock_deps["orchestrator"]
        cached = MagicMock()
        cached.model = "claude-sonnet"
        cached.response = "캐시된 응답"
        mock_deps["cache"].get.return_value = cached

        result = await orch.process("캐시 테스트")
        assert result == "캐시된 응답"
        mock_deps["client"].messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_tracks_usage(self, mock_deps):
        """사용량 추적 호출."""
        orch = mock_deps["orchestrator"]
        await orch.process("테스트")
        mock_deps["cost"].track_usage.assert_called()

    @pytest.mark.asyncio
    async def test_process_saves_to_cache(self, mock_deps):
        """응답을 캐시에 저장."""
        orch = mock_deps["orchestrator"]
        await orch.process("저장 테스트")
        mock_deps["cache"].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_uses_model_routing(self, mock_deps):
        """모델 라우팅 사용."""
        orch = mock_deps["orchestrator"]
        await orch.process("라우팅 테스트")
        mock_deps["router"].route.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_uses_summarizer(self, mock_deps):
        """대화 요약기 사용."""
        orch = mock_deps["orchestrator"]
        await orch.process("요약 테스트")
        mock_deps["summarizer"].summarize_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_conversation_history_grows(self, mock_deps):
        """대화 기록 누적."""
        orch = mock_deps["orchestrator"]
        await orch.process("첫 번째")
        await orch.process("두 번째")
        assert len(orch.conversation_history) == 4  # 2 user + 2 assistant


class TestOrchestratorToolCalls:
    """Tool 호출 처리 테스트."""

    @pytest.mark.asyncio
    async def test_handle_tool_calls(self, mock_deps):
        """Tool 호출 처리."""
        orch = mock_deps["orchestrator"]

        mock_tool = MagicMock()
        mock_tool.validate.return_value = (True, None)
        mock_tool.execute = AsyncMock(return_value=ToolResult(success=True, data="결과"))
        orch.registry = MagicMock()
        orch.registry.get.return_value = mock_tool

        block = MagicMock()
        block.type = "tool_use"
        block.name = "test_tool"
        block.input = {"param": "value"}
        block.id = "tool-123"

        results = await orch._handle_tool_calls([block])
        assert len(results) == 1
        assert results[0]["tool_use_id"] == "tool-123"
        assert "결과" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self, mock_deps):
        """알 수 없는 Tool."""
        orch = mock_deps["orchestrator"]
        orch.registry = MagicMock()
        orch.registry.get.return_value = None

        block = MagicMock()
        block.type = "tool_use"
        block.name = "unknown"
        block.input = {}
        block.id = "tool-456"

        results = await orch._handle_tool_calls([block])
        assert "알 수 없는 Tool" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_handle_tool_validation_failure(self, mock_deps):
        """Tool 파라미터 검증 실패."""
        orch = mock_deps["orchestrator"]

        mock_tool = MagicMock()
        mock_tool.validate.return_value = (False, "필수 파라미터 누락")
        orch.registry = MagicMock()
        orch.registry.get.return_value = mock_tool

        block = MagicMock()
        block.type = "tool_use"
        block.name = "test_tool"
        block.input = {}
        block.id = "tool-789"

        results = await orch._handle_tool_calls([block])
        assert "필수 파라미터 누락" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_process_with_tool_use(self, mock_deps):
        """Tool 사용이 포함된 처리 흐름."""
        orch = mock_deps["orchestrator"]

        # 첫 응답: tool_use
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "test_tool"
        tool_block.input = {}
        tool_block.id = "t1"

        tool_response = MagicMock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [tool_block]
        tool_response.usage.input_tokens = 10
        tool_response.usage.output_tokens = 5
        tool_response.usage.cache_creation_input_tokens = 0
        tool_response.usage.cache_read_input_tokens = 0

        # 두 번째 응답: end_turn
        final_block = MagicMock()
        final_block.text = "Tool 실행 완료"
        final_response = MagicMock()
        final_response.stop_reason = "end_turn"
        final_response.content = [final_block]
        final_response.usage.input_tokens = 15
        final_response.usage.output_tokens = 10
        final_response.usage.cache_creation_input_tokens = 0
        final_response.usage.cache_read_input_tokens = 0

        mock_deps["client"].messages.create.side_effect = [tool_response, final_response]

        mock_tool = MagicMock()
        mock_tool.validate.return_value = (True, None)
        mock_tool.execute = AsyncMock(return_value=ToolResult(success=True, data="ok"))
        orch.registry = MagicMock()
        orch.registry.get.return_value = mock_tool
        orch.registry.get_claude_specs.return_value = []

        result = await orch.process("Tool 테스트")
        assert result == "Tool 실행 완료"


class TestOrchestratorHelpers:
    """헬퍼 메서드 테스트."""

    def test_format_tool_result_success(self, mock_deps):
        """성공 결과 포맷팅."""
        orch = mock_deps["orchestrator"]
        result = orch._format_tool_result(ToolResult(success=True, data="데이터"))
        assert result == "데이터"

    def test_format_tool_result_error(self, mock_deps):
        """에러 결과 포맷팅."""
        orch = mock_deps["orchestrator"]
        result = orch._format_tool_result(ToolResult(success=False, error="실패"))
        assert "오류" in result
        assert "실패" in result

    def test_extract_text_response(self, mock_deps):
        """텍스트 추출."""
        orch = mock_deps["orchestrator"]
        block1 = MagicMock()
        block1.text = "첫 번째"
        block2 = MagicMock()
        block2.text = "두 번째"
        result = orch._extract_text_response([block1, block2])
        assert "첫 번째" in result
        assert "두 번째" in result

    def test_extract_text_response_no_text(self, mock_deps):
        """텍스트 없는 블록."""
        orch = mock_deps["orchestrator"]
        block = MagicMock(spec=[])  # text attr 없음
        result = orch._extract_text_response([block])
        assert result == ""

    def test_clear_history(self, mock_deps):
        """대화 기록 초기화."""
        orch = mock_deps["orchestrator"]
        orch.conversation_history = [{"role": "user", "content": "test"}]
        orch.clear_history()
        assert orch.conversation_history == []

    def test_get_history(self, mock_deps):
        """대화 기록 반환 (복사본)."""
        orch = mock_deps["orchestrator"]
        orch.conversation_history = [{"role": "user", "content": "test"}]
        history = orch.get_history()
        assert history == orch.conversation_history
        assert history is not orch.conversation_history  # 복사본

    def test_get_cost_info(self, mock_deps):
        """비용 정보 반환."""
        orch = mock_deps["orchestrator"]
        mock_deps["cost"].get_stats.return_value.to_dict.return_value = {"total": 0}
        info = orch.get_cost_info()
        assert "last_request" in info
        assert "routing" in info
        assert "session_stats" in info

    def test_get_cost_info_no_last_usage(self, mock_deps):
        """마지막 사용 정보 없을 때."""
        orch = mock_deps["orchestrator"]
        orch.last_usage = None
        orch.last_routing = None
        mock_deps["cost"].get_stats.return_value.to_dict.return_value = {}
        info = orch.get_cost_info()
        assert info["last_request"]["model"] is None
        assert info["routing"]["model"] is None

    def test_track_response_usage(self, mock_deps):
        """응답 사용량 추적."""
        orch = mock_deps["orchestrator"]
        response = MagicMock()
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50
        response.usage.cache_creation_input_tokens = 10
        response.usage.cache_read_input_tokens = 5
        orch._track_response_usage(response, "claude-sonnet")
        mock_deps["cost"].track_usage.assert_called_with(
            model="claude-sonnet",
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=10,
            cache_read_input_tokens=5,
        )
