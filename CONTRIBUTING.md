# 🤝 贡献指南

感谢你对本项目的关注！欢迎提交问题反馈、文档改进和代码贡献。

> 本项目是 [`astrbot_plugin_turnrig`](https://github.com/WentUrc/astrbot_plugin_turnrig) 的二次开发版本。
> 如果你的问题与**原项目**相关（而不是本仓库的改动导致的），也建议同时到上游仓库反馈。

## 🐛 反馈问题

提交 Issue 前请先：

1. 浏览已有 [Issues](https://github.com/yuanfang1120/astrbot_plugin_turnrig/issues)，确认没有重复
2. 确认插件版本（WebUI 插件管理页可以看到版本号，或看 `metadata.yaml`）
3. 打开 AstrBot 的 **debug** 日志级别，把相关日志一起贴上

一个问题描述里请包含：

- 你执行的指令、以及完整的报错/日志
- 预期结果 vs 实际结果
- AstrBot 版本、本插件版本、OneBot 实现（NapCat / Lagrange 等）

> 💡 排查「消息没被转发」时，先看日志里有没有这一行（INFO 级）：
> ```
> [messaging.message_listener] ✅ 群 <群号> 中的用户 <QQ号> 在监听列表中，应该监听此消息喵！ 🎯
> ```
> 没有它说明监听没匹配上，属于配置问题而非转发问题。

## 🔀 提交代码

```bash
# 1. Fork 本仓库后克隆你自己的 fork
git clone https://github.com/yuanfang1120/astrbot_plugin_turnrig.git
cd astrbot_plugin_turnrig

# 2. 基于 main 建分支
git checkout -b fix/你的改动

# 3. 改完提交并推送，然后开 Pull Request
git push origin fix/你的改动
```

请保持一个 PR 只做一件事，便于审查。

## 🧪 开发环境与自检

插件本身只依赖 AstrBot 运行环境，无需额外安装依赖即可开发（`Pillow`、`requests` 仅在使用对应功能时才需要）。

提交前建议跑两个检查：

```bash
# 代码风格（仓库已配好 ruff 规则）
ruff check .
ruff format .

# 群内指定用户匹配逻辑自检（用占位模块替代 astrbot，无需装 AstrBot）
python scripts/check_group_user_match.py
```

如果改了消息转发、监听匹配这类核心逻辑，请在 PR 描述里说明你**实际跑过**的场景
（在哪个平台、什么消息类型、结果如何），这比单纯说「已修复」有用得多。

## 🎨 代码风格

- 使用 `ruff` 默认规则（见 `pyproject.toml`），行宽 88，双引号
- 注释和日志是中文风格，保留现有写法即可
- 详细规范见 [docs/development/coding-style.md](docs/development/coding-style.md)

**注意**：`metadata.yaml` 的 `name` / `repo` 字段关系到 AstrBot 的插件识别与更新检测，
除非确实必要，不要随意改动。

## 📝 提交信息

建议使用 [Conventional Commits](https://www.conventionalcommits.org/) 风格：

```
fix: 修正群内指定用户监听因平台前缀不匹配而永不生效的问题
feat: 支持把转发目标指向非 QQ 平台
docs: 补充跨平台转发目标的会话 ID 写法
```

本项目带 CI 自动生成 `CHANGELOG.md`（按 commit 汇总）。如果你希望改动出现在更新日志里，
**请把要点写清楚在 commit message 里**，而不是只写「修复 bug」。

## 📄 许可证

本项目以 **AGPL-3.0** 授权（见 [LICENSE](LICENSE)）。

提交贡献即表示你同意你的代码以相同许可证发布，并且你有权提交这些代码
（不要直接复制来源不明或授权不兼容的代码）。

---

再次感谢你的贡献！✨
