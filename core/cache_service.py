"""로컬 응답 캐싱 서비스 - 동일/유사 질문에 대한 캐시 응답."""

import json
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
from config.settings import settings


@dataclass
class CachedResponse:
    """캐시된 응답."""
    query_hash: str
    query: str
    response: str
    model: str
    created_at: str
    hit_count: int = 0


class CacheService:
    """로컬 응답 캐싱 서비스."""

    def __init__(self, cache_path: Optional[Path] = None):
        self.cache_path = cache_path or settings.cache_dir / "response_cache.json"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        self.cache: dict[str, CachedResponse] = {}
        self._load()

    def _hash_query(self, query: str) -> str:
        """쿼리를 해시로 변환."""
        # 정규화: 소문자, 공백 정리
        normalized = " ".join(query.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get(self, query: str) -> Optional[CachedResponse]:
        """캐시에서 응답 조회."""
        if not settings.cost_optimization.response_caching_enabled:
            return None

        query_hash = self._hash_query(query)

        if query_hash in self.cache:
            cached = self.cache[query_hash]

            # TTL 체크
            created = datetime.fromisoformat(cached.created_at)
            ttl = timedelta(seconds=settings.cost_optimization.cache_ttl_seconds)

            if datetime.now() - created < ttl:
                # 히트 카운트 증가
                cached.hit_count += 1
                self._save()
                return cached
            else:
                # 만료된 캐시 삭제
                del self.cache[query_hash]
                self._save()

        return None

    def set(self, query: str, response: str, model: str) -> CachedResponse:
        """응답을 캐시에 저장."""
        if not settings.cost_optimization.response_caching_enabled:
            return None

        query_hash = self._hash_query(query)

        # 캐시 크기 제한
        if len(self.cache) >= settings.cost_optimization.max_cache_size:
            self._evict_oldest()

        cached = CachedResponse(
            query_hash=query_hash,
            query=query,
            response=response,
            model=model,
            created_at=datetime.now().isoformat(),
            hit_count=0
        )

        self.cache[query_hash] = cached
        self._save()

        return cached

    def _evict_oldest(self) -> None:
        """가장 오래된/적게 사용된 캐시 항목 제거."""
        if not self.cache:
            return

        # 히트 카운트가 낮고 오래된 항목 제거
        sorted_items = sorted(
            self.cache.items(),
            key=lambda x: (x[1].hit_count, x[1].created_at)
        )

        # 하위 10% 제거
        to_remove = max(1, len(sorted_items) // 10)
        for hash_key, _ in sorted_items[:to_remove]:
            del self.cache[hash_key]

    def get_stats(self) -> dict:
        """캐시 통계 반환."""
        total_hits = sum(c.hit_count for c in self.cache.values())
        return {
            "total_entries": len(self.cache),
            "total_hits": total_hits,
            "max_size": settings.cost_optimization.max_cache_size,
            "ttl_seconds": settings.cost_optimization.cache_ttl_seconds,
        }

    def clear(self) -> None:
        """캐시 초기화."""
        self.cache = {}
        self._save()

    def _save(self) -> None:
        """캐시를 파일에 저장."""
        data = {k: asdict(v) for k, v in self.cache.items()}
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """파일에서 캐시 로드."""
        if not self.cache_path.exists():
            return

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.cache = {
                k: CachedResponse(**v) for k, v in data.items()
            }
        except (json.JSONDecodeError, KeyError):
            self.cache = {}


# 전역 캐시 서비스 인스턴스
cache_service = CacheService()
