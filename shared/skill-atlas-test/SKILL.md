---
name: skill-atlas-test
description: Skill-Atlas 统一技能管理测试技能。当提到"Skill-Atlas"、"统一技能管理"、"测试技能共享"或"skill-atlas-test"时使用，用于验证跨 Claude Code 和 Codex 的技能共享机制。
---
# Skill-Atlas Test Skill ✅

## 测试触发
当用户说 "测试 skill-atlas" 或 "/skill skill-atlas/test" 时执行。

## 执行步骤
1. 确认 Skill-Atlas 机制正常工作
2. 显示当前环境信息
3. 验证软链接路径正确
4. 输出成功信息

## 输出格式
```
✅ Skill-Atlas v2.0 部署成功！
📂 当前目录: $(pwd)
🔗 技能路径: skill-atlas/test
🛠  平台: Claude Code / Codex
📈 Skill-Atlas: /Users/zejiawu/Projects/Project-Atlas/skill-atlas/
```
