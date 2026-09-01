#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [command]

Commands:
  docker        Start the full stack via Docker Compose (default)
  local         Start the MCP server in the local virtual environment
  stop          Stop the Docker Compose stack
  logs          Tail Docker Compose logs
  check         Validate environment and print the planned deployment mode
  help          Show this help message

Examples:
  ./deploy.sh
  ./deploy.sh docker
  ./deploy.sh local
  ./deploy.sh stop
  ./deploy.sh logs
  ./deploy.sh check
EOF
}

ensure_env_file() {
  if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
      echo "[INFO] .env not found. Copying from .env.example"
      cp .env.example .env
    else
      echo "[ERROR] .env.example not found" >&2
      exit 1
    fi
  fi
}

ensure_venv() {
  if [[ ! -d "$SCRIPT_DIR/mcp-server/.venv" ]]; then
    echo "[INFO] Creating Python virtual environment"
    ./create_venv.sh
  fi
}

run_docker_deploy() {
  ensure_env_file
  mkdir -p "$SCRIPT_DIR/logs"
  echo "[INFO] Launching Docker Compose stack"
  docker compose up -d --build
  echo "[INFO] Stack is running"
  echo "[INFO] View logs: docker compose logs -f"
}

run_local_deploy() {
  ensure_env_file
  ensure_venv
  mkdir -p "$SCRIPT_DIR/logs"
  echo "[INFO] Starting MCP server in local mode"
  exec ./run_local.sh
}

stop_docker_stack() {
  echo "[INFO] Stopping Docker Compose stack"
  docker compose down
}

show_logs() {
  docker compose logs -f --tail=200
}

check_deploy() {
  ensure_env_file
  echo "[INFO] Project root: $SCRIPT_DIR"
  echo "[INFO] Docker available: $(command -v docker >/dev/null && echo yes || echo no)"
  echo "[INFO] Python venv exists: $(if [[ -d "$SCRIPT_DIR/mcp-server/.venv" ]]; then echo yes; else echo no; fi)"
  echo "[INFO] Deployment mode: ${1:-docker}"
}

COMMAND="${1:-docker}"
shift || true

case "$COMMAND" in
  docker)
    run_docker_deploy
    ;;
  local)
    run_local_deploy
    ;;
  stop)
    stop_docker_stack
    ;;
  logs)
    show_logs
    ;;
  check)
    check_deploy "${1:-docker}"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    echo "[ERROR] Unknown command: $COMMAND" >&2
    usage >&2
    exit 1
    ;;
 esac
