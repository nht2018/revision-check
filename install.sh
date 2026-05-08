#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
TARGET="$CODEX_HOME/skills/rev-check"

mkdir -p "$CODEX_HOME/skills"
rm -rf "$TARGET"
cp -R "$ROOT/skills/rev-check" "$TARGET"

echo "Installed rev-check skill to $TARGET"
echo "Use it by starting a request with: \$rev-check"
