"""Orchestrator - Claude와 Tool을 연결하는 메인 두뇌."""

import os
from typing import Optional
from anthropic import Anthropic

from .registry import ToolRegistry, registry
from .base_tool import ToolResult
from .cost_tracker import cost_tracker, UsageRecord
from .model_router import model_router, RoutingResult
from .cache_service import cache_service
from .summarizer import summarizer
from .memory_service import memory_service
from config.settings import settings


class Orchestrator:
    """메인 오케스트레이터 - 사용자 요청을 받아 Tool을 실행."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 필요합니다")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model or settings.default_model
        self.registry = tool_registry or registry
        self.conversation_history: list[dict] = []

        # 기본 시스템 프롬프트 (캐싱 대상 - 변하지 않음)
        self.base_system_prompt = """당신은 사용자의 개인 AI 비서이자 "Second Brain"입니다.
사용자의 요청을 이해하고, 적절한 도구를 사용해서 작업을 수행합니다.

핵심 원칙:
1. 사용자의 의도를 정확히 파악합니다
2. 필요한 도구를 선택하고 실행합니다
3. 결과를 명확하게 전달합니다
4. 모르는 것은 솔직히 모른다고 합니다
5. 사용자에 대해 기억하고 있는 정보를 자연스럽게 활용합니다
6. 기억 정보를 직접 언급하기보다 맥락에 녹여서 응답합니다

응답은 간결하고 핵심적으로 합니다."""

        # 마지막 요청 정보
        self.last_usage: Optional[UsageRecord] = None
        self.last_routing: Optional[RoutingResult] = None

    def _build_system_prompt(self, user_message: str) -> str:
        """동적 시스템 프롬프트 생성 (기본 프롬프트 + 메모리 컨텍스트)."""
        memory_context = memory_service.build_context(user_message)
        if memory_context:
            return self.base_system_prompt + "\n" + memory_context
        return self.base_system_prompt

    def _get_system_config(self, user_message: str = "") -> list[dict]:
        """시스템 프롬프트 설정 (프롬프트 캐싱 포함)."""
        if settings.cost_optimization.prompt_caching_enabled:
            blocks = [
                {
                    "type": "text",
                    "text": self.base_system_prompt,
                    "cache_control": {"type": "ephemeral"}  # 기본 프롬프트 캐싱
                }
            ]
            # 메모리 컨텍스트는 별도 블록 (메시지마다 변할 수 있음)
            memory_context = memory_service.build_context(user_message)
            if memory_context:
                blocks.append({
                    "type": "text",
                    "text": memory_context,
                })
            return blocks
        else:
            return self._build_system_prompt(user_message)

    async def process(self, user_message: str) -> str:
        """사용자 메시지를 처리하고 응답 반환."""

        # 1. 로컬 캐시 확인
        cached = cache_service.get(user_message)
        if cached:
            # 캐시 히트 - 비용 추적 (비용 없음)
            self.last_usage = cost_tracker.track_usage(
                model=cached.model,
                input_tokens=0,
                output_tokens=0,
                from_local_cache=True
            )
            # 대화 기록에 추가
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": cached.response
            })
            return cached.response

        # 2. 모델 라우팅
        routing = model_router.route(user_message, self.conversation_history)
        self.last_routing = routing
        selected_model = routing.model

        # 3. 대화 기록 요약 (필요시)
        working_history = summarizer.summarize_history(self.conversation_history.copy())

        # 대화 기록에 새 메시지 추가
        working_history.append({
            "role": "user",
            "content": user_message
        })

        # 실제 대화 기록에도 추가
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # 4. Claude API 호출 (프롬프트 캐싱 + 메모리 컨텍스트 적용)
        system_config = self._get_system_config(user_message)

        response = self.client.messages.create(
            model=selected_model,
            max_tokens=4096,
            system=system_config,
            tools=self.registry.get_claude_specs(),
            messages=working_history,
        )

        # 사용량 추적
        self._track_response_usage(response, selected_model)

        # Tool 사용이 필요한 경우
        while response.stop_reason == "tool_use":
            # Tool 호출 처리
            tool_results = await self._handle_tool_calls(response.content)

            # 대화 기록에 assistant 응답 추가
            working_history.append({
                "role": "assistant",
                "content": response.content
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            # Tool 결과 추가
            working_history.append({
                "role": "user",
                "content": tool_results
            })
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # 다시 Claude 호출
            response = self.client.messages.create(
                model=selected_model,
                max_tokens=4096,
                system=system_config,
                tools=self.registry.get_claude_specs(),
                messages=working_history,
            )

            # 추가 사용량 추적
            self._track_response_usage(response, selected_model)

        # 최종 응답 추출
        final_response = self._extract_text_response(response.content)

        # 대화 기록에 추가
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })

        # 5. 로컬 캐시에 저장
        cache_service.set(user_message, final_response, selected_model)

        return final_response

    def _track_response_usage(self, response, model: str) -> None:
        """응답의 사용량을 추적."""
        usage = response.usage

        # 캐시 관련 토큰 추출
        cache_creation_tokens = getattr(usage, 'cache_creation_input_tokens', 0) or 0
        cache_read_tokens = getattr(usage, 'cache_read_input_tokens', 0) or 0

        self.last_usage = cost_tracker.track_usage(
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_creation_input_tokens=cache_creation_tokens,
            cache_read_input_tokens=cache_read_tokens,
        )

    async def _handle_tool_calls(self, content: list) -> list[dict]:
        """Tool 호출을 처리하고 결과 반환."""
        results = []

        for block in content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id

                # Tool 실행
                tool = self.registry.get(tool_name)
                if tool:
                    # 파라미터 검증
                    is_valid, error = tool.validate(**tool_input)
                    if not is_valid:
                        result = ToolResult(success=False, error=error)
                    else:
                        result = await tool.execute(**tool_input)
                else:
                    result = ToolResult(
                        success=False,
                        error=f"알 수 없는 Tool: {tool_name}"
                    )

                # 결과 포맷팅
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": self._format_tool_result(result)
                })

        return results

    def _format_tool_result(self, result: ToolResult) -> str:
        """Tool 결과를 문자열로 포맷팅."""
        if result.success:
            return str(result.data)
        else:
            return f"오류: {result.error}"

    def _extract_text_response(self, content: list) -> str:
        """응답에서 텍스트만 추출."""
        texts = []
        for block in content:
            if hasattr(block, 'text'):
                texts.append(block.text)
        return "\n".join(texts)

    def clear_history(self) -> None:
        """대화 기록 초기화."""
        self.conversation_history = []

    def get_history(self) -> list[dict]:
        """대화 기록 반환."""
        return self.conversation_history.copy()

    def get_cost_info(self) -> dict:
        """현재 비용 정보 반환."""
        stats = cost_tracker.get_stats()
        last_usage = self.last_usage

        return {
            "last_request": {
                "model": last_usage.model if last_usage else None,
                "input_tokens": last_usage.input_tokens if last_usage else 0,
                "output_tokens": last_usage.output_tokens if last_usage else 0,
                "cost_usd": last_usage.cost_usd if last_usage else 0,
                "cached": last_usage.cached if last_usage else False,
                "from_local_cache": last_usage.from_local_cache if last_usage else False,
            },
            "routing": {
                "model": self.last_routing.model if self.last_routing else None,
                "complexity": self.last_routing.complexity.value if self.last_routing else None,
                "reason": self.last_routing.reason if self.last_routing else None,
            },
            "session_stats": stats.to_dict(),
        }
