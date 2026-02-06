"""Tool Registry - Tool 등록 및 관리."""

from typing import Optional
from .base_tool import BaseTool, ToolCategory


class ToolRegistry:
    """Tool 저장소 - 모든 Tool을 등록하고 관리."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Tool 등록."""
        if tool.name in self._tools:
            raise ValueError(f"이미 등록된 Tool: {tool.name}")

        self._tools[tool.name] = tool
        print(f"[Registry] Tool 등록: {tool.name} ({tool.category.value})")

    def unregister(self, name: str) -> bool:
        """Tool 등록 해제."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:
        """이름으로 Tool 조회."""
        return self._tools.get(name)

    def get_by_category(self, category: ToolCategory) -> list[BaseTool]:
        """카테고리로 Tool 조회."""
        return [
            tool for tool in self._tools.values()
            if tool.category == category
        ]

    def list_all(self) -> list[BaseTool]:
        """모든 Tool 목록."""
        return list(self._tools.values())

    def get_claude_specs(self) -> list[dict]:
        """모든 Tool을 Claude API 스펙으로 변환."""
        return [tool.to_claude_spec() for tool in self._tools.values()]

    def search(self, query: str) -> list[BaseTool]:
        """이름 또는 설명에서 검색."""
        query_lower = query.lower()
        return [
            tool for tool in self._tools.values()
            if query_lower in tool.name.lower()
            or query_lower in tool.description.lower()
        ]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# 전역 레지스트리 인스턴스
registry = ToolRegistry()
