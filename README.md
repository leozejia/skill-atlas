# Skill-Atlas

Skill-Atlas is the Nexus entry library for skills. It is a cache + review +
distribution staging area, not a direct OpenClaw mount.

Skill-Atlas 是 Nexus 的技能入口库，负责“收集 → 评审 → 分发”，不是直接挂载到 OpenClaw 的技能目录。

## Layout

```
skill-atlas/
├── download/          # 原始下载区（榜单/仓库拉取）
├── review/            # 评审区（Architect + Jarvis 评审）
└── distribute/        # 分发区
    ├── global/        # 全局共享候选
    └── agents/        # 身份专用候选
        ├── jarvis/
        ├── guardian/
        ├── archivist/
        ├── marketing/
        └── logic/
```

## Workflow

1. 下载进入 `download/`。
2. 评审通过后进入 `review/`。
3. 按架构分发到 `distribute/global` 或 `distribute/agents/<id>`。
4. 最终由 Nexus 分发到 OpenClaw 全局或身份目录。

## Notes

- `download/`、`review/`、`distribute/` 不提交 Git（已在 `.gitignore` 忽略）。
- 旧的 `custom/shared/template` 流程已停用。
- 工具脚本后续会按新流程重整。

## License

[Apache 2.0](LICENSE)
