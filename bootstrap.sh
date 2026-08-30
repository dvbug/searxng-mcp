#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
ENV_FILE="$REPO_ROOT/.env"
ENV_EXAMPLE="$REPO_ROOT/.env.example"
VENV_PATH="${VENV_PATH:-$REPO_ROOT/mcp-server/.venv}"

if [[ ! -f "$ENV_EXAMPLE" ]]; then
  echo "[ERROR] Missing template file: $ENV_EXAMPLE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[INFO] Creating local .env from template"
  cp "$ENV_EXAMPLE" "$ENV_FILE"
fi

set -a
source "$ENV_FILE"
set +a

mkdir -p "$REPO_ROOT/logs" "$REPO_ROOT/searxng/data"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] Docker is required but not installed." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[ERROR] Docker Compose is required but not available." >&2
  exit 1
fi

if [[ ! -d "$VENV_PATH" ]]; then
  echo "[INFO] Creating project-local Python virtual environment"
  python3 -m venv "$VENV_PATH"
fi

"$VENV_PATH/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_PATH/bin/python" -m pip install -r "$REPO_ROOT/mcp-server/requirements.txt"

if [[ -x "$REPO_ROOT/generate_client_configs.sh" ]]; then
  echo "[INFO] Generating MCP client config examples for this repository"
  "$REPO_ROOT/generate_client_configs.sh"
fi

cd "$REPO_ROOT"

echo "[INFO] Starting SearXNG and MCP services..."
docker compose up -d --build

echo "[INFO] Waiting for health checks..."
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${SEARXNG_BIND_PORT:-7777}/search?q=hello&format=json" >/tmp/mcp_searxng_probe.json 2>/dev/null; then
    echo "[OK] SearXNG is responding at http://localhost:${SEARXNG_BIND_PORT:-7777}"
    break
  fi
  sleep 2
done

if ! curl -fsS "http://127.0.0.1:${SEARXNG_BIND_PORT:-7777}/search?q=hello&format=json" >/dev/null 2>&1; then
  echo "[WARN] SearXNG may still be starting. Check docker compose logs -f searxng"
fi

echo ""
echo "========================================="
echo "Deployment ready"
echo "========================================="
echo "Browser URL: http://localhost:${SEARXNG_BIND_PORT:-7777}"
echo "Search API:  http://localhost:${SEARXNG_BIND_PORT:-7777}/search"
echo "MCP stdio:   run ./run_local.sh or use the Docker client config"
echo "========================================="
echo ""

echo "[INFO] You can use the local MCP directly with:"
echo "    $VENV_PATH/bin/python $REPO_ROOT/mcp-server/main.py"

echo "[INFO] Or use Docker Compose as the MCP stdio transport:"
echo "    docker compose run --rm -i local-server"
