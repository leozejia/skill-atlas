# Skill-Atlas

[![GitHub stars](https://img.shields.io/github/stars/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas)
[![GitHub license](https://img.shields.io/github/license/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas/blob/main/LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Ready-ff6b6b)](https://claude.ai/code)
[![Codex](https://img.shields.io/badge/Codex-Ready-4ecdc4)](https://codex.com)

Skill-Atlas is a thin authoring layer for Skills. It focuses on local creation, iteration, and team workflow.
It does not replace any installer. Distribution uses `npx add-skill` / `npx skills add` from a repo or URL.

Skill-Atlas 是 Skills 的本地创作薄层，用于本地创建、迭代与团队协作。
它不会替代安装器，分发仍通过仓库或 URL 使用 `npx add-skill` / `npx skills add`。

There is no official Skills installer today; we treat Vercel's add-skill as a community tool.
目前没有统一官方的 Skills 安装器；我们把 Vercel 的 add-skill 视作社区工具。

## AI 快速启动 / AI Quick Start

把仓库链接发给 Claude Code 或 Codex，让它在项目根目录执行：
Share the repo link with Claude Code or Codex and ask it to run in the project root:

```
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh doctor
./manage.sh list shared
```

中文提示词：

```
请阅读这个仓库并在项目根目录执行：
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh doctor
./manage.sh list shared
最后告诉我 Skills 是否可用。
```

English prompt:

```
Read this repo and run in the project root:
chmod +x skill-atlas/manage.sh
./skill-atlas/manage.sh setup
./manage.sh doctor
./manage.sh list shared
Then tell me whether Skills are ready.
```

## 定位 / Positioning

- 本项目是 Skills 本地创作与协作的薄层 / A thin layer for local Skills authoring and teamwork
- 统一 `custom/` 与 `shared/` 的流程，不做全局注册 / Keeps `custom/` and `shared/` workflow consistent, no registry
- 分发交给 `add-skill` 生态 / Distribution stays with the `add-skill` ecosystem

## 工作流 / Workflow

- `custom/` 中迭代 Skills，`shared/` 存放可发布版本 / Iterate in `custom/`, publish-ready Skills live in `shared/`
- `./manage.sh publish <name>` 把 Skills 从 `custom/` 提升到 `shared/` / Promote a Skill to `shared/`
- `./manage.sh sync` 把 `shared/` 链接到目标工具目录 / Sync `shared/` into agent directories
- `npx add-skill` 用仓库或 URL 分发 / Distribute via repo or URL with `npx add-skill`

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
├── shared/          # 可发布的 Skills / publish-ready Skills
├── custom/          # 本地迭代 / local iteration
├── official/        # 可选镜像 / optional mirror
├── template/        # 新建 Skills 模板 / new Skill template
├── targets.conf     # 目标目录 / target directories
├── deploy.sh        # 初始化脚本 / setup script
└── manage.sh        # 管理脚本（由 deploy.sh 生成）/ manager (generated)
```

## 目标目录 / Targets

编辑 `targets.conf` 追加新的工具目录（相对路径基于项目根目录）。
Edit `targets.conf` to add new tool directories (relative paths resolve from project root).

```text
claude:.claude/skills
codex:~/.codex/skills
# gemini:/path/to/gemini/skills
# opencode:/path/to/opencode/skills
```

## 命令 / Commands

```bash
./manage.sh list [shared|custom|all]        # 列出 Skills / list Skills
./manage.sh add <name> [--custom|--shared]  # 新建 Skills / add a Skill
./manage.sh publish <name>                  # custom -> shared
./manage.sh setup [project-root]            # 初始化 / setup
./manage.sh sync                            # 刷新链接 / refresh links
./manage.sh doctor                          # 检查链接 / check links
./manage.sh test                            # 输出测试提示 / print test hint
```

## 说明 / Notes

- 仅 `shared/` 会被同步到目标目录 / Only `shared/` is synced to targets
- `template/` 为 `manage.sh add` 提供 SKILL.md 模板 / `template/` backs `manage.sh add`
- `./manage.sh` 在项目根目录是 wrapper / Repo root `./manage.sh` is a wrapper

## License

[Apache 2.0](LICENSE)
