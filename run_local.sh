#!/usr/bin/env bash
set -euo pipefail

# run_local.sh
# 作用：本地开发模式下启动 MCP 标准输入输出服务，确保使用项目内虚拟环境，
# 不依赖系统 Python，并读取项目根目录的 .env 配置。

# 1) 获取当前脚本所在目录，并把它当成项目根目录。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# 2) 读取项目内虚拟环境路径；如果环境变量 VENV_PATH 未显式设置，默认使用:
#    mcp-server/.venv
VENV_PATH="${VENV_PATH:-$REPO_ROOT/mcp-server/.venv}"
APP_DIR="$REPO_ROOT/mcp-server"
MAIN_FILE="$APP_DIR/main.py"

# 3) 校验 MCP 入口脚本是否存在，避免误运行导致空指针或找不到文件。
if [[ ! -f "$MAIN_FILE" ]]; then
  echo "[ERROR] MCP server entrypoint not found: $MAIN_FILE" >&2
  exit 1
fi

# 4) 校验项目内部虚拟环境是否已创建；如果未创建，提醒调用 create_venv.sh。
if [[ ! -d "$VENV_PATH" ]]; then
  echo "[ERROR] Virtual environment not found: $VENV_PATH" >&2
  echo "[INFO] Run: $REPO_ROOT/create_venv.sh" >&2
  exit 1
fi

# 5) 确认虚拟环境中的 Python 可执行文件存在且可用，防止引用错误文件。
if [[ ! -x "$VENV_PATH/bin/python" ]]; then
  echo "[ERROR] Invalid Python interpreter in virtual environment: $VENV_PATH/bin/python" >&2
  exit 1
fi

# 6) 读取项目根目录 .env 中的环境变量，确保日志路径、SearXNG API 地址等皆可被脚本使用。
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  source "$REPO_ROOT/.env"
  set +a
fi

# 7) 保障日志目录存在，并设置日志输出路径；这里遵循环境变量控制，避免硬编码。
mkdir -p "$REPO_ROOT/logs"
export MCP_LOG_PATH="${MCP_LOG_PATH:-$REPO_ROOT/logs/mcp_server.log}"

# 8) 用项目内的 venv Python 直接启动 MCP 服务，保证是 stdio 模式，不启动 HTTP 服务。
exec "$VENV_PATH/bin/python" "$MAIN_FILE"
