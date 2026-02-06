"""비용 API 라우터."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.cost_tracker import cost_tracker
from core.cache_service import cache_service


router = APIRouter(prefix="/api/cost", tags=["cost"])


class CostStatsResponse(BaseModel):
    """비용 통계 응답."""
    total_input_tokens: int
    total_output_tokens: int
    total_cache_write_tokens: int
    total_cache_read_tokens: int
    total_cost_usd: float
    total_requests: int
    cache_hits: int
    local_cache_hits: int
    cache_hit_rate: float
    estimated_savings_usd: float
    model_usage: dict


class CacheStatsResponse(BaseModel):
    """캐시 통계 응답."""
    total_entries: int
    total_hits: int
    max_size: int
    ttl_seconds: int


class CombinedStatsResponse(BaseModel):
    """통합 통계 응답."""
    cost: CostStatsResponse
    cache: CacheStatsResponse


@router.get("/stats", response_model=CombinedStatsResponse)
async def get_cost_stats():
    """비용 및 캐시 통계 조회."""
    cost_stats = cost_tracker.get_stats().to_dict()
    cache_stats = cache_service.get_stats()

    return CombinedStatsResponse(
        cost=CostStatsResponse(**cost_stats),
        cache=CacheStatsResponse(**cache_stats)
    )


@router.get("/history")
async def get_cost_history(hours: int = 24):
    """최근 비용 기록 조회."""
    recent = cost_tracker.get_recent_usage(hours=hours)
    return {
        "hours": hours,
        "records": [
            {
                "timestamp": r.timestamp,
                "model": r.model,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cost_usd": r.cost_usd,
                "cached": r.cached,
                "from_local_cache": r.from_local_cache,
            }
            for r in recent
        ]
    }


@router.post("/reset")
async def reset_cost_stats():
    """비용 통계 초기화."""
    cost_tracker.reset()
    return {"status": "success", "message": "비용 통계가 초기화되었습니다"}


@router.post("/clear-cache")
async def clear_response_cache():
    """응답 캐시 초기화."""
    cache_service.clear()
    return {"status": "success", "message": "응답 캐시가 초기화되었습니다"}


@router.get("/pricing")
async def get_pricing_info():
    """모델 가격 정보 조회."""
    from config.settings import MODEL_PRICING, MODEL_ALIASES

    return {
        "models": {
            alias: {
                "full_name": full_name,
                "pricing": {
                    "input_cost_per_mtok": MODEL_PRICING[full_name].input_cost,
                    "output_cost_per_mtok": MODEL_PRICING[full_name].output_cost,
                    "cache_write_cost_per_mtok": MODEL_PRICING[full_name].cache_write_cost,
                    "cache_read_cost_per_mtok": MODEL_PRICING[full_name].cache_read_cost,
                }
            }
            for alias, full_name in MODEL_ALIASES.items()
        }
    }
