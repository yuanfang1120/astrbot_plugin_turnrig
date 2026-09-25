# ⚙️ 配置说明

欢迎查看 **Turnrig** 插件的详细配置说明 这里会告诉你如何正确配置所有功能！

## 📁 配置文件位置

插件的配置文件保存在：
```
AstrBot/data/plugins_data/astrbot_plugin_turnrig/config.json
```

> 💡 **提示**: 配置文件会在插件首次启动时自动创建

## 🏗️ 配置结构

### 基础配置格式

```json
{
  "tasks": [
    {
      "id": "任务ID",
      "name": "任务名称",
      "monitor_groups": ["群聊ID1", "群聊ID2"],
      "monitor_private_users": ["用户ID1", "用户ID2"],
      "monitored_users_in_groups": {
        "群聊ID": ["用户ID1", "用户ID2"]
      },
      "target_sessions": [
        "aiocqhttp:GroupMessage:目标群聊ID",
        "aiocqhttp:FriendMessage:目标用户ID"
      ],
      "max_messages": 20,
      "enabled": true
    }
  ],
  "default_max_messages": 20,
  "bot_self_ids": ["机器人ID1", "机器人ID2"]
}
```

## 📋 配置参数详解

### 🎯 任务配置 (tasks)

每个转发任务包含以下配置项：

#### **基本信息**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 任务的唯一标识符，系统自动生成 |
| `name` | string | ✅ | 任务的友好名称，便于识别 |
| `enabled` | boolean | ❌ | 是否启用该任务，默认为 `true` |

#### **监听源配置**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `monitor_groups` | array | `[]` | 需要监听的群聊ID列表 |
| `monitor_private_users` | array | `[]` | 需要监听的私聊用户ID列表 |
| `monitored_users_in_groups` | object | `{}` | 指定群聊中需要监听的特定用户 |

**monitored_users_in_groups 格式示例**:
```json
{
  "123456789": ["用户ID1", "用户ID2"],
  "987654321": ["用户ID3"]
}
```

> 💡 **键的匹配规则**：推荐一律使用**纯群号**作为键（如上例）。
>
> 插件匹配时依次尝试：① 纯群号 → ② 完整会话ID（`平台实例ID:GroupMessage:群号`）→ ③ 任何以 `:群号` 结尾的键。
>
> 第 ③ 条是针对历史配置的兜底：`v1.6.6` 之前 `/turnrig adduser` 写入的键带着写死的 `aiocqhttp:` 前缀，而运行时会话ID的前缀是平台实例ID（常见为 `qq`），当时会导致监听永远不生效。现在新旧两种键都能匹配上。

#### **转发目标配置**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `target_sessions` | array | `[]` | 消息转发的目标会话列表 |

**target_sessions 格式规范**:
- 群聊: `aiocqhttp:GroupMessage:群聊ID`
- 私聊: `aiocqhttp:FriendMessage:用户ID`

#### **触发条件配置**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_messages` | integer | `20` | 消息累积到此数量时触发转发 |

### 🌍 全局配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_max_messages` | integer | `20` | 任务未设置消息阈值时的默认值 |
| `bot_self_ids` | array | `[]` | 机器人自身ID列表，用于防止循环转发 |

## 📝 配置示例

### 示例1: 简单群聊转发

```json
{
  "tasks": [
    {
      "id": "simple_forward",
      "name": "工作群转发",
      "monitor_groups": ["123456789"],
      "monitor_private_users": [],
      "monitored_users_in_groups": {},
      "target_sessions": ["aiocqhttp:GroupMessage:987654321"],
      "max_messages": 10,
      "enabled": true
    }
  ],
  "default_max_messages": 20
}
```

### 示例2: 多源多目标转发

```json
{
  "tasks": [
    {
      "id": "multi_forward",
      "name": "多群汇总",
      "monitor_groups": ["111111111", "222222222", "333333333"],
      "monitor_private_users": [],
      "monitored_users_in_groups": {},
      "target_sessions": [
        "aiocqhttp:GroupMessage:999999999",
        "aiocqhttp:FriendMessage:888888888"
      ],
      "max_messages": 15,
      "enabled": true
    }
  ],
  "default_max_messages": 20
}
```

### 示例3: 特定用户监听

```json
{
  "tasks": [
    {
      "id": "user_specific",
      "name": "重要用户监听",
      "monitor_groups": [],
      "monitor_private_users": ["555555555"],
      "monitored_users_in_groups": {
        "123456789": ["777777777", "888888888"]
      },
      "target_sessions": ["aiocqhttp:FriendMessage:999999999"],
      "max_messages": 5,
      "enabled": true
    }
  ],
  "default_max_messages": 20,
  "bot_self_ids": ["123456789"]
}
```

## 🔧 高级配置

### 防循环转发设置

为了防止机器人消息被转发造成循环，可以配置 `bot_self_ids`:

```json
{
  "bot_self_ids": ["你的机器人QQ号1", "你的机器人QQ号2"]
}
```

### 消息阈值优化

- **低频群聊**: 设置较小的 `max_messages` (5-10)
- **高频群聊**: 设置较大的 `max_messages` (20-50)
- **即时转发**: 设置为 1 (注意可能产生大量转发)

## ⚡ 动态配置

### 通过命令修改配置

大多数配置可以通过插件命令动态修改，无需手动编辑配置文件：

```bash
# 创建新任务
/turnrig create 新任务名称

# 添加监听源
/turnrig monitor 任务ID 群聊 群聊ID

# 添加转发目标
/turnrig target 任务ID 群聊 目标群聊ID

# 设置消息阈值
/turnrig threshold 任务ID 数量
```

详细命令说明请查看 [使用教程](usage.md) 

### 配置文件更新并应用

修改配置文件后会在下次任务执行时生效，需要重启插件

## 🔍 配置验证

### 常见配置错误

1. **会话ID格式错误**
   ```json
   // ❌ 错误
   "target_sessions": ["123456789"]
   
   // ✅ 正确
   "target_sessions": ["aiocqhttp:GroupMessage:123456789"]
   ```

2. **任务ID重复**
   ```json
   // ❌ 错误：两个任务使用相同ID
   "tasks": [
     {"id": "1", "name": "任务A"},
     {"id": "1", "name": "任务B"}
   ]
   ```

3. **数据类型错误**
   ```json
   // ❌ 错误
   "max_messages": "20"
   
   // ✅ 正确
   "max_messages": 20
   ```

### 配置检查命令

可以使用以下命令检查配置状态：

```bash
# 列出所有任务
/turnrig list

# 查看任务状态
/turnrig status 任务ID
```

## 📊 性能优化建议

### 监听源优化

- 避免监听过多的群聊，建议单个任务不超过10个监听源
- 合理设置消息阈值，避免频繁触发转发
- 使用特定用户监听而非全群监听来减少处理量

### 目标优化

- 单个任务的转发目标建议不超过5个
- 避免将同一个会话设置为多个任务的目标

### 缓存优化

插件会自动清理过期的消息缓存，默认保留7天的数据

## 🚨 注意事项

1. **权限要求**: 确保机器人在监听源和转发目标中都有足够的权限
2. **频率限制**: QQ平台有API调用频率限制，避免设置过小的消息阈值
3. **存储空间**: 大量的消息缓存可能占用较多磁盘空间，定期清理无用任务
4. **隐私保护**: 转发功能涉及消息内容，请确保符合相关隐私规定

---

配置完成后，记得重启插件或使用命令重载配置让更改生效 ✨

如果配置过程中遇到问题，可以查看 [故障排除](troubleshooting.md) 文档！ 
