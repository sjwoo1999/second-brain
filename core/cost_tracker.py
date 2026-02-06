"""비용 추적 서비스 - 토큰 사용량 및 비용 계산."""

import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path
from config.settings import settings, MODEL_PRICING, MODEL_ALIASES


@dataclass
class UsageRecord:
    """단일 API 호출 사용량 기록."""
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cost_usd: float = 0.0
    cached: bool = False
    from_local_cache: bool = False


@dataclass
class CostStats:
    """비용 통계."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_write_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cost_usd: float = 0.0
    total_requests: int = 0
    cache_hits: int = 0
    local_cache_hits: int = 0

    # 모델별 통계
    model_usage: dict = field(default_factory=dict)

    @property
    def cache_hit_rate(self) -> float:
        """캐시 히트율 계산."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits + self.local_cache_hits) / self.total_requests * 100

    @property
    def estimated_savings_usd(self) -> float:
        """예상 절감액 계산."""
        if self.total_cache_read_tokens == 0:
            return 0.0
        # 캐시 읽기로 절감한 비용 (일반 입력 - 캐시 읽기)
        default_pricing = settings.get_model_pricing(settings.default_model)
        savings = self.total_cache_read_tokens * (default_pricing.input_cost - default_pricing.cache_read_cost) / 1_000_000
        return savings

    def to_dict(self) -> dict:
        """딕셔너리로 변환."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_write_tokens": self.total_cache_write_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "local_cache_hits": self.local_cache_hits,
            "cache_hit_rate": round(self.cache_hit_rate, 2),
            "estimated_savings_usd": round(self.estimated_savings_usd, 6),
            "model_usage": self.model_usage,
        }


class CostTracker:
    """비용 추적기 - API 사용량 및 비용 모니터링."""

    def __init__(self, persist_path: Optional[Path] = None):
        self.persist_path = persist_path or settings.cache_dir / "cost_tracker.json"
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)

        self.stats = CostStats()
        self.history: list[UsageRecord] = []

        # 저장된 데이터 로드
        self._load()

    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0,
        from_local_cache: bool = False,
    ) -> UsageRecord:
        """API 사용량 추적 및 비용 계산."""

        # 모델 이름 정규화
        normalized_model = MODEL_ALIASES.get(model, model)
        pricing = settings.get_model_pricing(normalized_model)

        # 비용 계산
        if from_local_cache:
            cost = 0.0
        else:
            # 일반 입력 토큰 비용
            regular_input_tokens = input_tokens - cache_creation_input_tokens - cache_read_input_tokens
            cost = regular_input_tokens * pricing.input_cost / 1_000_000

            # 캐시 저장 비용
            cost += cache_creation_input_tokens * pricing.cache_write_cost / 1_000_000

            # 캐시 읽기 비용
            cost += cache_read_input_tokens * pricing.cache_read_cost / 1_000_000

            # 출력 토큰 비용
            cost += output_tokens * pricing.output_cost / 1_000_000

        # 레코드 생성
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            model=normalized_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            cost_usd=cost,
            cached=cache_read_input_tokens > 0,
            from_local_cache=from_local_cache,
        )

        # 통계 업데이트
        self._update_stats(record)

        # 히스토리에 추가
        self.history.append(record)

        # 자동 저장
        self._save()

        return record

    def _update_stats(self, record: UsageRecord) -> None:
        """통계 업데이트."""
        self.stats.total_input_tokens += record.input_tokens
        self.stats.total_output_tokens += record.output_tokens
        self.stats.total_cache_write_tokens += record.cache_creation_input_tokens
        self.stats.total_cache_read_tokens += record.cache_read_input_tokens
        self.stats.total_cost_usd += record.cost_usd
        self.stats.total_requests += 1

        if record.cached:
            self.stats.cache_hits += 1

        if record.from_local_cache:
            self.stats.local_cache_hits += 1

        # 모델별 통계
        model = record.model
        if model not in self.stats.model_usage:
            self.stats.model_usage[model] = {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0
            }

        self.stats.model_usage[model]["requests"] += 1
        self.stats.model_usage[model]["input_tokens"] += record.input_tokens
        self.stats.model_usage[model]["output_tokens"] += record.output_tokens
        self.stats.model_usage[model]["cost_usd"] += record.cost_usd

    def get_stats(self) -> CostStats:
        """현재 통계 반환."""
        return self.stats

    def get_recent_usage(self, hours: int = 24) -> list[UsageRecord]:
        """최근 사용량 반환."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            r for r in self.history
            if datetime.fromisoformat(r.timestamp) > cutoff
        ]

    def get_last_usage(self) -> Optional[UsageRecord]:
        """마지막 사용량 반환."""
        if self.history:
            return self.history[-1]
        return None

    def reset(self) -> None:
        """통계 초기화."""
        self.stats = CostStats()
        self.history = []
        self._save()

    def _save(self) -> None:
        """데이터 저장."""
        data = {
            "stats": self.stats.to_dict(),
            "history": [asdict(r) for r in self.history[-1000:]]  # 최근 1000건만 유지
        }
        with open(self.persist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """저장된 데이터 로드."""
        if not self.persist_path.exists():
            return

        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 통계 복원
            stats_data = data.get("stats", {})
            self.stats = CostStats(
                total_input_tokens=stats_data.get("total_input_tokens", 0),
                total_output_tokens=stats_data.get("total_output_tokens", 0),
                total_cache_write_tokens=stats_data.get("total_cache_write_tokens", 0),
                total_cache_read_tokens=stats_data.get("total_cache_read_tokens", 0),
                total_cost_usd=stats_data.get("total_cost_usd", 0.0),
                total_requests=stats_data.get("total_requests", 0),
                cache_hits=stats_data.get("cache_hits", 0),
                local_cache_hits=stats_data.get("local_cache_hits", 0),
                model_usage=stats_data.get("model_usage", {}),
            )

            # 히스토리 복원
            self.history = [
                UsageRecord(**r) for r in data.get("history", [])
            ]
        except (json.JSONDecodeError, KeyError):
            # 파일이 손상된 경우 초기화
            self.stats = CostStats()
            self.history = []


# 전역 비용 추적기 인스턴스
cost_tracker = CostTracker()
