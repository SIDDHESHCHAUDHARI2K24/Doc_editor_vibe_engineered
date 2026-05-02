#!/usr/bin/env bash
# install_skills.sh — idempotent installer for obra/superpowers skills
# Fetches upstream and copies required skills into .opencode/skills/
set -euo pipefail

FORCE=false
BRANCH="main"
UPSTREAM_URL="https://github.com/obra/superpowers.git"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force) FORCE=true; shift ;;
        --branch) BRANCH="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$REPO_ROOT/tools"
SUPERPOWERS_DIR="$TOOLS_DIR/superpowers"
SKILLS_DEST="$REPO_ROOT/.opencode/skills"

REQUIRED_SKILLS=(
    "using-superpowers"
    "brainstorming"
    "writing-plans"
    "executing-plans"
    "test-driven-development"
    "requesting-code-review"
    "receiving-code-review"
    "verification-before-completion"
    "using-git-worktrees"
    "finishing-a-development-branch"
    "subagent-driven-development"
    "dispatching-parallel-agents"
    "systematic-debugging"
)

echo "=== Superpowers Skills Installer ==="

# Ensure directories exist
mkdir -p "$TOOLS_DIR"
mkdir -p "$SKILLS_DEST"

# Clone or update superpowers repo
if [[ -d "$SUPERPOWERS_DIR/.git" ]]; then
    echo "[SKIP] superpowers repo already exists at $SUPERPOWERS_DIR"
    if $FORCE; then
        echo "[UPDATE] Fetching latest from upstream..."
        git -C "$SUPERPOWERS_DIR" fetch origin "$BRANCH"
        git -C "$SUPERPOWERS_DIR" checkout "$BRANCH"
        git -C "$SUPERPOWERS_DIR" reset --hard "origin/$BRANCH"
    fi
else
    echo "[CLONE] Cloning obra/superpowers into $SUPERPOWERS_DIR..."
    git clone --depth 1 --branch "$BRANCH" "$UPSTREAM_URL" "$SUPERPOWERS_DIR"
fi

# Copy each required skill
INSTALLED=0
SKIPPED=0

for SKILL in "${REQUIRED_SKILLS[@]}"; do
    SOURCE_DIR="$SUPERPOWERS_DIR/skills/$SKILL"
    DEST_DIR="$SKILLS_DEST/$SKILL"
    SOURCE_SKILL_MD="$SOURCE_DIR/SKILL.md"

    if [[ ! -f "$SOURCE_SKILL_MD" ]]; then
        echo "[WARN] Skill '$SKILL' not found in upstream — skipping"
        continue
    fi

    if [[ -f "$DEST_DIR/SKILL.md" ]] && ! $FORCE; then
        echo "[SKIP] Skill '$SKILL' already installed"
        ((SKIPPED++)) || true
        continue
    fi

    echo "[INSTALL] Skill: $SKILL"
    rm -rf "$DEST_DIR"
    cp -r "$SOURCE_DIR" "$DEST_DIR"
    ((INSTALLED++)) || true
done

echo ""
echo "=== Done ==="
echo "  Installed: $INSTALLED skill(s)"
echo "  Skipped:   $SKIPPED skill(s) (already present)"
echo "  Destination: $SKILLS_DEST"
echo ""
echo "To verify, ask your agent: 'Tell me about your superpowers'"
echo ""
echo "[HINT] Add this to your opencode.json for auto-loading:"
echo '  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]'
