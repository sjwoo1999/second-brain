"""ToolRegistry 및 BaseTool 단위 테스트."""

import pytest
from unittest.mock import AsyncMock

from core.registry import ToolRegistry
from core.base_tool import BaseTool, ToolCategory, ToolParameter, ToolResult


class DummyTool(BaseTool):
    """테스트용 Tool."""

    @property
    def name(self):
        return "dummy_tool"

    @property
    def description(self):
        return "테스트용 도구입니다"

    @property
    def category(self):
        return ToolCategory.SEARCH

    @property
    def parameters(self):
        return [
            ToolParameter(name="query", type="string", description="검색어", required=True),
            ToolParameter(name="limit", type="number", description="제한", required=False, default=10),
            ToolParameter(
                name="sort", type="string", description="정렬",
                required=False, enum=["asc", "desc"]
            ),
        ]

    async def execute(self, **kwargs):
        return ToolResult(success=True, data=f"결과: {kwargs.get('query')}")


class AnotherTool(BaseTool):
    """두 번째 테스트 Tool."""

    @property
    def name(self):
        return "another_tool"

    @property
    def description(self):
        return "Another tool for analysis"

    @property
    def category(self):
        return ToolCategory.ANALYSIS

    @property
    def parameters(self):
        return []

    async def execute(self, **kwargs):
        return ToolResult(success=True, data="done")


class TestToolRegistry:
    """ToolRegistry 테스트."""

    @pytest.fixture
    def registry(self):
        return ToolRegistry()

    def test_register(self, registry):
        """Tool 등록."""
        tool = DummyTool()
        registry.register(tool)
        assert len(registry) == 1
        assert "dummy_tool" in registry

    def test_register_duplicate_raises(self, registry):
        """중복 등록 에러."""
        registry.register(DummyTool())
        with pytest.raises(ValueError, match="이미 등록된 Tool"):
            registry.register(DummyTool())

    def test_unregister(self, registry):
        """Tool 등록 해제."""
        registry.register(DummyTool())
        assert registry.unregister("dummy_tool") is True
        assert len(registry) == 0

    def test_unregister_not_found(self, registry):
        """없는 Tool 해제."""
        assert registry.unregister("nonexistent") is False

    def test_get(self, registry):
        """이름으로 조회."""
        tool = DummyTool()
        registry.register(tool)
        assert registry.get("dummy_tool") is tool
        assert registry.get("nonexistent") is None

    def test_get_by_category(self, registry):
        """카테고리 조회."""
        registry.register(DummyTool())
        registry.register(AnotherTool())
        search_tools = registry.get_by_category(ToolCategory.SEARCH)
        assert len(search_tools) == 1
        assert search_tools[0].name == "dummy_tool"

    def test_list_all(self, registry):
        """전체 목록."""
        registry.register(DummyTool())
        registry.register(AnotherTool())
        tools = registry.list_all()
        assert len(tools) == 2

    def test_get_claude_specs(self, registry):
        """Claude API 스펙 변환."""
        registry.register(DummyTool())
        specs = registry.get_claude_specs()
        assert len(specs) == 1
        assert specs[0]["name"] == "dummy_tool"
        assert "input_schema" in specs[0]

    def test_search(self, registry):
        """검색."""
        registry.register(DummyTool())
        registry.register(AnotherTool())
        results = registry.search("dummy")
        assert len(results) == 1
        results = registry.search("analysis")
        assert len(results) == 1

    def test_search_case_insensitive(self, registry):
        """대소문자 무시 검색."""
        registry.register(DummyTool())
        results = registry.search("DUMMY")
        assert len(results) == 1

    def test_len(self, registry):
        """길이."""
        assert len(registry) == 0
        registry.register(DummyTool())
        assert len(registry) == 1

    def test_contains(self, registry):
        """포함 여부."""
        registry.register(DummyTool())
        assert "dummy_tool" in registry
        assert "nonexistent" not in registry


class TestBaseTool:
    """BaseTool 테스트."""

    def test_validate_success(self):
        """파라미터 검증 성공."""
        tool = DummyTool()
        is_valid, error = tool.validate(query="test")
        assert is_valid is True
        assert error is None

    def test_validate_missing_required(self):
        """필수 파라미터 누락."""
        tool = DummyTool()
        is_valid, error = tool.validate()
        assert is_valid is False
        assert "query" in error

    def test_validate_invalid_enum(self):
        """잘못된 enum 값."""
        tool = DummyTool()
        is_valid, error = tool.validate(query="test", sort="invalid")
        assert is_valid is False
        assert "유효하지 않은 값" in error

    def test_validate_valid_enum(self):
        """올바른 enum 값."""
        tool = DummyTool()
        is_valid, error = tool.validate(query="test", sort="asc")
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_execute(self):
        """Tool 실행."""
        tool = DummyTool()
        result = await tool.execute(query="Python")
        assert result.success is True
        assert "Python" in result.data

    def test_to_claude_spec(self):
        """Claude API 스펙 변환."""
        tool = DummyTool()
        spec = tool.to_claude_spec()
        assert spec["name"] == "dummy_tool"
        assert spec["description"] == "테스트용 도구입니다"
        assert "query" in spec["input_schema"]["properties"]
        assert "query" in spec["input_schema"]["required"]
        # optional param은 required에 없음
        assert "limit" not in spec["input_schema"]["required"]

    def test_to_claude_spec_enum(self):
        """Claude API 스펙에 enum 포함."""
        tool = DummyTool()
        spec = tool.to_claude_spec()
        sort_prop = spec["input_schema"]["properties"]["sort"]
        assert sort_prop["enum"] == ["asc", "desc"]


class TestToolResult:
    """ToolResult 테스트."""

    def test_success_result(self):
        """성공 결과."""
        result = ToolResult(success=True, data="데이터")
        assert result.success is True
        assert result.data == "데이터"
        assert result.error is None

    def test_error_result(self):
        """에러 결과."""
        result = ToolResult(success=False, error="실패 사유")
        assert result.success is False
        assert result.error == "실패 사유"

    def test_metadata(self):
        """메타데이터."""
        result = ToolResult(success=True, data="ok", metadata={"key": "value"})
        assert result.metadata["key"] == "value"

    def test_default_metadata(self):
        """기본 메타데이터."""
        result = ToolResult(success=True)
        assert result.metadata == {}
