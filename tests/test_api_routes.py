"""API 라우트 통합 테스트."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from interfaces.web.models.memory import MemoryType, Memory, MemoryStats
from interfaces.web.models.node import NodeType
from core.cost_tracker import CostStats


@pytest.fixture
def app_client(tmp_path):
    """독립적인 FastAPI TestClient."""
    # memory_service mock
    mock_memory_svc = MagicMock()
    mock_memory_svc.list_memories.return_value = []
    mock_memory_svc.search.return_value = []
    mock_memory_svc.get_stats.return_value = MemoryStats(
        total=5, active=4, by_type={"record": 3, "plan": 1},
        recent_count=2, total_conversations=10,
    )
    mock_memory_svc.get.return_value = None

    # graph_service mock
    mock_graph_svc = MagicMock()
    mock_graph_svc.get_graph_data.return_value = MagicMock(
        model_dump=lambda: {"nodes": [], "links": []}
    )
    mock_graph_svc.node_count = 0
    mock_graph_svc.edge_count = 0
    mock_graph_svc.get_nodes_by_type.return_value = []
    mock_graph_svc.get_all_nodes.return_value = []

    # cost_tracker / cache_service mock
    mock_cost_tracker = MagicMock()
    mock_cost_tracker.get_stats.return_value = CostStats()
    mock_cost_tracker.get_recent_usage.return_value = []

    mock_cache_svc = MagicMock()
    mock_cache_svc.get_stats.return_value = {
        "total_entries": 0, "total_hits": 0,
        "max_size": 1000, "ttl_seconds": 3600,
    }

    # orchestrator mock
    mock_orchestrator = MagicMock()
    mock_orchestrator.process = AsyncMock(return_value="테스트 응답")
    mock_orchestrator.get_history.return_value = []

    mock_extractor = MagicMock()
    mock_extractor.extract_from_user_message.return_value = []
    mock_extractor.extract_from_assistant_response.return_value = []

    with patch("interfaces.web.routes.memory.memory_service", mock_memory_svc), \
         patch("interfaces.web.routes.graph.graph_service", mock_graph_svc), \
         patch("interfaces.web.routes.cost.cost_tracker", mock_cost_tracker), \
         patch("interfaces.web.routes.cost.cache_service", mock_cache_svc), \
         patch("interfaces.web.routes.chat.get_orchestrator", return_value=mock_orchestrator), \
         patch("interfaces.web.routes.chat.get_node_extractor", return_value=mock_extractor):

        from interfaces.web.app import create_app
        app = create_app()
        client = TestClient(app)
        client._mocks = {
            "memory_service": mock_memory_svc,
            "graph_service": mock_graph_svc,
            "cost_tracker": mock_cost_tracker,
            "cache_service": mock_cache_svc,
            "orchestrator": mock_orchestrator,
            "extractor": mock_extractor,
        }
        yield client


class TestHealthEndpoint:
    """헬스체크 엔드포인트."""

    def test_health(self, app_client):
        """GET /health → 200."""
        resp = app_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestChatEndpoint:
    """채팅 엔드포인트."""

    def test_chat_success(self, app_client):
        """POST /api/chat → 응답."""
        resp = app_client.post("/api/chat/", json={"message": "안녕하세요"})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "nodes_added" in data
        assert data["response"] == "테스트 응답"

    def test_chat_empty_message(self, app_client):
        """빈 메시지 → 400."""
        resp = app_client.post("/api/chat/", json={"message": ""})
        assert resp.status_code == 400

    def test_chat_history(self, app_client):
        """GET /api/chat/history."""
        resp = app_client.get("/api/chat/history")
        assert resp.status_code == 200
        assert "history" in resp.json()

    def test_chat_clear(self, app_client):
        """POST /api/chat/clear."""
        resp = app_client.post("/api/chat/clear")
        assert resp.status_code == 200


class TestMemoryEndpoints:
    """메모리 엔드포인트."""

    def test_list_memories(self, app_client):
        """GET /api/memory → 목록."""
        resp = app_client.get("/api/memory/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_memory(self, app_client):
        """POST /api/memory → 201 생성."""
        mock_memory = Memory(
            type=MemoryType.RECORD,
            content="테스트 내용",
            summary="요약",
        )
        app_client._mocks["memory_service"].create.return_value = mock_memory

        resp = app_client.post("/api/memory/", json={
            "type": "record",
            "content": "테스트 내용",
            "summary": "요약",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "record"
        assert data["content"] == "테스트 내용"

    def test_get_memory_not_found(self, app_client):
        """GET /api/memory/{id} → 404."""
        app_client._mocks["memory_service"].get.return_value = None
        resp = app_client.get("/api/memory/nonexistent")
        assert resp.status_code == 404

    def test_get_memory_found(self, app_client):
        """GET /api/memory/{id} → 200."""
        mock_memory = Memory(
            type=MemoryType.RECORD,
            content="내용",
        )
        app_client._mocks["memory_service"].get.return_value = mock_memory
        resp = app_client.get(f"/api/memory/{mock_memory.id}")
        assert resp.status_code == 200

    def test_search_memories(self, app_client):
        """GET /api/memory/search?q=test."""
        resp = app_client.get("/api/memory/search", params={"q": "test"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_memory_stats(self, app_client):
        """GET /api/memory/stats."""
        resp = app_client.get("/api/memory/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert data["active"] == 4

    def test_delete_memory(self, app_client):
        """DELETE /api/memory/{id}."""
        app_client._mocks["memory_service"].delete.return_value = True
        resp = app_client.delete("/api/memory/some-id")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_memory_not_found(self, app_client):
        """DELETE /api/memory/{id} → 404."""
        app_client._mocks["memory_service"].delete.return_value = False
        resp = app_client.delete("/api/memory/nonexistent")
        assert resp.status_code == 404


class TestGraphEndpoints:
    """그래프 엔드포인트."""

    def test_get_graph(self, app_client):
        """GET /api/graph → 그래프 데이터."""
        resp = app_client.get("/api/graph/")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "links" in data

    def test_get_nodes(self, app_client):
        """GET /api/graph/nodes."""
        resp = app_client.get("/api/graph/nodes")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "count" in data

    def test_get_graph_stats(self, app_client):
        """GET /api/graph/stats."""
        resp = app_client.get("/api/graph/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "node_count" in data
        assert "edge_count" in data


class TestCostEndpoints:
    """비용 엔드포인트."""

    def test_get_cost_stats(self, app_client):
        """GET /api/cost/stats → 통합 통계."""
        resp = app_client.get("/api/cost/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "cost" in data
        assert "cache" in data
        assert "total_requests" in data["cost"]

    def test_get_cost_history(self, app_client):
        """GET /api/cost/history."""
        resp = app_client.get("/api/cost/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "records" in data

    def test_reset_cost(self, app_client):
        """POST /api/cost/reset."""
        resp = app_client.post("/api/cost/reset")
        assert resp.status_code == 200

    def test_clear_cache(self, app_client):
        """POST /api/cost/clear-cache."""
        resp = app_client.post("/api/cost/clear-cache")
        assert resp.status_code == 200

    def test_get_pricing(self, app_client):
        """GET /api/cost/pricing."""
        resp = app_client.get("/api/cost/pricing")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "haiku" in data["models"]
