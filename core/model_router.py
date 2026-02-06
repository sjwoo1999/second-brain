"""스마트 모델 라우터 - 질문 복잡도에 따른 모델 선택."""

import re
from enum import Enum
from dataclasses import dataclass
from config.settings import settings


class Complexity(Enum):
    """질문 복잡도 레벨."""
    SIMPLE = "simple"      # Haiku 사용
    NORMAL = "normal"      # Sonnet 사용
    COMPLEX = "complex"    # Opus 사용


@dataclass
class RoutingResult:
    """라우팅 결과."""
    model: str
    complexity: Complexity
    reason: str


class ModelRouter:
    """모델 라우터 - 메시지 복잡도 분석 및 적절한 모델 선택."""

    # 간단한 질문 패턴
    SIMPLE_PATTERNS = [
        r'^(안녕|hi|hello|hey)[\s!?.]*$',
        r'^(뭐해|뭐하는|뭐하고).*$',
        r'^(네|응|아니|yes|no|ok|okay)[\s!?.]*$',
        r'^(고마워|감사|thanks|thank you).*$',
        r'^(몇 시|현재 시간|what time|time\?).*$',
        r'^(오늘 날씨|날씨 어때|weather).*$',
        r'^.{1,20}$',  # 매우 짧은 메시지
    ]

    # 복잡한 질문 키워드
    COMPLEX_KEYWORDS = [
        # 한국어
        "분석", "설계", "아키텍처", "리팩토링", "최적화", "비교",
        "전략", "계획", "로드맵", "검토", "평가",
        "상세히", "자세히", "깊이", "심층적",
        # 영어
        "analyze", "design", "architecture", "refactor", "optimize",
        "compare", "strategy", "plan", "roadmap", "review", "evaluate",
        "detailed", "in-depth", "comprehensive", "elaborate",
    ]

    # 복잡한 질문 패턴
    COMPLEX_PATTERNS = [
        r'(어떻게|왜|how|why).*(해야|할까|should|would).*',
        r'(차이점|다른 점|difference|vs|versus).*',
        r'(장단점|pros.*cons|trade.*off).*',
        r'(비교|분석|compare|analyze).*',
        r'.*(가장 좋은|최선|best|optimal).*방법.*',
    ]

    def __init__(self):
        self.simple_patterns = [re.compile(p, re.IGNORECASE) for p in self.SIMPLE_PATTERNS]
        self.complex_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMPLEX_PATTERNS]

    def route(self, message: str, conversation_history: list[dict] = None) -> RoutingResult:
        """메시지 복잡도를 분석하여 적절한 모델 선택."""

        if not settings.cost_optimization.model_routing_enabled:
            return RoutingResult(
                model=settings.default_model,
                complexity=Complexity.NORMAL,
                reason="모델 라우팅 비활성화"
            )

        # 대화 기록 컨텍스트 고려
        context_complexity = self._analyze_conversation_context(conversation_history or [])

        # 메시지 복잡도 분석
        message_complexity = self._analyze_message(message)

        # 최종 복잡도 결정 (대화 컨텍스트와 메시지 복잡도 중 높은 것)
        if context_complexity == Complexity.COMPLEX or message_complexity == Complexity.COMPLEX:
            return RoutingResult(
                model=settings.opus_model,
                complexity=Complexity.COMPLEX,
                reason="복잡한 분석/설계 요청"
            )
        elif context_complexity == Complexity.SIMPLE and message_complexity == Complexity.SIMPLE:
            return RoutingResult(
                model=settings.haiku_model,
                complexity=Complexity.SIMPLE,
                reason="간단한 질문/인사"
            )
        else:
            return RoutingResult(
                model=settings.default_model,
                complexity=Complexity.NORMAL,
                reason="일반적인 대화"
            )

    def _analyze_message(self, message: str) -> Complexity:
        """단일 메시지 복잡도 분석."""
        message_lower = message.lower().strip()

        # 간단한 패턴 매칭
        for pattern in self.simple_patterns:
            if pattern.match(message_lower):
                return Complexity.SIMPLE

        # 복잡한 키워드 체크
        for keyword in self.COMPLEX_KEYWORDS:
            if keyword in message_lower:
                return Complexity.COMPLEX

        # 복잡한 패턴 매칭
        for pattern in self.complex_patterns:
            if pattern.search(message_lower):
                return Complexity.COMPLEX

        # 메시지 길이 기반 판단
        token_estimate = len(message.split())
        if token_estimate < settings.cost_optimization.simple_query_threshold:
            # 짧은 메시지지만 간단한 패턴이 아님 = 일반
            return Complexity.NORMAL

        # 긴 메시지는 일반적으로 더 복잡
        if token_estimate > 100:
            return Complexity.COMPLEX

        return Complexity.NORMAL

    def _analyze_conversation_context(self, history: list[dict]) -> Complexity:
        """대화 컨텍스트 기반 복잡도 분석."""
        if not history:
            return Complexity.SIMPLE

        # 최근 3개 메시지 분석
        recent_messages = history[-6:]  # user + assistant pairs
        combined_text = " ".join(
            msg.get("content", "") for msg in recent_messages
            if isinstance(msg.get("content"), str)
        )

        # 복잡한 키워드가 최근 대화에 있는지 확인
        combined_lower = combined_text.lower()
        for keyword in self.COMPLEX_KEYWORDS:
            if keyword in combined_lower:
                return Complexity.NORMAL  # 컨텍스트가 복잡하면 최소 NORMAL

        return Complexity.SIMPLE


# 전역 모델 라우터 인스턴스
model_router = ModelRouter()
