"""노드 추출기 - 대화에서 노드 자동 생성."""

import re
from typing import Optional
from ..models.node import Node, NodeType
from .graph_service import GraphService


class NodeExtractor:
    """대화에서 노드를 추출하는 서비스."""

    def __init__(self, graph_service: GraphService):
        self.graph = graph_service

    def extract_from_user_message(self, message: str) -> list[Node]:
        """사용자 메시지에서 노드 추출."""
        nodes = []

        # 질문 노드 생성 (질문형 메시지)
        if self._is_question(message):
            question_text = message[:50] + "..." if len(message) > 50 else message
            node, is_new = self.graph.find_or_create_node(
                NodeType.QUESTION,
                label=question_text,
                content=message
            )
            if is_new:
                nodes.append(node)
                self.graph.connect_to_recent(node, max_connections=2)

        # 토픽 추출 (키워드 기반)
        topics = self._extract_topics(message)
        for topic in topics:
            node, is_new = self.graph.find_or_create_node(
                NodeType.TOPIC,
                label=topic,
                content=f"토픽: {topic}"
            )
            if is_new:
                nodes.append(node)
                self.graph.connect_to_recent(node, max_connections=2)

        return nodes

    def extract_from_assistant_response(self, response: str) -> list[Node]:
        """AI 응답에서 노드 추출."""
        nodes = []

        # 인사이트 노드 (중요한 정보 포함 시)
        insights = self._extract_insights(response)
        for insight in insights:
            node, is_new = self.graph.find_or_create_node(
                NodeType.INSIGHT,
                label=insight[:30] + "..." if len(insight) > 30 else insight,
                content=insight
            )
            if is_new:
                nodes.append(node)
                self.graph.connect_to_recent(node, max_connections=2)

        # 지식 노드 (설명이나 정의 포함 시)
        knowledge = self._extract_knowledge(response)
        for item in knowledge:
            node, is_new = self.graph.find_or_create_node(
                NodeType.KNOWLEDGE,
                label=item[:30] + "..." if len(item) > 30 else item,
                content=item
            )
            if is_new:
                nodes.append(node)
                self.graph.connect_to_recent(node, max_connections=2)

        return nodes

    def extract_tool_node(self, tool_name: str, tool_input: dict) -> Node:
        """Tool 사용 시 노드 생성."""
        node, is_new = self.graph.find_or_create_node(
            NodeType.TOOL,
            label=tool_name,
            content=f"Tool: {tool_name}\nInput: {tool_input}"
        )
        if is_new:
            self.graph.connect_to_recent(node, max_connections=2)
        return node

    def _is_question(self, text: str) -> bool:
        """질문인지 확인."""
        question_patterns = [
            r"\?$",
            r"^(뭐|무엇|어떻게|왜|언제|어디|누가|얼마)",
            r"(알려|설명|가르쳐)",
            r"^(what|how|why|when|where|who|can|could|would|is|are|do|does)",
        ]
        text_lower = text.lower().strip()
        return any(re.search(p, text_lower) for p in question_patterns)

    def _extract_topics(self, text: str) -> list[str]:
        """텍스트에서 주요 토픽 추출."""
        topics = []

        # 한글 명사 패턴 (2글자 이상)
        korean_nouns = re.findall(r'[가-힣]{2,}', text)
        # 영어 단어 패턴 (3글자 이상)
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)

        # 불용어 제외
        stopwords = {
            "그래서", "그러면", "하지만", "그리고", "또한", "때문에",
            "the", "and", "for", "with", "this", "that", "from"
        }

        for word in korean_nouns + english_words:
            if word.lower() not in stopwords and len(word) >= 2:
                topics.append(word)
                if len(topics) >= 2:  # 최대 2개
                    break

        return topics

    def _extract_insights(self, text: str) -> list[str]:
        """응답에서 인사이트 추출."""
        insights = []

        # 중요 패턴 찾기
        patterns = [
            r"중요한 것은[^.]*\.",
            r"핵심은[^.]*\.",
            r"결론적으로[^.]*\.",
            r"The key (is|point)[^.]*\.",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            insights.extend(matches[:1])  # 패턴당 하나만

        return insights[:2]  # 최대 2개

    def _extract_knowledge(self, text: str) -> list[str]:
        """응답에서 지식 추출."""
        knowledge = []

        # 정의/설명 패턴
        patterns = [
            r"[가-힣a-zA-Z]+[은는이가]\s[^.]+입니다\.",
            r"[가-힣a-zA-Z]+[은는]\s[^.]+을 의미합니다\.",
            r"[A-Z][a-z]+ is [^.]+\.",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            knowledge.extend(matches[:1])

        return knowledge[:2]
