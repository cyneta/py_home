#!/bin/bash
# Install git hooks for py_home
# Run this once per deployment (dev machine, Pi, etc.)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "Installing py_home git hooks..."
echo ""

# Install post-merge hook
HOOK_SOURCE="$SCRIPT_DIR/git-hooks/post-merge"
HOOK_DEST="$HOOKS_DIR/post-merge"

if [ ! -f "$HOOK_SOURCE" ]; then
    echo "ERROR: Hook source not found: $HOOK_SOURCE"
    exit 1
fi

# Backup existing hook if present
if [ -f "$HOOK_DEST" ]; then
    BACKUP="$HOOK_DEST.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backing up existing hook: $BACKUP"
    cp "$HOOK_DEST" "$BACKUP"
fi

# Install hook
echo "Installing post-merge hook..."
cp "$HOOK_SOURCE" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

echo ""
echo "✓ Git hooks installed successfully!"
echo ""
echo "The post-merge hook will now:"
echo "  • Detect when config.yaml changes after git pull"
echo "  • Auto-run sync script in preview mode"
echo "  • Show you what keys would be added/removed"
echo "  • Prompt you to apply changes if needed"
echo ""
echo "Test it by running: git pull"
