"""채팅 API 라우트."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.orchestrator import Orchestrator
from ..services.graph_service import graph_service
from ..services.node_extractor import NodeExtractor


router = APIRouter(prefix="/api/chat", tags=["chat"])

# 간단한 REST 채팅용 Orchestrator
_orchestrator: Orchestrator | None = None
_node_extractor: NodeExtractor | None = None


def get_orchestrator() -> Orchestrator:
    """Orchestrator 인스턴스 반환."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def get_node_extractor() -> NodeExtractor:
    """NodeExtractor 인스턴스 반환."""
    global _node_extractor
    if _node_extractor is None:
        _node_extractor = NodeExtractor(graph_service)
    return _node_extractor


class ChatRequest(BaseModel):
    """채팅 요청."""
    message: str


class ChatResponse(BaseModel):
    """채팅 응답."""
    response: str
    nodes_added: int


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 메시지 처리."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="메시지가 비어있습니다")

    orchestrator = get_orchestrator()
    extractor = get_node_extractor()

    # 노드 추출 및 카운트
    nodes_count = 0

    # 사용자 메시지에서 노드 추출
    user_nodes = extractor.extract_from_user_message(request.message)
    nodes_count += len(user_nodes)

    try:
        # Orchestrator로 처리
        response = await orchestrator.process(request.message)

        # AI 응답에서 노드 추출
        response_nodes = extractor.extract_from_assistant_response(response)
        nodes_count += len(response_nodes)

        return ChatResponse(response=response, nodes_added=nodes_count)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history():
    """대화 기록 조회."""
    orchestrator = get_orchestrator()
    return {"history": orchestrator.get_history()}


@router.post("/clear")
async def clear_history():
    """대화 기록 초기화."""
    orchestrator = get_orchestrator()
    orchestrator.clear_history()
    return {"status": "cleared"}
