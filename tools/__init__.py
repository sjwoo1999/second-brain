"""Tools 모듈 - 모든 Tool들을 여기서 등록."""

from core.registry import registry

# Tool들을 import하면 자동으로 registry에 등록됨
# from .news import *
# from .finance import *
# from .dev import *


def register_all_tools():
    """모든 Tool을 등록하는 함수."""
    # 나중에 Tool 추가할 때마다 여기에 import 추가
    pass


def get_registered_tools():
    """등록된 모든 Tool 목록 반환."""
    return registry.list_all()
