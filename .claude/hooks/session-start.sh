#!/bin/bash
# SessionStart hook for abb-offline-coder (Claude Code on the web).
#
# Goals:
#   1) Install the Python env so `pytest` and `ruff` work out of the box.
#   2) Persist useful env vars for the session.
#   3) Defuse the Ollama AMX-backend segfault seen on cloud/VM CPUs that
#      advertise AMX without usable tile state (see docs/TROUBLESHOOTING.md).
#   4) Start `ollama serve` if Ollama is installed.
#
# Idempotent and non-interactive. Web-only (no-op locally unless
# CLAUDE_CODE_REMOTE=true, which the validation step sets explicitly).
set -euo pipefail

# Run only in Claude Code on the web (remote) environments.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$PROJECT_DIR"

PY="${PYTHON:-python3}"

# 1) Python venv + dependencies (cached after first run; idempotent).
if [ ! -d ".venv" ]; then
  "$PY" -m venv .venv
fi
# Note: don't force-upgrade setuptools here -- torch pins setuptools<82,
# and the editable build pulls its own isolated build deps anyway.
./.venv/bin/python -m pip install --quiet --upgrade pip wheel
./.venv/bin/pip install --quiet -e ".[dev]"

# 2) Persist env vars for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PATH=\"$PROJECT_DIR/.venv/bin:\$PATH\""
    echo "export ABB_AGENT_LLM_TIMEOUT_SECONDS=900"  # CPU inference is slow
    echo "export OLLAMA_FLASH_ATTENTION=0"
    echo "export OLLAMA_KEEP_ALIVE=-1"               # keep model resident
  } >> "$CLAUDE_ENV_FILE"
fi

# 3) Defuse the AMX-backend Ollama segfault (only if that backend is present).
OLLAMA_LIB="/usr/local/lib/ollama"
AMX_BACKEND="$OLLAMA_LIB/libggml-cpu-sapphirerapids.so"
if [ -f "$AMX_BACKEND" ]; then
  mkdir -p "$OLLAMA_LIB/_disabled_backends"
  mv -f "$AMX_BACKEND" "$OLLAMA_LIB/_disabled_backends/" 2>/dev/null || true
  echo "[hook] disabled AMX GGML backend to avoid llama-server segfault"
fi

# 4) Start Ollama if installed and not already serving.
if command -v ollama >/dev/null 2>&1; then
  if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    OLLAMA_FLASH_ATTENTION=0 OLLAMA_KEEP_ALIVE=-1 \
      nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
    echo "[hook] started ollama serve"
  fi
fi

echo "[hook] abb-offline-coder ready: .venv installed, env vars set."
