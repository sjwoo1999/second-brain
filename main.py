"""Second Brain - 메인 진입점."""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from core import Orchestrator, registry
from config import settings


def load_tools():
    """Tool들을 로드."""
    # 예시 Tool
    from tools.example import time_tool  # noqa: F401

    # 나중에 추가할 Tool들
    # from tools.news import world_news  # noqa: F401
    # from tools.finance import crypto  # noqa: F401

    print(f"\n[Second Brain] {len(registry)}개 Tool 로드됨")
    for tool in registry.list_all():
        print(f"  - {tool.name}: {tool.description[:50]}...")


async def interactive_cli():
    """대화형 CLI 인터페이스."""
    print("\n" + "=" * 60)
    print("🧠 Second Brain - Interactive Mode")
    print("=" * 60)
    print("명령어: 'quit' 종료 | 'clear' 대화 초기화 | 'tools' Tool 목록")
    print("=" * 60 + "\n")

    # 설정 검증
    is_valid, errors = settings.validate()
    if not is_valid:
        print("⚠️  설정 오류:")
        for error in errors:
            print(f"   - {error}")
        print("\n.env 파일을 확인해주세요.")
        return

    # Orchestrator 초기화
    orchestrator = Orchestrator()

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("\n👋 종료합니다.")
                break

            if user_input.lower() == "clear":
                orchestrator.clear_history()
                print("🔄 대화 기록이 초기화되었습니다.")
                continue

            if user_input.lower() == "tools":
                print("\n📦 등록된 Tools:")
                for tool in registry.list_all():
                    print(f"  [{tool.category.value}] {tool.name}")
                    print(f"      {tool.description}")
                continue

            # 메시지 처리
            print("\n🤖 Assistant: ", end="", flush=True)
            response = await orchestrator.process(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\n\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")


def main():
    """메인 함수."""
    print("\n🧠 Second Brain 시작...")

    # Tool 로드
    load_tools()

    # CLI 실행
    asyncio.run(interactive_cli())


if __name__ == "__main__":
    main()
