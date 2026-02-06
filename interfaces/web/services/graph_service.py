"""그래프 서비스 - 노드와 엣지 관리."""

import json
from pathlib import Path
from typing import Optional
from ..models.node import Node, Edge, NodeType, GraphData
from config.settings import settings


class GraphService:
    """그래프 데이터 관리 서비스."""

    def __init__(self, data_path: Optional[Path] = None):
        self._data_path = data_path or settings.base_dir / "data" / "graph.json"
        self._data_path.parent.mkdir(parents=True, exist_ok=True)

        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}
        self._connections: set[tuple[str, str]] = set()

        # 저장된 데이터 로드
        self._load()

    def add_node(self, node: Node) -> Node:
        """노드 추가."""
        self._nodes[node.id] = node
        self._save()
        return node

    def add_edge(self, source_id: str, target_id: str, label: Optional[str] = None) -> Optional[Edge]:
        """엣지 추가."""
        # 노드 존재 확인
        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        # 중복 연결 방지
        connection = (source_id, target_id)
        if connection in self._connections:
            return None

        edge = Edge(source=source_id, target=target_id, label=label)
        self._edges[edge.id] = edge
        self._connections.add(connection)
        self._save()
        return edge

    def get_node(self, node_id: str) -> Optional[Node]:
        """노드 조회."""
        return self._nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> list[Node]:
        """타입별 노드 조회."""
        return [n for n in self._nodes.values() if n.type == node_type]

    def get_all_nodes(self) -> list[Node]:
        """모든 노드 조회."""
        return list(self._nodes.values())

    def get_all_edges(self) -> list[Edge]:
        """모든 엣지 조회."""
        return list(self._edges.values())

    def get_graph_data(self) -> GraphData:
        """그래프 시각화용 데이터 반환."""
        nodes = [node.to_graph_node() for node in self._nodes.values()]
        links = [edge.to_graph_edge() for edge in self._edges.values()]
        return GraphData(nodes=nodes, links=links)

    def find_or_create_node(
        self,
        node_type: NodeType,
        label: str,
        content: Optional[str] = None
    ) -> tuple[Node, bool]:
        """기존 노드 찾거나 새로 생성. (node, is_new) 반환."""
        # 같은 타입과 레이블의 노드가 있는지 확인
        for node in self._nodes.values():
            if node.type == node_type and node.label.lower() == label.lower():
                return node, False

        # 없으면 새로 생성
        node = Node(type=node_type, label=label, content=content)
        self.add_node(node)
        return node, True

    def connect_to_recent(self, node: Node, max_connections: int = 3) -> list[Edge]:
        """최근 노드들과 연결."""
        edges = []
        recent_nodes = sorted(
            [n for n in self._nodes.values() if n.id != node.id],
            key=lambda n: n.created_at,
            reverse=True
        )[:max_connections]

        for recent in recent_nodes:
            edge = self.add_edge(recent.id, node.id)
            if edge:
                edges.append(edge)

        return edges

    def clear(self) -> None:
        """그래프 초기화."""
        self._nodes.clear()
        self._edges.clear()
        self._connections.clear()
        self._save()

    @property
    def node_count(self) -> int:
        """노드 개수."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """엣지 개수."""
        return len(self._edges)

    def _save(self) -> None:
        """그래프 데이터를 파일에 저장."""
        data = {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "label": n.label,
                    "content": n.content,
                    "created_at": n.created_at.isoformat() if hasattr(n.created_at, 'isoformat') else str(n.created_at)
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "label": e.label
                }
                for e in self._edges.values()
            ]
        }
        with open(self._data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """파일에서 그래프 데이터 로드."""
        if not self._data_path.exists():
            return

        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 노드 로드
            for node_data in data.get("nodes", []):
                node = Node(
                    type=NodeType(node_data["type"]),
                    label=node_data["label"],
                    content=node_data.get("content")
                )
                node.id = node_data["id"]
                self._nodes[node.id] = node

            # 엣지 로드
            for edge_data in data.get("edges", []):
                edge = Edge(
                    source=edge_data["source"],
                    target=edge_data["target"],
                    label=edge_data.get("label")
                )
                edge.id = edge_data["id"]
                self._edges[edge.id] = edge
                self._connections.add((edge.source, edge.target))

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[GraphService] 데이터 로드 실패: {e}")
            self._nodes = {}
            self._edges = {}
            self._connections = set()


# 전역 그래프 서비스 인스턴스
graph_service = GraphService()
