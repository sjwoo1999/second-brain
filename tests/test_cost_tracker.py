"""CostTracker 단위 테스트."""

import pytest
from core.cost_tracker import CostTracker, CostStats
from config.settings import settings, MODEL_PRICING


class TestCostTrackerBasic:
    """기본 비용 추적 테스트."""

    def test_initial_state(self, cost_tracker):
        """초기 상태 확인."""
        stats = cost_tracker.get_stats()
        assert stats.total_requests == 0
        assert stats.total_cost_usd == 0.0
        assert stats.total_input_tokens == 0
        assert stats.total_output_tokens == 0

    def test_track_usage(self, cost_tracker):
        """사용량 추적."""
        record = cost_tracker.track_usage(
            model=settings.default_model,
            input_tokens=1000,
            output_tokens=500,
        )

        assert record.model == settings.default_model
        assert record.input_tokens == 1000
        assert record.output_tokens == 500
        assert record.cost_usd > 0

    def test_cost_calculation_sonnet(self, cost_tracker):
        """Sonnet 비용 계산 정확도."""
        pricing = MODEL_PRICING[settings.default_model]
        record = cost_tracker.track_usage(
            model=settings.default_model,
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=1_000_000,
        )

        expected_cost = pricing.input_cost + pricing.output_cost
        assert abs(record.cost_usd - expected_cost) < 0.001

    def test_cost_calculation_with_cache(self, cost_tracker):
        """캐시 포함 비용 계산."""
        pricing = MODEL_PRICING[settings.default_model]

        record = cost_tracker.track_usage(
            model=settings.default_model,
            input_tokens=1_000_000,
            output_tokens=100_000,
            cache_creation_input_tokens=500_000,
            cache_read_input_tokens=300_000,
        )

        # regular_input = 1M - 500K - 300K = 200K
        expected = (
            200_000 * pricing.input_cost / 1_000_000
            + 500_000 * pricing.cache_write_cost / 1_000_000
            + 300_000 * pricing.cache_read_cost / 1_000_000
            + 100_000 * pricing.output_cost / 1_000_000
        )
        assert abs(record.cost_usd - expected) < 0.001


class TestCostTrackerModels:
    """모델별 가격 차이 테스트."""

    def test_haiku_cheaper_than_sonnet(self, cost_tracker):
        """Haiku가 Sonnet보다 저렴."""
        haiku = cost_tracker.track_usage(
            model=settings.haiku_model,
            input_tokens=1000,
            output_tokens=500,
        )
        # 새 tracker로 격리
        from core.cost_tracker import CostTracker
        tracker2 = CostTracker(persist_path=cost_tracker.persist_path.parent / "t2.json")
        sonnet = tracker2.track_usage(
            model=settings.default_model,
            input_tokens=1000,
            output_tokens=500,
        )
        assert haiku.cost_usd < sonnet.cost_usd

    def test_opus_most_expensive(self, cost_tracker):
        """Opus가 가장 비싼 모델."""
        opus = cost_tracker.track_usage(
            model=settings.opus_model,
            input_tokens=1000,
            output_tokens=500,
        )
        from core.cost_tracker import CostTracker
        tracker2 = CostTracker(persist_path=cost_tracker.persist_path.parent / "t3.json")
        sonnet = tracker2.track_usage(
            model=settings.default_model,
            input_tokens=1000,
            output_tokens=500,
        )
        assert opus.cost_usd > sonnet.cost_usd

    def test_model_alias_normalization(self, cost_tracker):
        """모델 별칭이 정규화됨."""
        record = cost_tracker.track_usage(
            model="sonnet",
            input_tokens=100,
            output_tokens=50,
        )
        assert record.model == settings.default_model


class TestCostTrackerLocalCache:
    """로컬 캐시 히트 시 비용."""

    def test_local_cache_zero_cost(self, cost_tracker):
        """로컬 캐시 히트 시 비용 $0."""
        record = cost_tracker.track_usage(
            model=settings.default_model,
            input_tokens=0,
            output_tokens=0,
            from_local_cache=True,
        )
        assert record.cost_usd == 0.0
        assert record.from_local_cache is True

    def test_local_cache_counted_in_stats(self, cost_tracker):
        """로컬 캐시 히트가 통계에 반영."""
        cost_tracker.track_usage(
            model=settings.default_model,
            input_tokens=0,
            output_tokens=0,
            from_local_cache=True,
        )
        stats = cost_tracker.get_stats()
        assert stats.local_cache_hits == 1
        assert stats.total_requests == 1


class TestCostTrackerStats:
    """통계 관련 테스트."""

    def test_cache_hit_rate(self, cost_tracker):
        """캐시 히트율 계산."""
        # 3건 중 1건 캐시 히트
        cost_tracker.track_usage(model=settings.default_model, input_tokens=100, output_tokens=50)
        cost_tracker.track_usage(
            model=settings.default_model, input_tokens=100, output_tokens=50,
            cache_read_input_tokens=50,
        )
        cost_tracker.track_usage(model=settings.default_model, input_tokens=100, output_tokens=50)

        stats = cost_tracker.get_stats()
        # 1 cache hit out of 3 requests = 33.33%
        assert abs(stats.cache_hit_rate - 33.33) < 1.0

    def test_cache_hit_rate_zero(self, cost_tracker):
        """요청 없을 때 히트율 0."""
        stats = cost_tracker.get_stats()
        assert stats.cache_hit_rate == 0.0

    def test_estimated_savings(self, cost_tracker):
        """예상 절감액 계산."""
        cost_tracker.track_usage(
            model=settings.default_model,
            input_tokens=1_000_000,
            output_tokens=100_000,
            cache_read_input_tokens=500_000,
        )
        stats = cost_tracker.get_stats()
        assert stats.estimated_savings_usd > 0

    def test_estimated_savings_zero(self, cost_tracker):
        """캐시 읽기 없으면 절감액 0."""
        cost_tracker.track_usage(
            model=settings.default_model,
            input_tokens=1000,
            output_tokens=500,
        )
        stats = cost_tracker.get_stats()
        assert stats.estimated_savings_usd == 0.0

    def test_model_usage_tracking(self, cost_tracker):
        """모델별 사용량 추적."""
        cost_tracker.track_usage(model=settings.haiku_model, input_tokens=100, output_tokens=50)
        cost_tracker.track_usage(model=settings.default_model, input_tokens=200, output_tokens=100)
        cost_tracker.track_usage(model=settings.haiku_model, input_tokens=150, output_tokens=75)

        stats = cost_tracker.get_stats()
        assert stats.model_usage[settings.haiku_model]["requests"] == 2
        assert stats.model_usage[settings.default_model]["requests"] == 1


class TestCostTrackerReset:
    """초기화 테스트."""

    def test_reset(self, cost_tracker):
        """reset() 후 통계 초기화."""
        cost_tracker.track_usage(model=settings.default_model, input_tokens=1000, output_tokens=500)
        cost_tracker.track_usage(model=settings.default_model, input_tokens=2000, output_tokens=1000)

        assert cost_tracker.get_stats().total_requests == 2

        cost_tracker.reset()

        stats = cost_tracker.get_stats()
        assert stats.total_requests == 0
        assert stats.total_cost_usd == 0.0
        assert stats.total_input_tokens == 0
        assert stats.model_usage == {}
        assert cost_tracker.history == []


class TestCostTrackerPersistence:
    """데이터 영속성 테스트."""

    def test_persist_and_load(self, tmp_path):
        """저장 후 다시 로드."""
        path = tmp_path / "persist_test.json"

        tracker1 = CostTracker(persist_path=path)
        tracker1.track_usage(model=settings.default_model, input_tokens=1000, output_tokens=500)

        # 새 인스턴스로 로드
        tracker2 = CostTracker(persist_path=path)
        stats = tracker2.get_stats()
        assert stats.total_requests == 1
        assert stats.total_input_tokens == 1000


class TestCostStatsDict:
    """CostStats.to_dict 테스트."""

    def test_to_dict(self, cost_tracker):
        """to_dict 변환."""
        cost_tracker.track_usage(model=settings.default_model, input_tokens=1000, output_tokens=500)
        stats = cost_tracker.get_stats()
        d = stats.to_dict()

        assert "total_input_tokens" in d
        assert "total_output_tokens" in d
        assert "total_cost_usd" in d
        assert "cache_hit_rate" in d
        assert "estimated_savings_usd" in d
        assert "model_usage" in d
