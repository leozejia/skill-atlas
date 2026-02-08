# Skill-Atlas

[![GitHub stars](https://img.shields.io/github/stars/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas)
[![GitHub license](https://img.shields.io/github/license/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas/blob/main/LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Ready-ff6b6b)](https://claude.ai/code)
[![Codex](https://img.shields.io/badge/Codex-Ready-4ecdc4)](https://codex.com)

Skill-Atlas is a scaffolding layer for Skills and a general-purpose tool layer.
It helps non-technical users install and manage Skills, with a local visual
manager that syncs the skills.sh (Vercel) ranking to your machine.

Skill-Atlas 是 Skills 的脚手架层，也是通用工具层。
它让普通人也能用上 Skills，并提供可视化页面同步 skills.sh（Vercel 生态）排行榜到本机。

There is no official Skills installer today; we treat Vercel's add-skill as a community tool.
目前没有统一官方的 Skills 安装器；我们把 Vercel 的 add-skill 视作社区工具。

## AI 快速启动 / AI Quick Start

把仓库链接发给 Claude Code 或 Codex，让它在项目根目录执行：
Share the repo link with Claude Code or Codex and ask it to run in the project root:

```
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh ui
```

中文提示词：

```
请阅读这个仓库并在项目根目录执行：
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh ui
打开页面后告诉我已安装的 Skills 数量。
```

English prompt:

```
Read this repo and run in the project root:
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh ui
Open the page and tell me how many Skills are installed.
```

## 可视化管理 / Visual Manager
定位：通用工具层的 Skills 脚手架。

启动：

```bash
./manage.sh ui
# 浏览器打开 http://127.0.0.1:5199
```

你可以在页面里：
- 查看 Top Skills 是否已安装
- 一键同步 Top Skills（安装缺失项）
- 强制更新（覆盖已安装版本）

## 高级：自定义迭代 / Advanced: Local Iteration

- 在 `custom/` 中迭代 Skills，发布到 `shared/`
- `./manage.sh publish <name>` 把 Skills 从 `custom/` 提升到 `shared/`
- `./manage.sh sync` 把 `shared/` 链接到本地 agent 目录

## 安装与分发 / Distribution (add-skill)

`npx add-skill` / `npx skills add` 从仓库或 URL 安装，不会从本地 `~/.agents/skills` 读取。
`npx add-skill` / `npx skills add` install from repo or URL; they do not read your local `~/.agents/skills`.

本地安装示例 / Local install:

```bash
npx add-skill ./skill-atlas/shared --skill <skill-name> --agent claude-code codex --yes --global
```

分发给他人 / Distribute to others:

```bash
npx add-skill <owner>/skill-atlas --skill <skill-name> --agent claude-code codex --yes --global
```

安装位置 / Install location:

- `~/.agents/skills/<skill>`
- `~/.claude/skills/<skill>`、`~/.codex/skills/<skill>`（通常是软链接 / usually symlinks）

## 目录结构 / Layout

```
skill-atlas/
├── shared/          # publish-ready Skills
├── custom/          # local iteration
├── official/        # optional mirror
├── template/        # new Skill template
├── targets.conf     # target directories
├── tools/           # scripts (installer/UI)
├── ui/              # visual manager
├── deploy.sh        # setup script
└── manage.sh        # manager (generated)
```

## 命令 / Commands

```bash
./manage.sh list [shared|custom|all]
./manage.sh add <name> [--custom|--shared]
./manage.sh publish <name>
./manage.sh setup [project-root]
./manage.sh sync
./manage.sh doctor
./manage.sh test
./manage.sh ui
```

## 说明 / Notes

- 本仓库只对接 skills.sh（Vercel 生态）排行榜的可视化同步
- `custom/` 仍适合团队自定义迭代，`shared/` 用于发布
- `./manage.sh` 在项目根目录是 wrapper

## License

[Apache 2.0](LICENSE)
