"""설정 관리."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


# .env 파일 로드
load_dotenv()


@dataclass
class ModelPricing:
    """모델별 가격 ($/MTok)."""
    input_cost: float
    output_cost: float
    cache_write_cost: float  # 캐시 저장 비용
    cache_read_cost: float   # 캐시 읽기 비용


@dataclass
class CostOptimizationSettings:
    """비용 최적화 설정."""

    # 기능 활성화
    prompt_caching_enabled: bool = True
    model_routing_enabled: bool = True
    response_caching_enabled: bool = True
    conversation_summarization_enabled: bool = True

    # 모델 라우팅 설정
    simple_query_threshold: int = 50      # 간단한 질문 토큰 수 기준
    complex_query_keywords: list[str] = field(default_factory=lambda: [
        "분석", "설계", "아키텍처", "리팩토링", "최적화", "비교",
        "analyze", "design", "architecture", "refactor", "optimize", "compare"
    ])

    # 대화 요약 설정
    max_recent_messages: int = 10         # 전체 유지할 최근 메시지 수
    summarize_after_messages: int = 15    # 요약 시작 메시지 수

    # 응답 캐싱 설정
    cache_ttl_seconds: int = 3600         # 캐시 유효 시간 (1시간)
    max_cache_size: int = 1000            # 최대 캐시 항목 수
    similarity_threshold: float = 0.95    # 유사도 매칭 임계값


# 모델별 가격 정보 (2024년 기준 Anthropic 공식 가격)
MODEL_PRICING = {
    "claude-opus-4-20250514": ModelPricing(
        input_cost=15.0,
        output_cost=75.0,
        cache_write_cost=18.75,  # 1.25x
        cache_read_cost=1.50     # 0.1x
    ),
    "claude-sonnet-4-20250514": ModelPricing(
        input_cost=3.0,
        output_cost=15.0,
        cache_write_cost=3.75,   # 1.25x
        cache_read_cost=0.30     # 0.1x
    ),
    "claude-3-5-haiku-20241022": ModelPricing(
        input_cost=0.80,
        output_cost=4.0,
        cache_write_cost=1.0,    # 1.25x
        cache_read_cost=0.08     # 0.1x
    ),
}

# 모델 별칭
MODEL_ALIASES = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
}


@dataclass
class Settings:
    """애플리케이션 설정."""

    # API Keys
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    discord_bot_token: str = field(
        default_factory=lambda: os.getenv("DISCORD_BOT_TOKEN", "")
    )
    github_token: str = field(
        default_factory=lambda: os.getenv("GITHUB_TOKEN", "")
    )

    # Model 설정
    default_model: str = "claude-sonnet-4-20250514"
    haiku_model: str = "claude-3-5-haiku-20241022"
    opus_model: str = "claude-opus-4-20250514"

    # 경로
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    knowledge_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "knowledge")
    memory_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "memory")
    cache_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "cache")

    # 기능 설정
    enable_memory: bool = True
    max_conversation_history: int = 50

    # Web 설정
    web_host: str = "127.0.0.1"
    web_port: int = 8000

    # 비용 최적화 설정
    cost_optimization: CostOptimizationSettings = field(default_factory=CostOptimizationSettings)

    def validate(self) -> tuple[bool, list[str]]:
        """설정 유효성 검사."""
        errors = []

        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY가 설정되지 않았습니다")

        return len(errors) == 0, errors

    def get_model_pricing(self, model: str) -> ModelPricing:
        """모델 가격 정보 반환."""
        # 별칭 처리
        if model in MODEL_ALIASES:
            model = MODEL_ALIASES[model]
        return MODEL_PRICING.get(model, MODEL_PRICING[self.default_model])


# 전역 설정 인스턴스
settings = Settings()
