# Skill-Atlas 🧭

[![GitHub stars](https://img.shields.io/github/stars/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas)
[![GitHub license](https://img.shields.io/github/license/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas/blob/main/LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Ready-ff6b6b)](https://claude.ai/code)
[![Codex](https://img.shields.io/badge/Codex-Ready-4ecdc4)](https://codex.com)

一个轻量的 Skills 目录布局，用软链接把 Claude Code 和 Codex 的 Skills 统一管理在同一个仓库里。  
A lightweight skills layout that keeps Claude Code and Codex in one repo via symlinks.

## 🧭 复制给 AI / Copy-Paste to AI

把仓库链接发给 Claude Code 或 Codex，然后直接让 AI 运行下面的命令。  
Send the repo link to Claude Code or Codex and ask it to run these commands.

示例指令（中文）：  
Example prompt (CN):

```
请阅读这个仓库并在项目根目录执行：
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh doctor
./manage.sh list shared
最后告诉我 Skills 是否可用。
```

Example prompt (EN):

```
Read this repo and run in the project root:
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh doctor
./manage.sh list shared
Tell me whether Skills are ready.
```

## 🎯 目标 / Goals

- 统一管理 Skills 目录，避免重复复制  
  Keep skills in one place without duplicating files
- 兼容 `SKILL.md` 标准，便于扩展  
  Stay compatible with the `SKILL.md` convention
- 简单可理解，能被脚本化  
  Keep it simple and scriptable

## 🚀 快速开始 / Quick Start

在包含 `.claude/` 的项目根目录运行（并确保 `skill-atlas/` 位于该目录下）：  
Run this from your project root that contains `.claude/` (with `skill-atlas/` inside it):

```bash
# 1) 一键部署 / one-click setup
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup

# 2) 测试 Skills 共享 / verify
# Claude Code: 使用 skill-atlas-test Skills 测试统一管理
# Codex: Use skill-atlas-test skill to verify unified management
```

如果 `skill-atlas/` 不在项目根目录，可以指定项目路径：  
If `skill-atlas/` lives elsewhere, pass the project root:

```bash
./skill-atlas/deploy.sh --project-root /path/to/project
```

目标工具目录来自 `targets.conf`，后续接入 Gemini/OpenCode 只需追加一行即可。  
Targets come from `targets.conf`; add one line to enable Gemini/OpenCode later.

## 🏗️ 结构 / Layout

```
skill-atlas/                    # 中央管理 / central repo
├── shared/                     # 已发布 Skills / published skills
│   └── skill-atlas-test/      # 测试 Skills / test skill
├── official/                   # 官方镜像（可选）/ optional mirror
├── custom/                     # 本地迭代 Skills / local iteration
├── targets.conf                # 目标工具目录 / target directories
├── deploy.sh                   # 一键部署 / setup script
└── manage.sh                   # 管理命令（由 deploy.sh 生成）

🔗 自动链接 / symlinks:
.claude/skills/skill-atlas  ──┐
                             ├─→ skill-atlas/
~/.codex/skills/skill-atlas ─┘

# 为了让工具直接发现 Skills，还会生成直链 / direct links for discovery:
.claude/skills/<skill>  ─→ skill-atlas/shared/<skill>
~/.codex/skills/<skill> ─→ skill-atlas/shared/<skill>
```

## 🎯 目标目录 / Targets

编辑 `targets.conf` 添加新的工具目录（相对路径会基于项目根目录解析）：  
Edit `targets.conf` to add more tools (relative paths resolve from project root):

```text
claude:.claude/skills
codex:~/.codex/skills
# gemini:/path/to/gemini/skills
# opencode:/path/to/opencode/skills
```

## 📋 使用示例 / Examples

```
# 在 custom 中迭代 / iterate in custom
./manage.sh add my-skill --custom

# 发布到 shared / publish to shared
./manage.sh publish my-skill

# 测试 Skills / test a skill
使用 my-skill Skills 处理我的任务

# 列出 Skills / list skills
./manage.sh list shared
```

## 🛠 管理命令 / Commands

```bash
./manage.sh list [shared|custom|all]     # 列出 Skills / list skills
./manage.sh add <name> [--custom|--shared] # 新建 Skills / add a skill
./manage.sh publish <name>              # custom -> shared
./manage.sh setup [project-root]         # 一键部署 / one-click setup
./manage.sh test                         # 运行测试 / run tests
./manage.sh sync                         # 同步软链接 / refresh symlinks
./manage.sh doctor                       # 检查链接状态 / check link status
```

## 🔎 说明 / Notes

- 这不是唯一的做法，类似的布局一定有人做过  
  This is not the only approach, and similar layouts likely exist
- 目前偏脚本化和轻量化，后续欢迎一起迭代  
  It is intentionally minimal and open to iteration
- `shared` 会被同步到目标工具目录；`custom` 不会  
  Only `shared` is linked into target tool directories
- 新接入工具时编辑 `targets.conf`，支持相对路径和 `~`  
  Add new tools by editing `targets.conf` (relative paths and `~` are supported)
- `template/` 是新建 Skills 的模板来源  
  `template/` provides the SKILL.md template for new Skills
- `./manage.sh` 是项目根目录的 wrapper，真实脚本在 `skill-atlas/manage.sh`  
  `./manage.sh` is a wrapper in project root; the real script lives in `skill-atlas/manage.sh`

## 📄 许可证 / License

[Apache 2.0](LICENSE)

## 🙌 致谢 / Thanks

- [Anthropic Skills](https://github.com/anthropics/skills) - 规范参考
- Claude Code & Codex 社区
