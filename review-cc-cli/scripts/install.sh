#!/bin/bash
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Deploying settings-review.json..."
mkdir -p ~/.claude
cp "$SKILL_DIR/config/settings-review.json" ~/.claude/settings-review.json

echo "==> Deploying rubrics..."
mkdir -p ~/.claude/review-rubrics
cp "$SKILL_DIR/rubrics/"*.md ~/.claude/review-rubrics/

echo ""
echo "✅ review-cc-cli installed!"
echo "   Skill directory: $SKILL_DIR"
echo "   Run /review in any Claude session."
