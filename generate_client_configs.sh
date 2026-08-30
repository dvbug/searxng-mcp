#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIR="$SCRIPT_DIR/mcp-clients"
mkdir -p "$CLIENT_DIR"

LOCAL_CONFIG="$CLIENT_DIR/local_debug.json"
DOCKER_CONFIG="$CLIENT_DIR/claude_desktop_docker.json"

cat > "$LOCAL_CONFIG" <<EOF
{
  "mcpServers": {
    "searxng-local": {
      "command": "$SCRIPT_DIR/mcp-server/.venv/bin/python",
      "args": [
        "$SCRIPT_DIR/mcp-server/main.py"
      ],
      "env": {
        "SEARXNG_API_URL": "http://127.0.0.1:7777/search",
        "MCP_LOG_LEVEL": "INFO",
        "MCP_LOG_PATH": "$SCRIPT_DIR/logs/mcp_server.log"
      }
    }
  }
}
EOF

cat > "$DOCKER_CONFIG" <<EOF
{
  "mcpServers": {
    "searxng": {
      "command": "docker",
      "args": [
        "compose",
        "run",
        "--rm",
        "-i",
        "local-server"
      ],
      "env": {
        "SEARXNG_API_URL": "http://searxng:8080/search",
        "MCP_LOG_LEVEL": "INFO",
        "MCP_LOG_PATH": "$SCRIPT_DIR/logs/mcp_server.log"
      }
    }
  }
}
EOF

echo "[INFO] Generated MCP client configs in $CLIENT_DIR"

echo "[INFO] Local: $LOCAL_CONFIG"
echo "[INFO] Docker: $DOCKER_CONFIG"
