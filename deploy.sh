#!/bin/bash
# deploy.sh - Skill-Atlas 一键部署脚本

echo "🚀 Skill-Atlas 部署中..."

# 1. 检查环境
if [ ! -d ".claude" ]; then
    echo "❌ 需要在 Claude Code 项目目录运行"
    exit 1
fi

# 2. 创建必要目录
mkdir -p .claude/skills/skill-atlas/
mkdir -p ~/.codex/skills/skill-atlas/

# 3. 建立软链接
ln -sf "$(pwd)/skill-atlas/" .claude/skills/skill-atlas/
ln -sf "$(pwd)/skill-atlas/" ~/.codex/skills/skill-atlas/

# 4. 创建管理命令
cat > manage.sh << 'EOF'
#!/bin/bash
case $1 in
    "list") find skill-atlas/shared/ -name "SKILL.md" -exec dirname {} \; | xargs -L1 basename ;;
    "add") mkdir -p "skill-atlas/shared/$2/"; cp skill-atlas/template/SKILL.md "skill-atlas/shared/$2/"; echo "✅ 新技能 $2 已创建" ;;
    "test") echo "使用 skill-atlas-test 技能测试系统" ;;
    "sync") echo "同步官方技能..." ;;
    *) echo "manage.sh [list|add <name>|test|sync]" ;;
esac
EOF
chmod +x manage.sh

# 5. 创建模板
mkdir -p skill-atlas/template/
cat > skill-atlas/template/SKILL.md << 'EOF'
---
name: my-new-skill
description: 描述你的技能功能和使用场景
---
# My New Skill

## 使用场景
当需要...

## 执行步骤
1. ...
2. ...

## 示例
"使用 my-new-skill 技能处理..."
EOF

echo "✅ 部署完成！"
echo ""
echo "测试命令："
echo "  ./manage.sh list"
echo "  使用 skill-atlas-test 技能测试 Skill-Atlas"
echo "管理命令："
echo "  ./manage.sh add my-skill"
