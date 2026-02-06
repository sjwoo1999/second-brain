"""그래프 API 라우트."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.node import NodeType, Node
from ..services.graph_service import graph_service


router = APIRouter(prefix="/api/graph", tags=["graph"])


class CreateNodeRequest(BaseModel):
    """노드 생성 요청."""
    type: NodeType
    label: str
    content: Optional[str] = None


class NodeResponse(BaseModel):
    """노드 응답."""
    id: str
    type: str
    label: str
    content: Optional[str]
    color: str


@router.get("/")
async def get_graph():
    """전체 그래프 데이터 조회."""
    return graph_service.get_graph_data().model_dump()


@router.get("/nodes")
async def get_nodes(type: Optional[NodeType] = None):
    """노드 목록 조회."""
    if type:
        nodes = graph_service.get_nodes_by_type(type)
    else:
        nodes = graph_service.get_all_nodes()

    return {
        "nodes": [node.to_graph_node() for node in nodes],
        "count": len(nodes)
    }


@router.get("/nodes/{node_id}")
async def get_node(node_id: str):
    """특정 노드 조회."""
    node = graph_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="노드를 찾을 수 없습니다")

    return node.to_graph_node()


@router.post("/nodes", response_model=NodeResponse)
async def create_node(request: CreateNodeRequest):
    """노드 수동 생성."""
    node, is_new = graph_service.find_or_create_node(
        request.type,
        request.label,
        request.content
    )

    if is_new:
        graph_service.connect_to_recent(node, max_connections=2)

    return NodeResponse(
        id=node.id,
        type=node.type.value,
        label=node.label,
        content=node.content,
        color=node.color
    )


@router.post("/edges")
async def create_edge(source_id: str, target_id: str, label: Optional[str] = None):
    """엣지 생성."""
    edge = graph_service.add_edge(source_id, target_id, label)
    if not edge:
        raise HTTPException(status_code=400, detail="엣지를 생성할 수 없습니다")

    return edge.to_graph_edge()


@router.delete("/clear")
async def clear_graph():
    """그래프 초기화."""
    graph_service.clear()
    return {"status": "cleared"}


@router.get("/stats")
async def get_stats():
    """그래프 통계."""
    return {
        "node_count": graph_service.node_count,
        "edge_count": graph_service.edge_count,
        "nodes_by_type": {
            t.value: len(graph_service.get_nodes_by_type(t))
            for t in NodeType
        }
    }
