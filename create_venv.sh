#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
VENV_PATH="${VENV_PATH:-$REPO_ROOT/mcp-server/.venv}"
REQUIREMENTS_FILE="$REPO_ROOT/mcp-server/requirements.txt"

if [[ ! -d "$REPO_ROOT/mcp-server" ]]; then
  echo "[ERROR] mcp-server directory not found: $REPO_ROOT/mcp-server" >&2
  exit 1
fi

if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  echo "[ERROR] requirements.txt not found: $REQUIREMENTS_FILE" >&2
  exit 1
fi

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  source "$REPO_ROOT/.env"
  set +a
fi

# Clear inherited proxy vars that may point to invalid local services and break pip.
for var in HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy FTP_PROXY ftp_proxy NO_PROXY no_proxy; do
  unset "$var" || true
done

if [[ -d "$VENV_PATH" ]]; then
  echo "[INFO] Virtual environment already exists: $VENV_PATH"
else
  echo "[INFO] Creating virtual environment at $VENV_PATH"
  python3 -m venv "$VENV_PATH"
fi

"$VENV_PATH/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_PATH/bin/python" -m pip install -r "$REQUIREMENTS_FILE"

cat <<EOF
[INFO] Local development environment is ready.
[INFO] Use the venv Python explicitly:
[INFO]   $VENV_PATH/bin/python
[INFO] Run the MCP server with:
[INFO]   $REPO_ROOT/run_local.sh
EOF
