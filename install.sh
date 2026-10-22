#!/usr/bin/env bash
# Installs oh-my-kiro into ~/.kiro (global agents, prompts, hooks). Re-runnable.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIRO="${HOME}/.kiro"

command -v kiro-cli >/dev/null || { echo "kiro-cli not found in PATH" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

mkdir -p "${KIRO}/prompts/oh-my-kiro" "${KIRO}/hooks/oh-my-kiro" "${KIRO}/agents"
cp -R "${SRC}/prompts/." "${KIRO}/prompts/oh-my-kiro/"
cp "${SRC}/hooks/"*.py "${SRC}/generate-agents.py" "${KIRO}/hooks/oh-my-kiro/"
chmod +x "${KIRO}/hooks/oh-my-kiro/"*.py

python3 "${KIRO}/hooks/oh-my-kiro/generate-agents.py" >/dev/null

failed=0
for f in "${KIRO}"/agents/{sisyphus,atlas,prometheus,oracle,librarian,explore,multimodal-looker,metis,momus,sisyphus-junior,cat-*}.json; do
  if ! kiro-cli agent validate --path "$f" >/dev/null 2>&1; then
    echo "invalid: $f" >&2
    failed=1
  fi
done
[ "$failed" -eq 0 ] || exit 1

if [ "${1:-}" = "--default" ]; then
  kiro-cli agent set-default sisyphus
fi

echo "oh-my-kiro installed. Start with: kiro-cli chat --agent sisyphus"
echo "(run ./install.sh --default to make sisyphus the default agent)"
