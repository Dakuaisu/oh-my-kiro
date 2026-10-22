#!/usr/bin/env bash
# Installs oh-my-kiro into ~/.kiro (global agents, prompts, hooks). Re-runnable.
# Usage: ./install.sh [--default] [--trust]
#   --default  make sisyphus the agent plain `kiro-cli` starts with
#   --trust    non-interactive install; accepted for scripted runs (the installer never prompts)
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIRO="${HOME}/.kiro"
SET_DEFAULT=0

for arg in "$@"; do
  case "$arg" in
    --default) SET_DEFAULT=1 ;;
    --trust) ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

command -v kiro-cli >/dev/null || { echo "kiro-cli not found in PATH" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

# Replace the prompt tree so prompts removed upstream (e.g. old keyword modes) do not linger.
rm -rf "${KIRO}/prompts/oh-my-kiro"
mkdir -p "${KIRO}/prompts/oh-my-kiro" "${KIRO}/hooks/oh-my-kiro" "${KIRO}/agents"
cp -R "${SRC}/prompts/." "${KIRO}/prompts/oh-my-kiro/"
cp "${SRC}/hooks/"*.py "${SRC}/generate-agents.py" "${KIRO}/hooks/oh-my-kiro/"
chmod +x "${KIRO}/hooks/oh-my-kiro/"*.py

generated=()
while IFS= read -r line; do generated+=("$line"); done < <(python3 "${KIRO}/hooks/oh-my-kiro/generate-agents.py")

failed=0
for f in "${generated[@]}"; do
  if ! out=$(kiro-cli agent validate --path "$f" 2>&1); then
    echo "invalid: $f" >&2
    echo "$out" >&2
    failed=1
  fi
done
[ "$failed" -eq 0 ] || exit 1
echo "validated ${#generated[@]} agents"

if [ "$SET_DEFAULT" -eq 1 ]; then
  kiro-cli agent set-default sisyphus
fi

echo "oh-my-kiro installed. Start with: kiro-cli chat --agent sisyphus"
[ "$SET_DEFAULT" -eq 1 ] || echo "(run ./install.sh --default to make sisyphus the default agent)"
