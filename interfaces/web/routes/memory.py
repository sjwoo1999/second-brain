"""메모리 REST API 라우트."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from core.memory_service import memory_service
from interfaces.web.models.memory import (
    MemoryType, Memory, MemoryCreate, MemoryUpdate, MemoryStats
)

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/", response_model=list[Memory])
async def list_memories(
    type: Optional[MemoryType] = Query(None, description="메모리 타입 필터"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """메모리 목록 조회."""
    return memory_service.list_memories(
        type_filter=type,
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=MemoryStats)
async def get_stats():
    """메모리 통계."""
    return memory_service.get_stats()


@router.get("/search", response_model=list[Memory])
async def search_memories(
    q: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(20, ge=1, le=100),
):
    """메모리 전문 검색."""
    return memory_service.search(q, limit=limit)


@router.get("/{memory_id}", response_model=Memory)
async def get_memory(memory_id: str):
    """단일 메모리 조회."""
    memory = memory_service.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="메모리를 찾을 수 없습니다")
    return memory


@router.post("/", response_model=Memory, status_code=201)
async def create_memory(data: MemoryCreate):
    """메모리 수동 생성."""
    return memory_service.create(data)


@router.put("/{memory_id}", response_model=Memory)
async def update_memory(memory_id: str, data: MemoryUpdate):
    """메모리 수정."""
    memory = memory_service.update(memory_id, data)
    if not memory:
        raise HTTPException(status_code=404, detail="메모리를 찾을 수 없습니다")
    return memory


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """메모리 소프트 삭제."""
    success = memory_service.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="메모리를 찾을 수 없습니다")
    return {"status": "deleted", "id": memory_id}
