# Skill-Atlas 🧭

[![GitHub stars](https://img.shields.io/github/stars/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas)
[![GitHub license](https://img.shields.io/github/license/leozejia/skill-atlas)](https://github.com/leozejia/skill-atlas/blob/main/LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Ready-ff6b6b)](https://claude.ai/code)
[![Codex](https://img.shields.io/badge/Codex-Ready-4ecdc4)](https://codex.com)

**世界上第一个跨 Claude Code + Codex 的统一技能管理系统**

## 🎯 一句话介绍
将 Claude Code 和 Codex 的技能统一管理，通过软链接实现零复制共享，支持自然语言触发和官方标准。

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/leozejia/skill-atlas.git
cd skill-atlas

# 2. 一键部署
chmod +x deploy.sh
./deploy.sh

# 3. 测试技能共享
# Claude Code: \"使用 skill-atlas-test 技能测试统一管理\"
# Codex: \"Use skill-atlas-test skill to verify unified management\"
```

## 🏗️ 架构

```
skill-atlas/                    # 中央管理
├── shared/                     # 共享技能库
│   └── skill-atlas-test/      # ✅ MVP 测试技能
├── official/                   # 官方技能镜像
├── custom/                     # 自定义技能
├── deploy.sh                   # 🚀 一键部署
└── manage.sh                   # 🛠 管理命令

🔗 自动链接:
.claude/skills/skill-atlas/ ──┐
                              ├─→ skill-atlas/
~/.codex/skills/skill-atlas/ ─┘
```

## ✨ 特性

- ✅ **零复制共享**：软链接技术，文件实时同步
- ✅ **官方标准**：完美兼容 `SKILL.md` 规范
- ✅ **自然语言触发**：无需记住命令
- ✅ **跨平台**：Claude Code + Codex 无缝集成
- ✅ **一键部署**：3 秒完成环境配置
- ✅ **开源免费**：Apache 2.0 许可

## 📋 使用示例

```
# 添加新技能
./manage.sh add \"my-custom-skill\"

# 测试技能
使用 my-custom-skill 技能处理我的任务

# 列出技能
./manage.sh list
```

## 🛠 管理命令

```bash
./manage.sh list      # 列出所有技能
./manage.sh add <name>  # 添加新技能
./manage.sh test      # 运行测试
./manage.sh sync      # 同步官方技能
```

## 🎨 贡献指南

1. Fork 仓库
2. 创建技能目录：`mkdir shared/my-skill/`
3. 编辑 `SKILL.md`（参考 template/）
4. 测试：`使用 my-skill 技能...`
5. PR 提交！

## 📄 许可证

[Apache 2.0](LICENSE)

## 🙌 致谢

- [Anthropic Skills](https://github.com/anthropics/skills) - 官方标准
- Claude Code & Codex 社区

---
**Made with ❤️ for AI 技能革命**
