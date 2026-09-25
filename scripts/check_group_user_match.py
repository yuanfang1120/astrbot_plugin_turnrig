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
        """
        返回一个占位类

        Args:
            name: 被访问的属性名

        Returns:
            一个空的占位类，够当类型注解用
        """
        return type(name, (), {})


def _install_astrbot_stubs():
    """
    把 astrbot 相关模块替换成占位实现

    Note:
        这样插件模块才能在没有安装 AstrBot 的环境里被导入，
        仅用于自检，不会影响插件本身的运行 ⚠️
    """
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
    """假的 MessageType，只需要 .name 属性"""

    name = "GROUP_MESSAGE"


class _FakeEvent:
    """只提供 _should_monitor_group_user 用到的四个访问点"""

    def __init__(self, group_id="123456789", sender_id="987654321", prefix="qq"):
        """
        构造一个模拟的群消息事件

        Args:
            group_id: 群号
            sender_id: 发送者 QQ 号
            prefix: 会话 ID 的平台前缀（真实 UMO 用的是平台实例名，如 qq）
        """
        self._group_id = group_id
        self._sender_id = sender_id
        self.unified_msg_origin = f"{prefix}:GroupMessage:{group_id}"

    def get_message_type(self):
        """
        获取消息类型

        Returns:
            假的 MessageType，其 name 为 GROUP_MESSAGE
        """
        return _FakeMessageType()

    def get_group_id(self):
        """
        获取群号

        Returns:
            当前模拟的群号
        """
        return self._group_id

    def get_sender_id(self):
        """
        获取发送者 QQ 号

        Returns:
            当前模拟的发送者 QQ 号
        """
        return self._sender_id


def main():
    """
    跑一遍应当命中与不应当命中的用例

    Note:
        全部符合预期时会打印"全部通过"，任一用例不符则直接断言失败 ❌
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    _install_astrbot_stubs()

    from messaging.message_listener import MessageListener

    listener = MessageListener.__new__(MessageListener)  # 跳过 __init__ 的插件依赖
    event = _FakeEvent()

    should_match = {
        "纯群号（修复后命令写入的格式）": {"123456789": ["987654321"]},
        "写死 aiocqhttp 前缀（历史错误数据）": {
            "aiocqhttp:GroupMessage:123456789": ["987654321"]
        },
        "真实 UMO 前缀 qq": {"qq:GroupMessage:123456789": ["987654321"]},
    }
    should_not_match = {
        "别的群": {"123456790": ["987654321"]},
        "别的用户": {"123456789": ["987654322"]},
        "没有任何配置": {},
        "群号只是别的群号的后缀片段": {
            "aiocqhttp:GroupMessage:1123456789": ["987654321"]
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

    print("\n全部通过，群内指定用户的 key 匹配与平台前缀无关")


if __name__ == "__main__":
    main()
