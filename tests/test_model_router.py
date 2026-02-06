"""ModelRouter 단위 테스트."""

import pytest
from unittest.mock import patch
from core.model_router import ModelRouter, Complexity
from config.settings import settings


class TestModelRouterSimple:
    """간단한 질문 → SIMPLE (Haiku) 라우팅."""

    @pytest.mark.parametrize("message", [
        "안녕",
        "안녕!",
        "hi",
        "hello",
        "네",
        "응",
        "ok",
        "고마워",
        "감사합니다",
        "thanks",
    ])
    def test_simple_greetings(self, model_router, message):
        """인사/단답 → SIMPLE."""
        result = model_router.route(message)
        assert result.complexity == Complexity.SIMPLE
        assert result.model == settings.haiku_model

    def test_very_short_message(self, model_router):
        """매우 짧은 메시지 → SIMPLE."""
        result = model_router.route("뭐해?")
        assert result.complexity == Complexity.SIMPLE


class TestModelRouterNormal:
    """일반 질문 → NORMAL (Sonnet) 라우팅."""

    def test_normal_question(self, model_router):
        """일반 질문 → NORMAL."""
        result = model_router.route("파이썬에서 리스트 컴프리헨션 사용법을 알려줘")
        assert result.complexity == Complexity.NORMAL
        assert result.model == settings.default_model

    def test_normal_request(self, model_router):
        """일반 요청 → NORMAL."""
        result = model_router.route("오늘 할 일 목록 만들어줘 회의 준비하기 보고서 작성하기 이메일 보내기")
        assert result.complexity == Complexity.NORMAL


class TestModelRouterComplex:
    """복잡한 질문 → COMPLEX (Opus) 라우팅."""

    @pytest.mark.parametrize("keyword", [
        "분석", "설계", "아키텍처", "리팩토링", "최적화", "비교",
        "analyze", "design", "architecture", "refactor", "optimize",
    ])
    def test_complex_keywords(self, model_router, keyword):
        """복잡 키워드 포함 → COMPLEX."""
        result = model_router.route(f"이 코드를 {keyword}해줘 자세한 결과를 알려줘")
        assert result.complexity == Complexity.COMPLEX
        assert result.model == settings.opus_model

    def test_long_message(self, model_router):
        """100단어 이상 긴 메시지 → COMPLEX."""
        long_msg = " ".join(["단어"] * 110)
        result = model_router.route(long_msg)
        assert result.complexity == Complexity.COMPLEX

    def test_complex_pattern(self, model_router):
        """복잡 패턴 매칭 → COMPLEX."""
        # 메시지가 20자 이하면 SIMPLE 패턴에 먼저 매칭되므로 충분히 길게 작성
        result = model_router.route("이 프로젝트의 백엔드 구조를 어떻게 해야 가장 좋은 방법일까?")
        assert result.complexity == Complexity.COMPLEX


class TestModelRouterContext:
    """대화 컨텍스트 기반 라우팅."""

    def test_complex_context_upgrades(self, model_router):
        """대화 컨텍스트에 복잡 키워드가 있으면 NORMAL 이상."""
        history = [
            {"role": "user", "content": "시스템 아키텍처에 대해 이야기하자"},
            {"role": "assistant", "content": "네, 아키텍처 설계에 대해 논의합시다."},
        ]
        # 짧은 후속 메시지지만 컨텍스트가 복잡함
        result = model_router.route("계속해줘", conversation_history=history)
        # 컨텍스트에 "아키텍처" 가 있으므로 최소 NORMAL
        assert result.complexity in (Complexity.NORMAL, Complexity.COMPLEX)

    def test_empty_context(self, model_router):
        """빈 대화 컨텍스트."""
        result = model_router.route("안녕", conversation_history=[])
        assert result.complexity == Complexity.SIMPLE


class TestModelRouterDisabled:
    """라우팅 비활성화."""

    def test_disabled_routing(self, model_router):
        """라우팅 비활성화 시 기본 모델 반환."""
        original = settings.cost_optimization.model_routing_enabled
        try:
            settings.cost_optimization.model_routing_enabled = False
            result = model_router.route("복잡한 아키텍처 분석 요청")
            assert result.model == settings.default_model
            assert result.complexity == Complexity.NORMAL
            assert "비활성화" in result.reason
        finally:
            settings.cost_optimization.model_routing_enabled = original
