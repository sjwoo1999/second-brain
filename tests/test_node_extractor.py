"""NodeExtractor 단위 테스트."""

import pytest
from interfaces.web.services.node_extractor import NodeExtractor
from interfaces.web.models.node import NodeType


class TestNodeExtractorQuestion:
    """질문 감지 테스트."""

    @pytest.mark.parametrize("text", [
        "파이썬이 뭐야?",
        "what is Python?",
        "뭐가 더 좋아",
        "어떻게 하면 돼",
        "왜 그런거야",
        "how does it work?",
        "can you help me?",
        "알려줘",
        "설명해줘",
    ])
    def test_is_question(self, node_extractor, text):
        """질문형 텍스트 감지."""
        assert node_extractor._is_question(text) is True

    @pytest.mark.parametrize("text", [
        "오늘 날씨 좋다",
        "좋은 아침입니다",
        "I had lunch",
    ])
    def test_is_not_question(self, node_extractor, text):
        """비질문형 텍스트."""
        assert node_extractor._is_question(text) is False

    def test_question_node_created(self, node_extractor, graph_service):
        """질문 메시지에서 질문 노드 생성."""
        nodes = node_extractor.extract_from_user_message("파이썬이 뭐야?")
        question_nodes = [n for n in nodes if n.type == NodeType.QUESTION]
        assert len(question_nodes) >= 1


class TestNodeExtractorTopics:
    """토픽 추출 테스트."""

    def test_korean_topics(self, node_extractor):
        """한글 토픽 추출."""
        topics = node_extractor._extract_topics("파이썬과 자바스크립트를 비교해줘")
        assert len(topics) >= 1
        # 2글자 이상의 한글 단어가 추출되어야 함
        assert all(len(t) >= 2 for t in topics)

    def test_english_topics(self, node_extractor):
        """영어 토픽 추출."""
        topics = node_extractor._extract_topics("Tell me about Python and JavaScript")
        assert len(topics) >= 1
        assert all(len(t) >= 3 for t in topics)

    def test_stopwords_excluded(self, node_extractor):
        """불용어 제외."""
        topics = node_extractor._extract_topics("그래서 그러면 하지만 Python")
        # 불용어는 제외되어야 함
        assert "그래서" not in topics
        assert "그러면" not in topics
        assert "하지만" not in topics

    def test_max_topics_limit(self, node_extractor):
        """최대 2개 토픽 제한."""
        topics = node_extractor._extract_topics(
            "파이썬 자바스크립트 러스트 고랭 타입스크립트"
        )
        assert len(topics) <= 2

    def test_topic_nodes_created(self, node_extractor, graph_service):
        """토픽 메시지에서 토픽 노드 생성."""
        nodes = node_extractor.extract_from_user_message("Python에 대해 알려줘")
        topic_nodes = [n for n in nodes if n.type == NodeType.TOPIC]
        assert len(topic_nodes) >= 1


class TestNodeExtractorInsights:
    """인사이트 추출 테스트."""

    @pytest.mark.parametrize("text,expected_count", [
        ("중요한 것은 코드의 가독성이다.", 1),
        ("핵심은 테스트 커버리지를 높이는 것이다.", 1),
        ("결론적으로 마이크로서비스가 적합하다.", 1),
        ("The key point is simplicity.", 1),
        ("아무 내용 없는 텍스트", 0),
    ])
    def test_extract_insights(self, node_extractor, text, expected_count):
        """인사이트 패턴 매칭."""
        insights = node_extractor._extract_insights(text)
        assert len(insights) == expected_count

    def test_insight_max_limit(self, node_extractor):
        """최대 2개 인사이트 제한."""
        text = "중요한 것은 가독성이다. 핵심은 테스트이다. 결론적으로 좋다."
        insights = node_extractor._extract_insights(text)
        assert len(insights) <= 2

    def test_insight_nodes_created(self, node_extractor, graph_service):
        """AI 응답에서 인사이트 노드 생성."""
        response = "중요한 것은 코드의 가독성이다. 이것이 핵심입니다."
        nodes = node_extractor.extract_from_assistant_response(response)
        insight_nodes = [n for n in nodes if n.type == NodeType.INSIGHT]
        assert len(insight_nodes) >= 1


class TestNodeExtractorKnowledge:
    """지식 추출 테스트."""

    @pytest.mark.parametrize("text,expected_count", [
        ("파이썬은 인터프리터 언어입니다.", 1),
        ("컴파일러는 소스 코드를 기계어로 변환하는 것을 의미합니다.", 1),
        ("Python is a high-level programming language.", 1),
        ("단순 텍스트", 0),
    ])
    def test_extract_knowledge(self, node_extractor, text, expected_count):
        """지식 정의 패턴 매칭."""
        knowledge = node_extractor._extract_knowledge(text)
        assert len(knowledge) == expected_count

    def test_knowledge_nodes_created(self, node_extractor, graph_service):
        """AI 응답에서 지식 노드 생성."""
        response = "Python is a versatile programming language."
        nodes = node_extractor.extract_from_assistant_response(response)
        knowledge_nodes = [n for n in nodes if n.type == NodeType.KNOWLEDGE]
        assert len(knowledge_nodes) >= 1


class TestNodeExtractorTool:
    """Tool 노드 생성 테스트."""

    def test_extract_tool_node(self, node_extractor, graph_service):
        """Tool 사용 시 노드 생성."""
        node = node_extractor.extract_tool_node("web_search", {"query": "Python"})
        assert node.type == NodeType.TOOL
        assert node.label == "web_search"

    def test_tool_node_dedup(self, node_extractor, graph_service):
        """같은 Tool 재사용 시 중복 안 생김."""
        n1 = node_extractor.extract_tool_node("web_search", {"query": "a"})
        n2 = node_extractor.extract_tool_node("web_search", {"query": "b"})
        assert n1.id == n2.id
        assert graph_service.node_count == 1
