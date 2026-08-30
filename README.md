# SearXNG MCP

This project packages a SearXNG web search service and a local MCP stdio server together for mainland China usage. It is designed so that after a Git clone, a single script can prepare the runtime, start the services, and expose both the browser search UI and the MCP tool.

## Git-ready project layout

```text
.
├─ .gitignore
├─ .env.example
├─ docker-compose.yml
├─ README.md
├─ bootstrap.sh
├─ create_venv.sh
├─ run_local.sh
├─ logs/
│  └─ .gitkeep
├─ searxng/
│  ├─ settings.yml
│  └─ data/
│     └─ .gitkeep
├─ mcp-clients/
│  ├─ claude_desktop_docker.json
│  └─ local_debug.json
├─ mcp-server/
│  ├─ Dockerfile
│  ├─ main.py
│  ├─ requirements.txt
│  └─ .venv/
└─ .env   # generated locally and ignored by Git
```

## One-click deployment

After cloning the repo, run:

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

The script will:

1. Create or repair the local `.env` from `.env.example`
2. Ensure Docker and Docker Compose are available
3. Create the local Python venv in `mcp-server/.venv`
4. Install Python dependencies
5. Start the `searxng` and `local-server` services with Docker Compose
6. Validate that the browser endpoint and the MCP stdio interface work
7. Print the final access URLs and client configuration guidance

## Environment variables

The repository ships a portable template in `.env.example`.

```env
SEARXNG_API_URL=http://searxng:8080/search
SEARXNG_BIND_PORT=7777
HTTP_PROXY=
HTTPS_PROXY=
MCP_LOG_LEVEL=INFO
MCP_LOG_PATH=./logs/mcp_server.log
VENV_PATH=./mcp-server/.venv
```

This avoids hardcoded local machine paths so the project is safe to commit to Git and redeploy on other machines.

## Local development workflow

### 1) Standard bootstrap

```bash
./bootstrap.sh
```

### 2) Manual local MCP server

```bash
./create_venv.sh
./run_local.sh
```

## Docker workflow

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f searxng
docker compose logs -f server
```

Stop all services:

```bash
docker compose down
```

## Browser and MCP access

### Web UI

Open:

```text
http://localhost:7777
```

### JSON API

```bash
curl "http://localhost:7777/search?q=python&language=zh-CN&format=json&pageno=1"
```

### MCP stdio test

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo","version":"1.0.0"}}}' | ./mcp-server/.venv/bin/python ./mcp-server/main.py
```

For Claude Desktop or Cursor, generate a client config from the project root and point the command to the repository-local venv and main script.

## Git notes

- `.env`, runtime logs, and local virtualenvs are ignored by Git.
- Only source files, Docker config, and example client configs are versioned.
- A clean clone can be bootstrapped with a single script and no host-specific config.

## Safety notes

- Keep the MCP server on stdio only; never expose it as an HTTP endpoint.
- Default engines prefer mainland-direct search sources and avoid unstable overseas providers.
- Use proxy variables only when you explicitly need to access overseas engines.

## Example MCP client configs

After running `./bootstrap.sh`, the repository automatically generates ready-to-use JSON config examples in `mcp-clients/` based on the actual clone path. These files can be imported directly into Claude Desktop, Cursor, or other MCP clients.

### Local stdio config

```json
{
  "mcpServers": {
    "searxng-local": {
      "command": "/absolute/path/to/your/cloned/repo/mcp-server/.venv/bin/python",
      "args": [
        "/absolute/path/to/your/cloned/repo/mcp-server/main.py"
      ],
      "env": {
        "SEARXNG_API_URL": "http://127.0.0.1:7777/search",
        "MCP_LOG_LEVEL": "INFO",
        "MCP_LOG_PATH": "/absolute/path/to/your/cloned/repo/logs/mcp_server.log"
      }
    }
  }
}
```

### Docker stdio config

```json
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
        "MCP_LOG_PATH": "/absolute/path/to/your/cloned/repo/logs/mcp_server.log"
      }
    }
  }
}
```

The generated JSON files in `mcp-clients/` already contain the correct absolute paths for the current machine, so there is no manual editing needed after the bootstrap script runs.
