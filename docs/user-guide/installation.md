# 📦 安装指南

本页介绍如何安装并让 TurnRig 跑起来。

## 🎯 前提条件

- 已安装并配置好 **AstrBot**（建议 v4.x）
- 已有一个可用的 **QQ 机器人账号**（推荐 NapCat，其次 Lagrange）
- 如果要转发到其他平台（如微信），需要先在 AstrBot 里配置好对应的平台适配器

## 🚀 安装

### 方法一：WebUI 上传安装（推荐）

1. 打开 AstrBot 的 WebUI，进入「插件管理」
2. 上传本仓库 Release 里的 `astrbot_plugin_turnrig.zip`
3. 等待提示安装成功后，**重载插件**

### 方法二：手动放置

```bash
# 进入 AstrBot 的插件目录
cd AstrBot/data/plugins

# 下载或 clone 本仓库，确保目录名是 astrbot_plugin_turnrig
git clone https://github.com/yuanfang1120/astrbot_plugin_turnrig.git astrbot_plugin_turnrig
```

然后重启 AstrBot。

> 插件本体只用 AstrBot 自身与 Python 标准库，另有 `requests`（下载媒体文件）和 `Pillow`（GIF 转静态图）
> 两个第三方依赖，已列在 `requirements.txt` 中。通过 WebUI 安装时 AstrBot 会自动处理依赖；
> 手动放置安装的话，如果日志报 `ModuleNotFoundError`，在 AstrBot 环境里执行 `pip install -r requirements.txt` 即可。

## ⚙️ 初始配置

### 1. 启用插件

重载/重启后，在 WebUI「插件管理」里确认 TurnRig 状态为「运行中」，日志里会出现：

```
[INFO] [turnrig] 转发侦听器插件初始化完成，数据存储在 ... 目录下喵～ ✅
[INFO] [turnrig] 已加载 N 个转发任务喵～ 📊
```

### 2. 用指令配置任务（推荐）

插件首次启动会创建一个空的「测试任务」占位。推荐直接用指令配出自己的任务：

```
# 创建任务，记下返回的任务 ID（假设是 1）
/turnrig create 我的转发任务

# 添加监听源：群内指定用户（在目标群里执行简化版更方便）
/tr adduser 1 <被监听的QQ号>
#   或完整版：/turnrig adduser 1 <群号> <被监听的QQ号>

# 设置转发目标（在目标会话里发 /tr target 1 会自动取真实会话ID）
/turnrig target 1 私聊 <你的QQ号>

# 阈值设为 1，来一条转一条
/turnrig threshold 1 1
```

配置完用 `/turnrig list` 检查，各项都符合预期即可。

### 3. （可选）直接编辑配置文件

配置文件位置：

```
AstrBot/data/plugins_data/astrbot_plugin_turnrig/config.json
```

结构如下：

```json
{
  "tasks": [
    {
      "id": "1",
      "name": "我的转发任务",
      "monitor_groups": [],
      "monitor_private_users": [],
      "monitored_users_in_groups": { "996221889": ["1957780271"] },
      "target_sessions": ["qq:FriendMessage:你的QQ号"],
      "max_messages": 1,
      "enabled": true
    }
  ],
  "default_max_messages": 20,
  "bot_self_ids": [],
  "send_single_messages": false
}
```

字段含义：

| 字段 | 说明 |
| :--- | :--- |
| `monitor_groups` | 整群监听，填群号 |
| `monitor_private_users` | 私聊监听，填 QQ 号 |
| `monitored_users_in_groups` | 群内指定用户监听，`{群号: [QQ号, ...]}` |
| `target_sessions` | 转发目标，必须填**完整会话 ID** |
| `max_messages` | 消息阈值，`1` 表示即时转发 |
| `bot_self_ids` | 机器人自身 ID，用于防止循环转发 |

> ⚠️ **编辑文件前必须先停用插件**。插件每 5 分钟会把内存里的配置回写到文件，
> 运行中手改会被覆盖。正确顺序是：停用插件 → 改文件 → 重新启用。

> ⚠️ `send_single_messages` 这个开关由 WebUI 管理，**在 config.json 里手改无效**，
> 会在插件启动时被 WebUI 的值覆盖，请在插件管理页切换。

详细的匹配规则与字段说明见 [配置说明](configuration.md)。

## 🧪 验证安装

1. `/turnrig list` 能看到你的任务，且 `🎯目标` 不为空
2. 让被监听的用户在目标群里发一条消息
3. debug 日志级别下应依次出现：

```
[messaging.message_listener] ✅ 群 <群号> 中的用户 <QQ号> 在监听列表中，应该监听此消息喵！ 🎯
[messaging.message_listener] 已缓存消息到任务 1, 会话 ..., 缓存大小: 1
[messaging.forward_manager] 成功将消息转发到 <目标会话> 喵～ ✅
```

目标会话里收到消息即安装成功。

## 🔧 常见安装问题

### 插件加载失败 / 日志里没有任何 turnrig 输出

- 确认目录名是 `astrbot_plugin_turnrig`（WebUI 上传安装会自动处理）
- 确认 `main.py`、`metadata.yaml` 在插件目录根部
- 看 AstrBot 启动日志里是否有插件加载报错

### 消息收到了但转发不出去

- 检查 `/turnrig list` 里 `🎯目标` 是否为空（为空则一条都不会发）
- QQ 目标：确认机器人在目标群里，且账号未被风控
- 非 QQ 目标（微信等）：确认会话 ID 前缀是平台实例 ID，不是 `aiocqhttp`，
  详见 [配置说明](configuration.md) 与 [故障排除](troubleshooting.md)

### 提示「只有管理员才能执行此操作」

所有管理命令都要求执行者是 AstrBot 管理员，请把自己的 QQ 加入 AstrBot 的管理员列表。

## 🎉 下一步

- ⚙️ [配置说明](configuration.md) — 了解所有字段与匹配规则
- 🚀 [使用教程](usage.md) — 常见场景配置示例
- 🔧 [故障排除](troubleshooting.md) — 出问题时先看这里
