"""Base Tool Interface - 모든 Tool이 따라야 하는 표준 규격."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class ToolCategory(Enum):
    """Tool 카테고리 분류."""

    FINANCE = "finance"          # 주식, 코인, 환율
    NEWS = "news"                # 뉴스, 트렌드
    DEV = "dev"                  # GitHub, Figma, 코드
    NOTIFICATION = "notification"  # Discord, Slack, Email
    PRODUCTIVITY = "productivity"  # 메모, 일정, 리마인더
    SEARCH = "search"            # 웹 검색, 문서 검색
    ANALYSIS = "analysis"        # 데이터 분석, 요약


@dataclass
class ToolParameter:
    """Tool 파라미터 정의."""

    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    enum: Optional[list[str]] = None
    default: Any = None


@dataclass
class ToolResult:
    """Tool 실행 결과."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    """모든 Tool의 기본 인터페이스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool 고유 이름 (예: 'get_crypto_price')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 설명 - Claude가 언제 이 Tool을 쓸지 판단하는 데 사용."""
        pass

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool 카테고리."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """Tool 입력 파라미터 목록."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Tool 실행."""
        pass

    def validate(self, **kwargs) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사."""
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"필수 파라미터 누락: {param.name}"

            if param.enum and param.name in kwargs:
                if kwargs[param.name] not in param.enum:
                    return False, f"유효하지 않은 값: {param.name}={kwargs[param.name]}"

        return True, None

    def to_claude_spec(self) -> dict:
        """Claude API Tool 스펙으로 변환."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        }
