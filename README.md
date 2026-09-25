# TurnRig · AstrBot 消息转发插件

> 监听指定会话的消息，转发到 QQ 群 / 好友，或其他 AstrBot 支持的平台（如微信）。
> 支持精确到「**某个群里某个人的发言**」，也支持整群监听。

<!-- FORTUNE_ANCHOR -->

## 🔮 每日占卜 (2026-09-25 16:07 CST)

**😅 需要加油** ✨

🎯 **幸运数字**: 38
🎨 **幸运颜色**: 💜 紫色
💡 **今日建议**: 今天是修复bug的好日子喵～

*每天更新一次，仅供娱乐喵～* 🐱


## ✨ 功能特性

- 🎯 **精确监听**：可只监听「指定群里指定用户」的发言，不会把整个群的消息都转出去
- 🔀 **多任务**：每个任务独立配置监听源、转发目标、消息阈值，互不干扰
- 📤 **跨平台转发**：目标可以是 QQ（走合并转发卡片），也可以是微信等其他平台（自动合并成**一条**消息发出）
- ⚡ **即时转发**：阈值设为 `1` 即为「来一条转一条」
- 🖼️ **富媒体**：文字、图片、视频、文件、引用回复、嵌套转发等
- 🔄 **可靠投递**：发送失败会进失败缓存并定期重试，不会静默丢失
- 🧹 **自动维护**：定期保存配置、清理过期消息记录与临时文件

## 📦 安装

1. 在 AstrBot 的 WebUI「插件管理」里上传本仓库的 zip 安装，或
2. 手动把 `astrbot_plugin_turnrig` 整个目录放进 `AstrBot/data/plugins/`，然后重启 AstrBot

> 插件本体只依赖 AstrBot 自身与 Python 标准库，另有 `requests`、`Pillow` 两个第三方库
> （`Pillow` 仅在把 GIF 转静态图时才用到），一般 AstrBot 环境已自带。

安装后在 WebUI 里启用插件，看到日志出现「转发侦听器插件初始化完成」即加载成功。

## 🚀 快速上手

以「监听 `996221889` 群里 `1957780271` 的发言，转发到我自己的 QQ」为例：

```
# 1. 创建任务，会返回任务 ID（下面假设是 1）
/turnrig create 测试

# 2. 添加「群内指定用户」监听（建议在目标群里发简化版，会自动带上当前群号）
/tr adduser 1 1957780271
#    或者在任意会话里用完整版
/turnrig adduser 1 996221889 1957780271

# 3. 设置转发目标为你的 QQ 私聊
/turnrig target 1 私聊 你的QQ号

# 4. 阈值设为 1，来一条转一条
/turnrig threshold 1 1
```

之后让 `1957780271` 在那个群里发一条消息，你的私聊就会收到转发。

查看当前状态：

```
/turnrig list          # 任务列表（能看到监听源、监听人数、目标、阈值）
/turnrig status 1      # 指定任务的缓存状态
```

> ⚠️ 所有管理命令都需要 **AstrBot 管理员**权限。
> ⚠️ 阈值不设置的话默认是 `20`，意味着要攒够 20 条才转发一次。

## 🛠️ 指令一览

### 任务管理

| 指令 | 说明 |
| :--- | :--- |
| `/turnrig list` | 列出所有转发任务 |
| `/turnrig status [任务ID]` | 查看任务缓存状态 |
| `/turnrig create [名称]` | 创建任务 |
| `/turnrig delete <任务ID>` | 删除任务 |
| `/turnrig enable <任务ID>` | 启用任务 |
| `/turnrig disable <任务ID>` | 禁用任务 |
| `/turnrig rename <任务ID> <名称>` | 重命名任务 |
| `/turnrig threshold <任务ID> <数量>` | 设置消息阈值（设为 1 即为即时转发） |

### 监听源

| 指令 | 说明 |
| :--- | :--- |
| `/turnrig monitor <任务ID> 群聊/私聊 <会话ID>` | 添加监听源 |
| `/turnrig unmonitor <任务ID> 群聊/私聊 <会话ID>` | 移除监听源 |
| `/turnrig adduser <任务ID> <群号> <QQ号>` | 添加「群内指定用户」监听 |
| `/turnrig removeuser <任务ID> <群号> <QQ号>` | 移除「群内指定用户」监听 |

### 转发目标

| 指令 | 说明 |
| :--- | :--- |
| `/turnrig target <任务ID> 群聊/私聊 <会话ID>` | 添加转发目标 |
| `/turnrig untarget <任务ID> 群聊/私聊 <会话ID>` | 移除转发目标 |
| `/turnrig forward <任务ID> [群聊/私聊 <会话ID>]` | 手动触发一次转发 |

### 其他

| 指令 | 说明 |
| :--- | :--- |
| `/turnrig addbot <QQ号>` / `removebot <QQ号>` / `listbots` | 管理机器人 ID 过滤列表（防循环转发） |
| `/turnrig cleanup <天数>` | 清理指定天数前的已处理消息记录 |
| `/turnrig help` | 显示完整帮助 |

### 简化指令 `/tr`

在目标会话里直接执行，自动使用当前会话 ID，省去手输 ID：

| 指令 | 说明 |
| :--- | :--- |
| `/tr add <任务ID>` / `/tr remove <任务ID>` | 把当前会话加入 / 移出监听列表 |
| `/tr target <任务ID>` / `/tr untarget <任务ID>` | 把当前会话加入 / 移出转发目标 |
| `/tr adduser <任务ID> <QQ号>` | 把指定用户加入**当前群**的监听列表 |
| `/tr removeuser <任务ID> <QQ号>` | 从**当前群**的监听列表移除指定用户 |
| `/tr list` / `/tr help` | 列出任务 / 查看简化指令帮助 |

## 📝 会话 ID 格式

AstrBot 的会话 ID 是 `平台实例ID:消息类型:会话ID`，例如 `qq:GroupMessage:996221889`。

配置监听源 / 转发目标时，插件支持这些写法：

- ✅ **推荐**：`群聊 群号`、`私聊 QQ号`（中间**必须有空格**）
- ✅ **标准**：`<平台实例ID>:GroupMessage:<群号>`、`<平台实例ID>:FriendMessage:<QQ号>`
- ✅ **最省事**：在目标会话里直接发 `/tr add` 或 `/tr target`，自动取真实 ID
- ❌ 不推荐：直接写纯数字 ID，可能被当成类型识别错误

> [!IMPORTANT]
> `群聊 xxx` / `私聊 xxx` 这两种简写会把平台前缀固定成 `aiocqhttp`，**只能用于 QQ 目标**。
>
> 要转发到微信等其他平台，必须使用完整的三段式 ID，且前缀是你在 AstrBot WebUI 里给该平台连接起的名字
> （如 `weixin_personal`）：
>
> ```
> /turnrig target 1 weixin_personal:FriendMessage:wxid_xxxxxxxx
> ```
>
> 前缀写错的话消息会被当成 QQ 好友投递，发不到微信里。**所以跨平台目标强烈建议用 `/tr target`**。

## ⚙️ WebUI 配置

插件在 WebUI 中只暴露一个开关：

- `send_single_messages`：开启后，转发到 **QQ** 时跳过「合并转发卡片」，改为逐条发送。

任务列表、监听源、转发目标、消息阈值等**全部由指令管理**，持久化在
`data/plugins_data/astrbot_plugin_turnrig/config.json`，不会被 WebUI 配置覆盖。
改完开关后需要在插件管理页「重载插件」才会生效。

> 该开关**不影响**非 QQ 平台（微信等）：那条路径本来就是合并成一条普通消息发送的。

## 💾 数据存储

插件的所有数据都在 `AstrBot/data/plugins_data/astrbot_plugin_turnrig/` 下：

| 文件 | 说明 |
| :--- | :--- |
| `config.json` | 任务配置（监听源、目标、阈值等） |
| `message_cache.json` | 消息缓存 |
| `temp/` | 转发过程中下载的临时图片文件 |

维护节奏：每 5 分钟保存一次配置；每小时清理 7 天前的消息 ID 记录、清理 2 小时前的临时文件。

## 🐛 故障排除

完整排查手册见 [docs/user-guide/troubleshooting.md](docs/user-guide/troubleshooting.md)。最常见的一步是先确认**监听是否匹配上**——

打开 debug 日志级别后，匹配成功一定会打印：

```
[messaging.message_listener] ✅ 群 <群号> 中的用户 <QQ号> 在监听列表中，应该监听此消息喵！ 🎯
```

没有这一行，说明任务没命中，继续看这条（debug 级）三个判断结果：

```
任务 <ID> 监听判断结果喵: 常规监听=False, 用户监听=False, 群内用户监听=False 📊
```

另外，AstrBot 的**会话白名单**是在事件分发之前生效的，如果群里消息连插件日志都不产生，
先检查白名单里是否漏加了该会话。

## 📚 文档导航

- 📖 [文档中心](docs/README.md)
- 📦 [安装指南](docs/user-guide/installation.md)
- ⚙️ [配置说明](docs/user-guide/configuration.md)
- 🚀 [使用教程](docs/user-guide/usage.md)
- 🔧 [故障排除](docs/user-guide/troubleshooting.md)
- 🏛️ [架构与 API 文档](docs/README.md#-开发者文档)

## 🙏 致谢与来源

本项目是 [`astrbot_plugin_turnrig`](https://github.com/WentUrc/astrbot_plugin_turnrig)
（原作者 **IGCrystal** / **WentUrc**）的**二次开发版本**，在原项目基础上修复了若干问题并调整了部分行为。
感谢原作者的出色工作。

本仓库的修改内容记录在 [CHANGELOG.md](CHANGELOG.md) 中。

## 📄 许可证

[AGPL-3.0](LICENSE)。

原项目同样以 AGPL-3.0 授权，二次开发版本必须继续沿用该许可证并保留原始版权声明。
如果你通过网络向他人提供本插件的功能，同样需要按 AGPL-3.0 提供完整源码。
