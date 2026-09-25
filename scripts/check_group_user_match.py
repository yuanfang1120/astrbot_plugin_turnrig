"""群内指定用户匹配逻辑自检喵～ 🎯

背景：UMO 的平台前缀是运行时的平台实例名（如 qq），而 normalize_session_id
     写死了 "aiocqhttp"，导致 /turnrig adduser 写进 monitored_users_in_groups
     的记录永远匹配不到。本脚本验证 key 匹配已与平台前缀无关。

运行（插件根目录）:
    python scripts/check_group_user_match.py
"""

import logging
import sys
import types
from pathlib import Path


class _StubModule(types.ModuleType):
    """任意属性都返回占位类，够插件模块在没有 AstrBot 的环境下被导入"""

    def __getattr__(self, name):
        return type(name, (), {})


def _install_astrbot_stubs():
    for name in (
        "astrbot",
        "astrbot.api",
        "astrbot.api.event",
        "astrbot.api.message_components",
    ):
        module = _StubModule(name)
        module.__path__ = []
        sys.modules[name] = module

    api = sys.modules["astrbot.api"]
    sys.modules["astrbot"].api = api
    api.event = sys.modules["astrbot.api.event"]
    api.message_components = sys.modules["astrbot.api.message_components"]
    api.logger = logging.getLogger("astrbot-stub")


class _FakeMessageType:
    name = "GROUP_MESSAGE"


class _FakeEvent:
    """只提供 _should_monitor_group_user 用到的四个访问点"""

    def __init__(self, group_id="996221889", sender_id="1957780271", prefix="qq"):
        self._group_id = group_id
        self._sender_id = sender_id
        self.unified_msg_origin = f"{prefix}:GroupMessage:{group_id}"

    def get_message_type(self):
        return _FakeMessageType()

    def get_group_id(self):
        return self._group_id

    def get_sender_id(self):
        return self._sender_id


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    _install_astrbot_stubs()

    from messaging.message_listener import MessageListener

    listener = MessageListener.__new__(MessageListener)  # 跳过 __init__ 的插件依赖
    event = _FakeEvent()

    should_match = {
        "纯群号（修复后命令写入的格式）": {"996221889": ["1957780271"]},
        "写死 aiocqhttp 前缀（历史错误数据）": {
            "aiocqhttp:GroupMessage:996221889": ["1957780271"]
        },
        "真实 UMO 前缀 qq": {"qq:GroupMessage:996221889": ["1957780271"]},
    }
    should_not_match = {
        "别的群": {"996221890": ["1957780271"]},
        "别的用户": {"996221889": ["1957780272"]},
        "没有任何配置": {},
        "群号只是别的群号的后缀片段": {
            "aiocqhttp:GroupMessage:1996221889": ["1957780271"]
        },
    }

    for label, mapping in should_match.items():
        task = {"monitored_users_in_groups": mapping}
        assert listener._should_monitor_group_user(task, event) is True, (
            f"应命中却没有命中: {label}"
        )
        print(f"[OK] 命中   {label}")

    for label, mapping in should_not_match.items():
        task = {"monitored_users_in_groups": mapping}
        assert listener._should_monitor_group_user(task, event) is False, (
            f"不应命中却命中了: {label}"
        )
        print(f"[OK] 不命中 {label}")

    print("\n全部通过 ✅  群内指定用户的 key 匹配与平台前缀无关")


if __name__ == "__main__":
    main()
