"""노드 모델 정의."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class NodeType(str, Enum):
    """노드 타입."""
    TOPIC = "topic"          # 대화 주제 (보라)
    TOOL = "tool"            # 사용한 Tool (초록)
    KNOWLEDGE = "knowledge"  # 학습한 지식 (노랑)
    QUESTION = "question"    # 사용자 질문 (파랑)
    INSIGHT = "insight"      # AI 인사이트 (핑크)


# 노드 타입별 색상
NODE_COLORS = {
    NodeType.TOPIC: "#8B5CF6",      # 보라
    NodeType.TOOL: "#10B981",       # 초록
    NodeType.KNOWLEDGE: "#F59E0B",  # 노랑
    NodeType.QUESTION: "#3B82F6",   # 파랑
    NodeType.INSIGHT: "#EC4899",    # 핑크
}


class Node(BaseModel):
    """그래프 노드."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: NodeType
    label: str
    content: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)

    @property
    def color(self) -> str:
        """노드 색상 반환."""
        return NODE_COLORS.get(self.type, "#6B7280")

    def to_graph_node(self) -> dict:
        """그래프 시각화용 데이터 반환."""
        return {
            "id": self.id,
            "type": self.type.value,
            "label": self.label,
            "content": self.content,
            "color": self.color,
            "val": 1,  # 노드 크기
        }


class Edge(BaseModel):
    """그래프 엣지 (연결선)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str  # 시작 노드 ID
    target: str  # 끝 노드 ID
    label: Optional[str] = None
    weight: float = 1.0

    def to_graph_edge(self) -> dict:
        """그래프 시각화용 데이터 반환."""
        return {
            "source": self.source,
            "target": self.target,
            "label": self.label,
        }


class GraphData(BaseModel):
    """전체 그래프 데이터."""

    nodes: list[dict] = Field(default_factory=list)
    links: list[dict] = Field(default_factory=list)
