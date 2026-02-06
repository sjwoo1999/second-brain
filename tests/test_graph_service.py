"""GraphService 단위 테스트."""

import pytest
from interfaces.web.models.node import Node, NodeType


class TestGraphServiceNode:
    """노드 관련 테스트."""

    def test_add_and_get_node(self, graph_service):
        """노드 추가 및 조회."""
        node = Node(type=NodeType.TOPIC, label="Python", content="프로그래밍 언어")
        added = graph_service.add_node(node)

        assert added.id == node.id
        assert graph_service.node_count == 1

        fetched = graph_service.get_node(node.id)
        assert fetched is not None
        assert fetched.label == "Python"

    def test_get_nonexistent_node(self, graph_service):
        """존재하지 않는 노드 조회."""
        assert graph_service.get_node("nonexistent") is None

    def test_get_nodes_by_type(self, graph_service):
        """타입별 노드 조회."""
        graph_service.add_node(Node(type=NodeType.TOPIC, label="Python"))
        graph_service.add_node(Node(type=NodeType.TOPIC, label="JavaScript"))
        graph_service.add_node(Node(type=NodeType.QUESTION, label="뭐가 좋아?"))

        topics = graph_service.get_nodes_by_type(NodeType.TOPIC)
        assert len(topics) == 2
        questions = graph_service.get_nodes_by_type(NodeType.QUESTION)
        assert len(questions) == 1

    def test_get_all_nodes(self, graph_service):
        """전체 노드 조회."""
        graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        graph_service.add_node(Node(type=NodeType.KNOWLEDGE, label="B"))
        assert len(graph_service.get_all_nodes()) == 2


class TestGraphServiceEdge:
    """엣지 관련 테스트."""

    def test_add_edge(self, graph_service):
        """엣지 생성."""
        n1 = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        n2 = graph_service.add_node(Node(type=NodeType.TOPIC, label="B"))

        edge = graph_service.add_edge(n1.id, n2.id, label="관련")
        assert edge is not None
        assert edge.source == n1.id
        assert edge.target == n2.id
        assert edge.label == "관련"
        assert graph_service.edge_count == 1

    def test_add_edge_nonexistent_node(self, graph_service):
        """존재하지 않는 노드에 엣지 생성 시 None."""
        n1 = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        result = graph_service.add_edge(n1.id, "nonexistent")
        assert result is None

    def test_duplicate_edge_prevention(self, graph_service):
        """중복 엣지 방지."""
        n1 = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        n2 = graph_service.add_node(Node(type=NodeType.TOPIC, label="B"))

        edge1 = graph_service.add_edge(n1.id, n2.id)
        edge2 = graph_service.add_edge(n1.id, n2.id)  # 중복
        assert edge1 is not None
        assert edge2 is None
        assert graph_service.edge_count == 1

    def test_get_all_edges(self, graph_service):
        """전체 엣지 조회."""
        n1 = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        n2 = graph_service.add_node(Node(type=NodeType.TOPIC, label="B"))
        n3 = graph_service.add_node(Node(type=NodeType.TOPIC, label="C"))

        graph_service.add_edge(n1.id, n2.id)
        graph_service.add_edge(n2.id, n3.id)

        edges = graph_service.get_all_edges()
        assert len(edges) == 2


class TestGraphServiceFindOrCreate:
    """find_or_create_node 테스트."""

    def test_create_new_node(self, graph_service):
        """새 노드 생성."""
        node, is_new = graph_service.find_or_create_node(
            NodeType.TOPIC, "Python", "프로그래밍 언어"
        )
        assert is_new is True
        assert node.label == "Python"
        assert graph_service.node_count == 1

    def test_find_existing_node(self, graph_service):
        """기존 노드 반환 (대소문자 무시)."""
        node1, _ = graph_service.find_or_create_node(NodeType.TOPIC, "Python")
        node2, is_new = graph_service.find_or_create_node(NodeType.TOPIC, "python")

        assert is_new is False
        assert node2.id == node1.id
        assert graph_service.node_count == 1

    def test_different_type_creates_new(self, graph_service):
        """다른 타입은 새 노드 생성."""
        n1, _ = graph_service.find_or_create_node(NodeType.TOPIC, "Python")
        n2, is_new = graph_service.find_or_create_node(NodeType.KNOWLEDGE, "Python")

        assert is_new is True
        assert n1.id != n2.id
        assert graph_service.node_count == 2


class TestGraphServiceConnectRecent:
    """connect_to_recent 테스트."""

    def test_connect_to_recent(self, graph_service):
        """최근 노드와 연결."""
        n1 = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        n2 = graph_service.add_node(Node(type=NodeType.TOPIC, label="B"))
        n3 = graph_service.add_node(Node(type=NodeType.TOPIC, label="C"))

        # n3를 최근 노드들과 연결
        new_node = graph_service.add_node(Node(type=NodeType.TOPIC, label="D"))
        edges = graph_service.connect_to_recent(new_node, max_connections=2)

        assert len(edges) <= 2
        assert graph_service.edge_count >= 1

    def test_connect_to_recent_empty(self, graph_service):
        """다른 노드 없을 때."""
        node = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        edges = graph_service.connect_to_recent(node)
        assert len(edges) == 0


class TestGraphServiceGraphData:
    """get_graph_data 테스트."""

    def test_get_graph_data(self, graph_service):
        """그래프 데이터 직렬화."""
        n1 = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        n2 = graph_service.add_node(Node(type=NodeType.QUESTION, label="B?"))
        graph_service.add_edge(n1.id, n2.id)

        data = graph_service.get_graph_data()
        assert len(data.nodes) == 2
        assert len(data.links) == 1

        # 노드 직렬화 형태 확인
        node_dict = data.nodes[0]
        assert "id" in node_dict
        assert "type" in node_dict
        assert "label" in node_dict
        assert "color" in node_dict

    def test_get_graph_data_empty(self, graph_service):
        """빈 그래프."""
        data = graph_service.get_graph_data()
        assert data.nodes == []
        assert data.links == []


class TestGraphServiceClear:
    """초기화 테스트."""

    def test_clear(self, graph_service):
        """clear() 동작."""
        n1 = graph_service.add_node(Node(type=NodeType.TOPIC, label="A"))
        n2 = graph_service.add_node(Node(type=NodeType.TOPIC, label="B"))
        graph_service.add_edge(n1.id, n2.id)

        graph_service.clear()
        assert graph_service.node_count == 0
        assert graph_service.edge_count == 0


class TestGraphServicePersistence:
    """영속성 테스트."""

    def test_persist_and_load(self, tmp_path):
        """저장 후 로드."""
        from interfaces.web.services.graph_service import GraphService

        path = tmp_path / "persist_graph.json"
        svc1 = GraphService(data_path=path)
        svc1.add_node(Node(type=NodeType.TOPIC, label="Python"))

        svc2 = GraphService(data_path=path)
        assert svc2.node_count == 1
        nodes = svc2.get_all_nodes()
        assert nodes[0].label == "Python"
