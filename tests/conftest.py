"""공통 테스트 fixture."""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def memory_service(tmp_path):
    """In-memory SQLite 기반 MemoryService."""
    db_path = str(tmp_path / "test_memory.db")
    from core.memory_service import MemoryService
    return MemoryService(db_path=db_path)


@pytest.fixture
def graph_service(tmp_path):
    """임시 파일 기반 GraphService."""
    data_path = tmp_path / "test_graph.json"
    from interfaces.web.services.graph_service import GraphService
    return GraphService(data_path=data_path)


@pytest.fixture
def cost_tracker(tmp_path):
    """임시 파일 기반 CostTracker."""
    persist_path = tmp_path / "test_cost.json"
    from core.cost_tracker import CostTracker
    return CostTracker(persist_path=persist_path)


@pytest.fixture
def cache_service(tmp_path):
    """임시 파일 기반 CacheService."""
    cache_path = tmp_path / "test_cache.json"
    from core.cache_service import CacheService
    return CacheService(cache_path=cache_path)


@pytest.fixture
def model_router():
    """ModelRouter 인스턴스."""
    from core.model_router import ModelRouter
    return ModelRouter()


@pytest.fixture
def node_extractor(graph_service):
    """NodeExtractor 인스턴스."""
    from interfaces.web.services.node_extractor import NodeExtractor
    return NodeExtractor(graph_service)


@pytest.fixture
def mock_anthropic():
    """Anthropic 클라이언트 mock."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="[]")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def test_client(tmp_path):
    """FastAPI TestClient with mocked services."""
    from unittest.mock import patch, MagicMock

    # Mock the global service instances before importing app
    mock_orchestrator = MagicMock()
    mock_orchestrator.process = MagicMock(return_value="테스트 응답")
    mock_orchestrator.get_history.return_value = []

    with patch("interfaces.web.routes.chat.get_orchestrator", return_value=mock_orchestrator), \
         patch("interfaces.web.routes.chat.get_node_extractor") as mock_ext_fn:

        mock_extractor = MagicMock()
        mock_extractor.extract_from_user_message.return_value = []
        mock_extractor.extract_from_assistant_response.return_value = []
        mock_ext_fn.return_value = mock_extractor

        from fastapi.testclient import TestClient
        from interfaces.web.app import create_app

        app = create_app()
        client = TestClient(app)
        client._mock_orchestrator = mock_orchestrator
        client._mock_extractor = mock_extractor
        yield client
