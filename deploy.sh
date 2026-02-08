#!/bin/bash
# deploy.sh - Skill-Atlas 一键部署脚本

set -euo pipefail

echo "🚀 Skill-Atlas 部署中..."

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_atlas_dir="$script_dir"
targets_file="${SKILL_ATLAS_TARGETS_FILE:-$skill_atlas_dir/targets.conf}"

project_root="${SKILL_ATLAS_PROJECT_ROOT:-}"
while [ $# -gt 0 ]; do
    case "$1" in
        --project-root)
            if [ $# -lt 2 ]; then
                echo "❌ --project-root 需要路径参数"
                exit 1
            fi
            project_root="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$project_root" ]; then
    if [ -d "$skill_atlas_dir/../.claude" ]; then
        project_root="$(cd "$skill_atlas_dir/.." && pwd)"
    elif [ -d ".claude" ]; then
        project_root="$(pwd)"
    else
        echo "❌ 找不到 .claude/，请在 Claude Code 项目根目录运行"
        echo "   或指定: SKILL_ATLAS_PROJECT_ROOT=/path/to/project ./skill-atlas/deploy.sh"
        exit 1
    fi
fi

if [ ! -d "$project_root" ]; then
    echo "❌ 无效的项目路径: $project_root"
    exit 1
fi

if [ ! -d "$project_root/.claude" ]; then
    echo "❌ 未找到 $project_root/.claude"
    exit 1
fi

shared_dir="$skill_atlas_dir/shared"
custom_dir="$skill_atlas_dir/custom"

mkdir -p "$shared_dir" "$custom_dir"

targets=()
target_dirs=()

trim_line() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

append_target() {
    local entry
    entry="$(trim_line "$1")"
    [ -n "$entry" ] || return 0
    targets+=("$entry")
}

read_targets() {
    local line
    targets=()
    if [ -f "$targets_file" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            line="${line%%#*}"
            line="$(trim_line "$line")"
            [ -n "$line" ] || continue
            append_target "$line"
        done < "$targets_file"
    fi

    if [ ${#targets[@]} -eq 0 ]; then
        targets=("claude:.claude/skills" "codex:~/.codex/skills")
    fi

    if [ -n "${SKILL_ATLAS_EXTRA_TARGETS:-}" ]; then
        IFS=',' read -r -a extra_targets <<< "$SKILL_ATLAS_EXTRA_TARGETS"
        for entry in "${extra_targets[@]}"; do
            append_target "$entry"
        done
    fi
}

resolve_target_path() {
    local path="$1"
    if [[ "$path" == ~* ]]; then
        path="${path/#\~/$HOME}"
    fi
    if [[ "$path" = /* ]]; then
        printf '%s' "$path"
    else
        printf '%s' "$project_root/$path"
    fi
}

load_targets() {
    local entry name path resolved
    target_dirs=()
    read_targets
    for entry in "${targets[@]}"; do
        name="${entry%%:*}"
        path="${entry#*:}"
        if [ -z "$name" ] || [ -z "$path" ] || [ "$name" = "$entry" ]; then
            echo "⚠️  跳过无效 target: $entry"
            continue
        fi
        resolved="$(resolve_target_path "$path")"
        target_dirs+=("$name:$resolved")
        mkdir -p "$resolved"
    done
}

link_skill_atlas_root() {
    local entry target_dir
    for entry in "${target_dirs[@]}"; do
        target_dir="${entry#*:}"
        ln -sfn "$skill_atlas_dir" "$target_dir/skill-atlas"
    done
}

link_shared_skills() {
    local skill_dir name entry target_dir
    for skill_dir in "$shared_dir"/*; do
        [ -d "$skill_dir" ] || continue
        [ -f "$skill_dir/SKILL.md" ] || continue
        name="$(basename "$skill_dir")"
        for entry in "${target_dirs[@]}"; do
            target_dir="${entry#*:}"
            ln -sfn "$skill_dir" "$target_dir/$name"
        done
    done
}

load_targets
link_skill_atlas_root
link_shared_skills

cat > "$skill_atlas_dir/manage.sh" << 'EOF'
#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_atlas_dir="$script_dir"
targets_file="${SKILL_ATLAS_TARGETS_FILE:-$skill_atlas_dir/targets.conf}"
project_root="${SKILL_ATLAS_PROJECT_ROOT:-$(cd "$script_dir/.." && pwd)}"
shared_dir="$skill_atlas_dir/shared"
custom_dir="$skill_atlas_dir/custom"
template_path="$skill_atlas_dir/template/SKILL.md"

if [ ! -d "$project_root/.claude" ]; then
    echo "❌ 未找到 $project_root/.claude"
    exit 1
fi

targets=()
target_dirs=()

trim_line() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

append_target() {
    local entry
    entry="$(trim_line "$1")"
    [ -n "$entry" ] || return 0
    targets+=("$entry")
}

read_targets() {
    local line
    targets=()
    if [ -f "$targets_file" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            line="${line%%#*}"
            line="$(trim_line "$line")"
            [ -n "$line" ] || continue
            append_target "$line"
        done < "$targets_file"
    fi

    if [ ${#targets[@]} -eq 0 ]; then
        targets=("claude:.claude/skills" "codex:~/.codex/skills")
    fi

    if [ -n "${SKILL_ATLAS_EXTRA_TARGETS:-}" ]; then
        IFS=',' read -r -a extra_targets <<< "$SKILL_ATLAS_EXTRA_TARGETS"
        for entry in "${extra_targets[@]}"; do
            append_target "$entry"
        done
    fi
}

resolve_target_path() {
    local path="$1"
    if [[ "$path" == ~* ]]; then
        path="${path/#\~/$HOME}"
    fi
    if [[ "$path" = /* ]]; then
        printf '%s' "$path"
    else
        printf '%s' "$project_root/$path"
    fi
}

load_targets() {
    local entry name path resolved
    target_dirs=()
    read_targets
    for entry in "${targets[@]}"; do
        name="${entry%%:*}"
        path="${entry#*:}"
        if [ -z "$name" ] || [ -z "$path" ] || [ "$name" = "$entry" ]; then
            echo "⚠️  跳过无效 target: $entry"
            continue
        fi
        resolved="$(resolve_target_path "$path")"
        target_dirs+=("$name:$resolved")
        mkdir -p "$resolved"
    done
}

link_skill_atlas_root() {
    local entry target_dir
    for entry in "${target_dirs[@]}"; do
        target_dir="${entry#*:}"
        ln -sfn "$skill_atlas_dir" "$target_dir/skill-atlas"
    done
}

link_shared_skills() {
    local skill_dir name entry target_dir
    for skill_dir in "$shared_dir"/*; do
        [ -d "$skill_dir" ] || continue
        [ -f "$skill_dir/SKILL.md" ] || continue
        name="$(basename "$skill_dir")"
        for entry in "${target_dirs[@]}"; do
            target_dir="${entry#*:}"
            ln -sfn "$skill_dir" "$target_dir/$name"
        done
    done
}

list_skills() {
    local scope="${1:-shared}"
    local skill_dir
    case "$scope" in
        shared)
            for skill_dir in "$shared_dir"/*; do
                [ -d "$skill_dir" ] || continue
                [ -f "$skill_dir/SKILL.md" ] || continue
                basename "$skill_dir"
            done
            ;;
        custom)
            for skill_dir in "$custom_dir"/*; do
                [ -d "$skill_dir" ] || continue
                [ -f "$skill_dir/SKILL.md" ] || continue
                basename "$skill_dir"
            done
            ;;
        all)
            echo "shared:"
            list_skills shared
            echo ""
            echo "custom:"
            list_skills custom
            ;;
        *)
            echo "用法: manage.sh list [shared|custom|all]"
            exit 1
            ;;
    esac
}

add_skill() {
    local name="${1:-}"
    local scope="${2:-custom}"
    if [ -z "$name" ]; then
        echo "❌ 需要技能名称"
        echo "用法: manage.sh add <name> [--custom|--shared]"
        exit 1
    fi
    if [ ! -f "$template_path" ]; then
        echo "❌ 模板不存在: $template_path"
        exit 1
    fi
    case "$scope" in
        --shared)
            mkdir -p "$shared_dir/$name"
            cp "$template_path" "$shared_dir/$name/SKILL.md"
            link_skill_atlas_root
            link_shared_skills
            ;;
        --custom|custom)
            mkdir -p "$custom_dir/$name"
            cp "$template_path" "$custom_dir/$name/SKILL.md"
            ;;
        *)
            echo "用法: manage.sh add <name> [--custom|--shared]"
            exit 1
            ;;
    esac
    echo "✅ 新技能 $name 已创建"
}

publish_skill() {
    local name="${1:-}"
    if [ -z "$name" ]; then
        echo "❌ 需要技能名称"
        echo "用法: manage.sh publish <name>"
        exit 1
    fi
    if [ ! -d "$custom_dir/$name" ]; then
        echo "❌ 未找到 custom 技能: $name"
        exit 1
    fi
    if [ -d "$shared_dir/$name" ]; then
        echo "❌ shared 中已存在: $name"
        exit 1
    fi
    mv "$custom_dir/$name" "$shared_dir/$name"
    link_skill_atlas_root
    link_shared_skills
    echo "✅ 已发布到 shared: $name"
}

setup() {
    local target_root="${1:-$project_root}"
    "$skill_atlas_dir/deploy.sh" --project-root "$target_root"
}

doctor() {
    echo "Skill-Atlas: $skill_atlas_dir"
    echo "Project root: $project_root"
    echo "Targets file: $targets_file"
    for entry in "${target_dirs[@]}"; do
        local name target_dir link_target
        name="${entry%%:*}"
        target_dir="${entry#*:}"
        echo "Target [$name]: $target_dir"
        if [ -L "$target_dir/skill-atlas" ]; then
            link_target="$(readlink "$target_dir/skill-atlas")"
            if [ "$link_target" = "$skill_atlas_dir" ]; then
                echo "  ✅ skill-atlas -> $link_target"
            else
                echo "  ⚠️  skill-atlas -> $link_target"
            fi
        else
            echo "  ⚠️  skill-atlas link missing"
        fi
    done
}

load_targets

case "${1:-}" in
    list) list_skills "${2:-shared}" ;;
    add) add_skill "${2:-}" "${3:-custom}" ;;
    publish) publish_skill "${2:-}" ;;
    setup) setup "${2:-}" ;;
    sync) link_skill_atlas_root; link_shared_skills ;;
    test) echo "使用 skill-atlas-test 技能测试系统" ;;
    ui) python "$skill_atlas_dir/tools/skills-ui.py" ;;
    doctor) doctor ;;
    *) echo "manage.sh [list [shared|custom|all]|add <name> [--custom|--shared]|publish <name>|setup [project-root]|sync|test|ui|doctor]" ;;
esac
EOF
chmod +x "$skill_atlas_dir/manage.sh"

cat > "$project_root/manage.sh" << EOF
#!/bin/bash
exec "$skill_atlas_dir/manage.sh" "\$@"
EOF
chmod +x "$project_root/manage.sh"

mkdir -p "$skill_atlas_dir/template"
if [ ! -f "$skill_atlas_dir/template/SKILL.md" ]; then
cat > "$skill_atlas_dir/template/SKILL.md" << 'EOF'
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
fi

echo "✅ 部署完成！"
echo ""
echo "测试命令："
echo "  ./manage.sh list"
echo "  使用 skill-atlas-test 技能测试 Skill-Atlas"
echo "管理命令："
echo "  ./manage.sh add my-skill --custom"
echo "  ./manage.sh publish my-skill"
echo "  ./manage.sh ui"
