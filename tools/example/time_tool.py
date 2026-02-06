"""예시 Tool - 현재 시간 조회."""

from datetime import datetime
import sys
import os

# 상위 디렉토리를 path에 추가 (개발 중 임시)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.base_tool import BaseTool, ToolCategory, ToolParameter, ToolResult
from core.registry import registry


class CurrentTimeTool(BaseTool):
    """현재 시간을 알려주는 Tool."""

    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "현재 날짜와 시간을 알려줍니다. 오늘이 며칠인지, 지금 몇 시인지 물어볼 때 사용합니다."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PRODUCTIVITY

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="timezone",
                type="string",
                description="시간대 (기본값: Asia/Seoul)",
                required=False,
                default="Asia/Seoul"
            ),
            ToolParameter(
                name="format",
                type="string",
                description="출력 형식",
                required=False,
                enum=["full", "date", "time"],
                default="full"
            )
        ]

    async def execute(self, timezone: str = "Asia/Seoul", format: str = "full") -> ToolResult:
        try:
            now = datetime.now()

            if format == "date":
                result = now.strftime("%Y년 %m월 %d일 %A")
            elif format == "time":
                result = now.strftime("%H시 %M분 %S초")
            else:  # full
                result = now.strftime("%Y년 %m월 %d일 %A %H시 %M분")

            return ToolResult(
                success=True,
                data=result,
                metadata={"timezone": timezone, "format": format}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Tool 등록
registry.register(CurrentTimeTool())
