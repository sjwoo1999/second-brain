"""CacheService 단위 테스트."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from core.cache_service import CacheService
from config.settings import settings


class TestCacheServiceBasic:
    """기본 캐시 동작 테스트."""

    def test_miss_then_set_then_hit(self, cache_service):
        """캐시 miss → set → hit 흐름."""
        # miss
        result = cache_service.get("안녕하세요?")
        assert result is None

        # set
        cached = cache_service.set("안녕하세요?", "안녕! 반가워요.", "sonnet")
        assert cached is not None
        assert cached.query == "안녕하세요?"
        assert cached.response == "안녕! 반가워요."

        # hit
        result = cache_service.get("안녕하세요?")
        assert result is not None
        assert result.response == "안녕! 반가워요."
        assert result.hit_count == 1

    def test_multiple_hits_increment(self, cache_service):
        """여러 번 히트 시 카운트 증가."""
        cache_service.set("질문", "응답", "sonnet")

        cache_service.get("질문")
        cache_service.get("질문")
        result = cache_service.get("질문")
        assert result.hit_count == 3


class TestCacheServiceTTL:
    """TTL 만료 테스트."""

    def test_ttl_expiry(self, cache_service):
        """TTL 만료 시 miss."""
        cache_service.set("질문", "응답", "sonnet")

        # 캐시 항목의 created_at을 과거로 설정
        query_hash = cache_service._hash_query("질문")
        old_time = (datetime.now() - timedelta(seconds=settings.cost_optimization.cache_ttl_seconds + 100))
        cache_service.cache[query_hash].created_at = old_time.isoformat()

        result = cache_service.get("질문")
        assert result is None

    def test_not_expired(self, cache_service):
        """TTL 만료 전 hit."""
        cache_service.set("질문", "응답", "sonnet")
        result = cache_service.get("질문")
        assert result is not None


class TestCacheServiceNormalization:
    """쿼리 정규화 테스트."""

    def test_case_insensitive(self, cache_service):
        """대소문자 무시."""
        cache_service.set("Hello World", "response", "sonnet")
        result = cache_service.get("hello world")
        assert result is not None

    def test_whitespace_normalization(self, cache_service):
        """공백 정규화."""
        cache_service.set("hello   world", "response", "sonnet")
        result = cache_service.get("hello world")
        assert result is not None

    def test_same_hash(self, cache_service):
        """정규화된 쿼리는 같은 해시."""
        h1 = cache_service._hash_query("Hello  World")
        h2 = cache_service._hash_query("hello world")
        assert h1 == h2


class TestCacheServiceEviction:
    """캐시 크기 제한 및 LRU 제거 테스트."""

    def test_eviction_on_max_size(self, tmp_path):
        """최대 크기 초과 시 제거."""
        cache_path = tmp_path / "evict_cache.json"

        # 작은 max_cache_size로 테스트
        original_max = settings.cost_optimization.max_cache_size
        try:
            settings.cost_optimization.max_cache_size = 5
            svc = CacheService(cache_path=cache_path)

            # 5개 채우기
            for i in range(5):
                svc.set(f"query_{i}", f"response_{i}", "sonnet")

            assert len(svc.cache) == 5

            # 6번째 추가 시 eviction 발생
            svc.set("query_new", "response_new", "sonnet")
            assert len(svc.cache) <= 5
        finally:
            settings.cost_optimization.max_cache_size = original_max


class TestCacheServiceClear:
    """캐시 초기화 테스트."""

    def test_clear(self, cache_service):
        """clear() 동작."""
        cache_service.set("q1", "r1", "sonnet")
        cache_service.set("q2", "r2", "sonnet")
        assert len(cache_service.cache) == 2

        cache_service.clear()
        assert len(cache_service.cache) == 0

        # clear 후 miss 확인
        assert cache_service.get("q1") is None


class TestCacheServiceDisabled:
    """캐싱 비활성화 테스트."""

    def test_disabled_get_returns_none(self, cache_service):
        """비활성화 시 get → None."""
        cache_service.set("q", "r", "sonnet")

        original = settings.cost_optimization.response_caching_enabled
        try:
            settings.cost_optimization.response_caching_enabled = False
            result = cache_service.get("q")
            assert result is None
        finally:
            settings.cost_optimization.response_caching_enabled = original

    def test_disabled_set_returns_none(self, cache_service):
        """비활성화 시 set → None."""
        original = settings.cost_optimization.response_caching_enabled
        try:
            settings.cost_optimization.response_caching_enabled = False
            result = cache_service.set("q", "r", "sonnet")
            assert result is None
        finally:
            settings.cost_optimization.response_caching_enabled = original


class TestCacheServiceStats:
    """캐시 통계 테스트."""

    def test_get_stats(self, cache_service):
        """통계 반환."""
        cache_service.set("q1", "r1", "sonnet")
        cache_service.set("q2", "r2", "sonnet")
        cache_service.get("q1")  # 1 hit

        stats = cache_service.get_stats()
        assert stats["total_entries"] == 2
        assert stats["total_hits"] == 1


class TestCacheServicePersistence:
    """영속성 테스트."""

    def test_persist_and_load(self, tmp_path):
        """저장 후 로드."""
        path = tmp_path / "persist_cache.json"

        svc1 = CacheService(cache_path=path)
        svc1.set("question", "answer", "sonnet")

        svc2 = CacheService(cache_path=path)
        result = svc2.get("question")
        assert result is not None
        assert result.response == "answer"
