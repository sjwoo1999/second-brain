"""메모리 데이터 모델."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class MemoryType(str, Enum):
    """메모리 타입."""
    THINKING_PATTERN = "thinking_pattern"  # 사용자의 사고 방식
    RECORD = "record"                      # 기록 (사실, 경험)
    PLAN = "plan"                          # 계획, 목표
    CONTEXT = "context"                    # 대화 맥락 정보
    PREFERENCE = "preference"              # 선호도, 취향


# 메모리 타입별 아이콘/색상
MEMORY_TYPE_META = {
    MemoryType.THINKING_PATTERN: {"icon": "🧠", "color": "#8B5CF6"},
    MemoryType.RECORD: {"icon": "📝", "color": "#3B82F6"},
    MemoryType.PLAN: {"icon": "🎯", "color": "#10B981"},
    MemoryType.CONTEXT: {"icon": "💡", "color": "#F59E0B"},
    MemoryType.PREFERENCE: {"icon": "⭐", "color": "#EC4899"},
}


class Memory(BaseModel):
    """메모리 엔티티."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType
    category: str = ""
    content: str
    summary: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    access_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class MemoryCreate(BaseModel):
    """메모리 생성 입력."""

    type: MemoryType
    category: str = ""
    content: str
    summary: str = ""
    confidence: float = 0.8


class MemoryUpdate(BaseModel):
    """메모리 수정 입력."""

    type: Optional[MemoryType] = None
    category: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    is_active: Optional[bool] = None


class MemoryStats(BaseModel):
    """메모리 통계."""

    total: int = 0
    active: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    recent_count: int = 0  # 최근 24시간
    total_conversations: int = 0
