import asyncio
import os
import time

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.star import Context, Star, register

from .commands.command_handlers import CommandHandlers

# 导入解耦后的模块喵～ 📦
from .config.config_manager import ConfigManager
from .messaging.forward_manager import ForwardManager
from .messaging.message_listener import MessageListener


@register(
    "astrbot_plugin_turnrig",
    "yuanfang1120",
    "监听指定会话的消息并转发到 QQ 或其他平台，支持群内指定用户精准监听",
    "1.6.6",
    "https://github.com/yuanfang1120/astrbot_plugin_turnrig",
)
class TurnRigPlugin(Star):
    """
    TurnRig消息转发插件喵～ 🚀
    这是一个超级可爱的消息转发小助手！ ฅ(^•ω•^ฅ

    功能特色：
    - 📨 智能消息监听和转发
    - 🎯 多任务管理系统
    - 💾 持久化配置和缓存
    - 🔄 自动重试机制
    - ✨ 支持各种媒体类型

    Note:
        所有的消息都会被精心处理，确保完整转发喵！ 💫
    """

    def __init__(self, context: Context, config=None):
        """
        初始化转发插件喵～ 🐾
        创建一个全新的消息转发小助手！

        Args:
            context: AstrBot上下文对象喵
            config: 配置数据（可选）喵
        """
        super().__init__(context)

        # 数据存储路径 - 修改为正确的持久化数据存储路径喵～ 📁
        self.data_dir = os.path.join("data", "plugins_data", "astrbot_plugin_turnrig")
        os.makedirs(self.data_dir, exist_ok=True)

        # 创建临时目录用于存储图片喵～ 🖼️
        self.temp_dir = os.path.join(self.data_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)

        # 确保下载助手可以访问临时目录喵～ 📥
        from .messaging.forward.download_helper import DownloadHelper

        self.download_helper = DownloadHelper(self.temp_dir)
        self.download_helper.plugin = self  # 添加对插件的引用，用于访问配置喵 🔗

        # 创建配置管理器喵～ ⚙️
        self.config_manager = ConfigManager(self.data_dir)

        # 从配置文件加载或使用默认配置喵～ 📋
        self.config = self.config_manager.load_config() or {
            "tasks": [],
            "default_max_messages": 20,
            "bot_self_ids": [],  # 机器人ID列表，用于防止循环发送喵～ 🤖
        }

        # 如果收到了 AstrBot 的配置，且当前配置为空，才使用 AstrBot 配置喵～ 🔄
        if config and not self.config:
            # 尝试将旧格式配置转换为新格式喵～ 🔧
            if isinstance(config, dict) and not config.get("tasks"):
                default_task = {
                    "id": "1",  # 使用"1"作为第一个任务的ID喵 🆔
                    "name": "默认任务",
                    "monitor_groups": config.get("monitor_groups", []),
                    "monitor_private_users": config.get("monitor_private_users", []),
                    "monitored_users_in_groups": config.get(
                        "monitored_users_in_groups", {}
                    ),
                    "target_sessions": config.get("target_sessions", []),
                    "max_messages": config.get("max_messages", 20),
                    "enabled": True,
                }
                self.config = {"tasks": [default_task], "default_max_messages": 20}
            else:
                self.config = config

        # 确保配置有tasks字段喵～ 📝
        if "tasks" not in self.config:
            self.config["tasks"] = []

        # 确保配置有default_max_messages字段喵～ 🔢
        if "default_max_messages" not in self.config:
            self.config["default_max_messages"] = 20

        # 确保配置有bot_self_ids字段喵～ 🤖
        if "bot_self_ids" not in self.config:
            self.config["bot_self_ids"] = []

        # 确保可配置的单条发送开关存在，默认关闭
        if "send_single_messages" not in self.config:
            self.config["send_single_messages"] = False

        # 如果 AstrBot 通过 __init__ 传入了配置，则覆盖本地对应开关
        try:
            if config and isinstance(config, dict) and "send_single_messages" in config:
                self.config["send_single_messages"] = bool(
                    config.get("send_single_messages", False)
                )
        except Exception:
            pass

        # 如果没有任何任务，创建一个自动捕获所有消息的测试任务喵～ 🧪
        if not self.config["tasks"]:
            logger.info("没有找到任何转发任务，创建一个测试任务喵～ 🆕")
            test_task = {
                "id": "test",
                "name": "测试任务",
                "monitor_groups": [],  # 这里留空以便后续手动添加喵 📋
                "monitor_private_users": [],
                "monitored_users_in_groups": {},
                "target_sessions": [],  # 这里留空以便后续手动添加喵 🎯
                "max_messages": 20,
                "enabled": True,
                "monitor_sessions": [],  # 新增字段，用于直接匹配session_id喵 🔍
            }
            self.config["tasks"].append(test_task)
            self.save_config_file()

        # 消息缓存喵～ 💾
        self.message_cache = self.config_manager.load_message_cache() or {}

        # 清理缓存中的无效任务喵～ 🧹
        self._cleanup_invalid_tasks_in_cache()

        # 保存一次配置确保文件存在喵～ 💾
        self.save_config_file()
        logger.info(
            f"转发侦听器插件初始化完成，数据存储在 {self.data_dir} 目录下喵～ ✅"
        )
        logger.info(f"已加载 {len(self.config.get('tasks', []))} 个转发任务喵～ 📊")

        # 打印所有任务的详细信息，便于调试喵～ 🔍
        for task in self.config.get("tasks", []):
            logger.info(
                f"任务ID: {task.get('id')}, 名称: {task.get('name')}, 启用状态: {task.get('enabled')} 喵～ 📋"
            )
            logger.info(f"  监听群组: {task.get('monitor_groups', [])} 喵～ 👥")
            logger.info(f"  监听私聊: {task.get('monitor_private_users', [])} 喵～ 💬")
            logger.info(
                f"  群内特定用户: {task.get('monitored_users_in_groups', {})} 喵～ 👤"
            )
            logger.info(f"  转发目标: {task.get('target_sessions', [])} 喵～ 🎯")

        # 创建模块实例喵～ 🏗️
        self.forward_manager = ForwardManager(self)
        self.message_listener = MessageListener(self)
        self.command_handlers = CommandHandlers(self)

        # 启动定期保存任务喵～ ⏰
        asyncio.create_task(self.periodic_save())

        # 添加一个新的循环监听任务喵～ 🔄
        asyncio.create_task(self.message_monitor_loop())

        # 添加消息ID清理任务喵～ 🧹
        self.cleanup_task = None
        self.start_cleanup_task()

        # 添加清理临时文件任务喵～ 📁
        asyncio.create_task(self.cleanup_temp_files())

    def _cleanup_invalid_tasks_in_cache(self):
        """
        清理缓存中不存在的任务喵～ 🧹
        把那些已经被删除的任务从缓存中移除！

        Note:
            这样可以保持缓存的整洁，避免占用多余空间喵～ ✨
        """
        valid_task_ids = {
            str(task.get("id", "")) for task in self.config.get("tasks", [])
        }
        invalid_tasks = []

        # 检查消息缓存中的任务喵～ 🔍
        for task_id in list(self.message_cache.keys()):
            if str(task_id) not in valid_task_ids:
                invalid_tasks.append(task_id)
                del self.message_cache[task_id]

        if invalid_tasks:
            logger.info(
                f"已清理 {len(invalid_tasks)} 个无效任务的缓存喵: {', '.join(invalid_tasks)} 🗑️"
            )
            self.save_message_cache()

    def save_config_file(self):
        """
        将配置保存到文件喵～ 💾
        把所有的设置都安全地存储起来！
        """
        self.config_manager.save_config(self.config)

    def save_message_cache(self):
        """
        保存消息缓存喵～ 💾
        把缓存的消息都安全地保存到文件里！

        Note:
            现在会传递当前配置，避免任务被意外删除喵～ 🔧
        """
        # 传递当前配置给config_manager，避免从文件重新加载导致的任务丢失喵～ ✨
        self.config_manager.save_message_cache(self.message_cache, self.config)

    async def periodic_save(self):
        """
        定期保存数据喵～ ⏰
        每5分钟自动保存一次，确保数据不丢失！

        Note:
            这是一个后台任务，会一直运行喵～ 🔄
        """
        while True:
            await asyncio.sleep(300)  # 每5分钟保存一次喵～ 😴
            self.save_message_cache()
            self.save_config_file()  # 也保存配置喵～ ⚙️
            logger.debug("已完成定期保存喵～ ✅")

    async def message_monitor_loop(self):
        """
        定期检查消息监听状态喵～ 🔍
        监控长时间未活跃的会话，但不主动获取历史消息！

        Note:
            这个任务会帮助清理过期的会话状态喵～ 🧹
        """
        while True:
            try:
                # 检查长时间未活跃会话喵～ 📊
                for task_id, sessions in self.message_cache.items():
                    for session_id, messages in sessions.items():
                        if not messages:
                            logger.debug(
                                f"跳过空缓存会话 {session_id} 在任务 {task_id} 中"
                            )
                            continue

                        # 简单使用最后一条消息的时间戳喵～
                        last_message_timestamp = messages[-1].get("timestamp", 0)

                        # 检查是否真的超过1小时未活动喵～ ⏰
                        if (
                            last_message_timestamp > 0
                            and time.time() - last_message_timestamp > 3600
                        ):
                            logger.debug(
                                f"会话 {session_id} 在任务 {task_id} 中超过1小时未活动"
                            )

                # 移除主动获取历史消息的功能
                # 只依赖消息监听器来记录新消息

            except Exception as e:
                logger.error(f"消息监听循环错误: {e}")

            await asyncio.sleep(
                60
            )  # 每60秒检查一次，因为不再主动获取消息，可以降低频率

    async def _fetch_latest_messages(self, platform, msg_type, chat_id):
        """
        获取最新消息喵～ 📥
        （暂时保留但不实现，避免过度请求API）

        Args:
            platform: 平台对象喵
            msg_type: 消息类型喵
            chat_id: 聊天ID喵

        Note:
            为了避免频繁API调用，这个功能暂时不实现喵～ ⚠️
        """
        return []

    async def _process_fetched_messages(self, task_id, session_id, messages):
        """
        处理获取到的消息喵～ 🔄
        （暂时保留但不实现）

        Args:
            task_id: 任务ID喵
            session_id: 会话ID喵
            messages: 消息列表喵
        """
        pass

    def get_task_by_id(self, task_id):
        """
        根据ID获取任务喵～ 🔍
        找到指定ID的任务配置！

        Args:
            task_id: 任务ID喵

        Returns:
            找到的任务字典，如果不存在则返回None喵
        """
        for task in self.config.get("tasks", []):
            if str(task.get("id")) == str(task_id):
                return task
        return None

    def get_all_enabled_tasks(self):
        """
        获取所有启用的任务喵～ ✅
        返回当前启用状态的所有任务！

        Returns:
            已启用的任务列表喵～
        """
        return [
            task for task in self.config.get("tasks", []) if task.get("enabled", True)
        ]

    def get_max_task_id(self):
        """
        获取最大的任务ID喵～ 🔢
        用于自动生成新的任务ID！

        Returns:
            当前最大的任务ID（整数）喵

        Note:
            如果没有任务，返回0喵～ 🆕
        """
        max_id = 0
        for task in self.config.get("tasks", []):
            try:
                task_id = int(task.get("id", 0))
                if task_id > max_id:
                    max_id = task_id
            except (ValueError, TypeError):
                # 如果任务ID不是数字，跳过喵～ ⏭️
                continue
        return max_id

    def start_cleanup_task(self):
        """
        启动消息ID清理任务喵～ 🧹
        定期清理过期的消息ID记录！

        Note:
            避免重复启动任务喵～ ⚠️
        """
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self.periodic_message_ids_cleanup())

    async def periodic_message_ids_cleanup(self):
        """
        定期清理过期的消息ID记录喵～ ⏰
        每小时自动清理一次过期记录！

        Note:
            这是一个后台任务，会一直运行喵～ 🔄
        """
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次喵～ 😴
                cleaned_count = self.cleanup_expired_message_ids()
                if cleaned_count > 0:
                    logger.info(f"定期清理了 {cleaned_count} 个过期消息ID记录喵～ 🗑️")
            except Exception as e:
                logger.error(f"定期清理消息ID失败喵: {e} 😿")

    def cleanup_expired_message_ids(self, days: int = 7) -> int:
        """
        清理指定天数前的消息ID记录喵～ 🧹
        删除过期的消息处理记录，释放内存！

        Args:
            days: 保留天数，默认7天喵

        Returns:
            清理的记录数量喵

        Note:
            只清理真正过期的记录，保证功能正常喵～ ✨
        """
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 3600)  # days天前的时间戳喵
        cleaned_count = 0

        # 清理所有任务的过期消息ID记录喵～ 🔍
        for key in list(self.config.keys()):
            if key.startswith("processed_message_ids_"):
                processed_ids = self.config[key]
                if isinstance(processed_ids, list):
                    original_count = len(processed_ids)
                    # 过滤出未过期的记录喵～ 📋
                    self.config[key] = [
                        item
                        for item in processed_ids
                        if isinstance(item, dict)
                        and item.get("timestamp", 0) > cutoff_time
                    ]
                    removed_count = original_count - len(self.config[key])
                    cleaned_count += removed_count

                    if removed_count > 0:
                        task_id = key.replace("processed_message_ids_", "")
                        logger.info(
                            f"任务 {task_id} 清理了 {removed_count} 个过期消息ID记录喵～ 🗑️"
                        )

        # 如果清理了记录，保存配置喵～ 💾
        if cleaned_count > 0:
            self.save_config_file()
            logger.info(f"总共清理了 {cleaned_count} 个过期消息ID记录喵～ ✅")

        return cleaned_count

    async def cleanup_temp_files(self):
        """
        定期清理临时文件喵～ 📁
        每小时清理一次超过2小时的临时文件！

        Note:
            只清理真正过期的文件，避免影响正在使用的文件喵～ ⚠️
        """
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次喵～ 😴
                current_time = time.time()
                cleaned_count = 0

                # 遍历临时目录喵～ 🔍
                if os.path.exists(self.temp_dir):
                    for filename in os.listdir(self.temp_dir):
                        file_path = os.path.join(self.temp_dir, filename)
                        try:
                            # 检查文件修改时间喵～ ⏰
                            if os.path.isfile(file_path):
                                file_mtime = os.path.getmtime(file_path)
                                # 删除超过2小时的文件喵～ 🗑️
                                if current_time - file_mtime > 7200:  # 2小时 = 7200秒
                                    os.remove(file_path)
                                    cleaned_count += 1
                                    logger.debug(f"清理临时文件喵: {filename} 🗂️")
                        except Exception as e:
                            logger.warning(f"清理临时文件 {filename} 失败喵: {e} 😿")

                if cleaned_count > 0:
                    logger.info(f"清理了 {cleaned_count} 个临时文件喵～ 🧹")

            except Exception as e:
                logger.error(f"清理临时文件任务失败喵: {e} 😿")

    async def terminate(self):
        """
        插件终止时的清理操作喵～ 🔚
        确保所有数据都被安全保存！

        Note:
            这是插件关闭前的最后一次保存机会喵～ 💾
        """
        try:
            # 保存所有数据喵～ 💾
            self.save_message_cache()
            self.save_config_file()

            # 保存失败消息缓存喵～ 🔄
            if hasattr(self, "forward_manager") and self.forward_manager:
                self.forward_manager.save_failed_messages_cache()

            # 取消清理任务喵～ ❌
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()

            logger.info("转发插件已安全关闭，所有数据已保存喵～ ✅")

        except Exception as e:
            logger.error(f"插件关闭时出错喵: {e} 😿")

    # === 消息处理相关方法喵～ 📨 ===

    @filter.event_message_type(filter.EventMessageType.ALL)
    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    async def on_all_message(self, event: AstrMessageEvent):
        """
        监听所有消息的入口喵～ 👂
        这里是消息处理的第一站！

        Args:
            event: 消息事件对象喵

        Note:
            会过滤掉插件自己的指令消息喵～ 🔍
        """
        try:
            # 获取消息内容喵～ 📝
            message_str = event.message_str

            # 如果是插件指令，不进行转发处理喵～ ⚠️
            if message_str:
                # 检查是否为转发相关的指令喵～ 🔍
                if (
                    message_str.startswith("/turnrig")
                    or message_str.startswith("/tr ")
                    or message_str == "/tr"
                    or message_str.startswith("/fn")  # 转发指令
                ):
                    logger.debug(f"跳过插件指令消息喵: {message_str} ⏭️")
                    return

                # 检查是否为机器人的回复消息（避免循环）喵～ 🤖
                sender_id = event.get_sender_id()
                if sender_id == str(
                    self.context.get_platform("aiocqhttp").get_client().self_id
                ):
                    logger.debug("跳过机器人自己的消息喵～ 🤖")
                    return

            # 委托给消息监听器处理喵～ 📨
            await self.message_listener.on_all_message(event)

        except Exception as e:
            logger.error(f"处理消息时出错喵: {e} 😿")
            import traceback

            logger.error(traceback.format_exc())

    @filter.event_message_type(filter.EventMessageType.ALL)
    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    async def on_group_notice(self, event):
        """
        监听群组通知消息喵～ 📢
        处理群文件上传等特殊事件！

        Args:
            event: 通知事件对象喵

        Note:
            主要处理群文件上传通知喵～ 📁
        """
        try:
            # 检查是否为群文件上传通知喵～ 📁
            if hasattr(event, "notice_type") and event.notice_type == "group_upload":
                logger.info("检测到群文件上传通知，委托给监听器处理喵～ 📂")
                await self.message_listener.on_group_upload_notice(event)
            else:
                logger.debug(
                    f"忽略其他类型的通知消息喵: {getattr(event, 'notice_type', 'unknown')} ⏭️"
                )

        except Exception as e:
            logger.error(f"处理群组通知失败喵: {e} 😿")

    # === 命令处理相关方法喵～ 🔧 ===

    @filter.command_group("turnrig")
    async def turnrig(self, event: AstrMessageEvent):
        """
        TurnRig命令组的入口喵～ 🚪
        处理所有以 /turnrig 开头的命令！
        """
        return MessageEventResult().message(
            "请指定具体的子命令喵～ 使用 /turnrig help 查看帮助 📖"
        )

    @turnrig.command("list")
    async def list_tasks(self, event: AstrMessageEvent):
        """列出所有任务喵～ 📋"""
        return await self.command_handlers.handle_list_tasks(event)

    @turnrig.command("status")
    async def status(self, event: AstrMessageEvent, task_id: str = None):
        """查看任务状态喵～ 📊"""
        return await self.command_handlers.handle_status(event, task_id)

    @turnrig.command("create")
    async def create_task(self, event: AstrMessageEvent, task_name: str = None):
        """创建新任务喵～ ✨"""
        return await self.command_handlers.handle_create_task(event, task_name)

    @turnrig.command("delete")
    async def delete_task(self, event: AstrMessageEvent, task_id: str = None):
        """删除任务喵～ 🗑️"""
        return await self.command_handlers.handle_delete_task(event, task_id)

    @turnrig.command("enable")
    async def enable_task(self, event: AstrMessageEvent, task_id: str = None):
        """启用任务喵～ ✅"""
        return await self.command_handlers.handle_enable_task(event, task_id)

    @turnrig.command("disable")
    async def disable_task(self, event: AstrMessageEvent, task_id: str = None):
        """禁用任务喵～ ❌"""
        return await self.command_handlers.handle_disable_task(event, task_id)

    @turnrig.command("monitor")
    async def add_monitor(
        self, event: AstrMessageEvent, task_id: str = None, session_id: str = None
    ):
        """
        添加监听会话喵～ 👂
        把指定的会话加入监听列表！
        """
        # 委托给命令处理器，传递所有参数喵～ 🔄
        cmd_text = event.message_str
        parts = cmd_text.split() if cmd_text else []
        return await self.command_handlers.handle_add_monitor(
            event, task_id, session_id, *parts[3:]
        )

    @turnrig.command("unmonitor")
    async def remove_monitor(
        self, event: AstrMessageEvent, task_id: str = None, session_id: str = None
    ):
        """
        移除监听会话喵～ 👋
        把指定的会话从监听列表中移除！
        """
        cmd_text = event.message_str
        parts = cmd_text.split() if cmd_text else []
        return await self.command_handlers.handle_remove_monitor(
            event, task_id, session_id, *parts[3:]
        )

    @turnrig.command("target")
    async def add_target(
        self, event: AstrMessageEvent, task_id: str = None, target_session: str = None
    ):
        """
        添加转发目标喵～ 🎯
        指定消息转发的目标会话！
        """
        cmd_text = event.message_str
        parts = cmd_text.split() if cmd_text else []
        return await self.command_handlers.handle_add_target(
            event, task_id, target_session, *parts[3:]
        )

    @turnrig.command("untarget")
    async def remove_target(
        self, event: AstrMessageEvent, task_id: str = None, target_session: str = None
    ):
        """
        移除转发目标喵～ 🚫
        从转发目标列表中移除指定会话！
        """
        cmd_text = event.message_str
        parts = cmd_text.split() if cmd_text else []
        return await self.command_handlers.handle_remove_target(
            event, task_id, target_session, *parts[3:]
        )

    @turnrig.command("threshold")
    async def set_threshold(
        self, event: AstrMessageEvent, task_id: str = None, threshold: int = None
    ):
        """设置消息阈值喵～ 🔢"""
        return await self.command_handlers.handle_set_threshold(
            event, task_id, threshold
        )

    @turnrig.command("rename")
    async def rename_task(
        self, event: AstrMessageEvent, task_id: str = None, new_name: str = None
    ):
        """重命名任务喵～ ✏️"""
        return await self.command_handlers.handle_rename_task(event, task_id, new_name)

    @turnrig.command("forward")
    async def manual_forward(
        self, event: AstrMessageEvent, task_id: str = None, session_id: str = None
    ):
        """
        手动转发消息喵～ 📤
        立即转发指定会话的缓存消息！
        """
        cmd_text = event.message_str
        parts = cmd_text.split() if cmd_text else []
        return await self.command_handlers.handle_manual_forward(
            event, task_id, session_id, *parts[3:]
        )

    @turnrig.command("cleanup")
    async def cleanup_ids(self, event: AstrMessageEvent, days: int = 7):
        """清理过期消息ID喵～ 🧹"""
        return await self.command_handlers.handle_cleanup_ids(event, days)

    @turnrig.command("addbot")
    async def add_bot_id(self, event: AstrMessageEvent, bot_id: str = None):
        """添加机器人ID到过滤列表喵～ 🤖"""
        return await self.command_handlers.handle_add_bot_id(event, bot_id)

    @turnrig.command("removebot")
    async def remove_bot_id(self, event: AstrMessageEvent, bot_id: str = None):
        """从过滤列表移除机器人ID喵～ 🗑️"""
        return await self.command_handlers.handle_remove_bot_id(event, bot_id)

    @turnrig.command("listbots")
    async def list_bot_ids(self, event: AstrMessageEvent):
        """列出所有过滤的机器人ID喵～ 📋"""
        return await self.command_handlers.handle_list_bot_ids(event)

    @turnrig.command("adduser")
    async def add_user_in_group(
        self,
        event: AstrMessageEvent,
        task_id: str = None,
        group_id: str = None,
        user_id: str = None,
    ):
        """
        添加群内特定用户监听喵～ 👤
        监听指定群组中特定用户的消息！
        """
        return await self.command_handlers.handle_add_user_in_group(
            event, task_id, group_id, user_id
        )

    @turnrig.command("removeuser")
    async def remove_user_from_group(
        self,
        event: AstrMessageEvent,
        task_id: str = None,
        group_id: str = None,
        user_id: str = None,
    ):
        """
        移除群内特定用户监听喵～ 👋
        停止监听指定群组中特定用户的消息！
        """
        return await self.command_handlers.handle_remove_user_from_group(
            event, task_id, group_id, user_id
        )

    @turnrig.command("help")
    async def turnrig_help(self, event: AstrMessageEvent):
        """显示帮助信息喵～ 📖"""
        return await self.command_handlers.handle_turnrig_help(event)

    # === 简化命令组喵～ 🔧 ===

    @filter.command_group("tr")
    async def tr(self, event: AstrMessageEvent):
        """
        简化命令组入口喵～ 🚪
        处理所有以 /tr 开头的命令！
        """
        return MessageEventResult().message(
            "请指定具体的子命令喵～ 使用 /tr help 查看帮助 📖"
        )

    @tr.command("add")
    async def tr_add_monitor(self, event: AstrMessageEvent, task_id: str = None):
        """快速添加监听喵～ ➕"""
        return await self.command_handlers.handle_tr_add_monitor(event, task_id)

    @tr.command("remove")
    async def tr_remove_monitor(self, event: AstrMessageEvent, task_id: str = None):
        """快速移除监听喵～ ➖"""
        return await self.command_handlers.handle_tr_remove_monitor(event, task_id)

    @tr.command("target")
    async def tr_add_target(self, event: AstrMessageEvent, task_id: str = None):
        """快速添加目标喵～ 🎯"""
        return await self.command_handlers.handle_tr_add_target(event, task_id)

    @tr.command("untarget")
    async def tr_remove_target(self, event: AstrMessageEvent, task_id: str = None):
        """快速移除目标喵～ 🚫"""
        return await self.command_handlers.handle_tr_remove_target(event, task_id)

    @tr.command("list")
    async def tr_list_tasks(self, event: AstrMessageEvent):
        """快速列出任务喵～ 📋"""
        return await self.command_handlers.handle_tr_list_tasks(event)

    @tr.command("adduser")
    async def tr_add_user_in_group(
        self, event: AstrMessageEvent, task_id: str = None, user_id: str = None
    ):
        """快速添加群内用户监听喵～ 👤"""
        return await self.command_handlers.handle_tr_add_user_in_group(
            event, task_id, user_id
        )

    @tr.command("removeuser")
    async def tr_remove_user_from_group(
        self, event: AstrMessageEvent, task_id: str = None, user_id: str = None
    ):
        """快速移除群内用户监听喵～ 👋"""
        return await self.command_handlers.handle_tr_remove_user_from_group(
            event, task_id, user_id
        )

    @tr.command("help")
    async def tr_help(self, event: AstrMessageEvent):
        """显示简化命令帮助喵～ 📖"""
        return await self.command_handlers.handle_tr_help(event)
