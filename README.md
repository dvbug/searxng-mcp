# SearXNG MCP Server

一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 的 SearXNG 搜索集成服务。项目当前以 `main2.py` 为主入口，支持 `stdio` / `sse` / `streamable-http` 三种传输方式，并通过 SearXNG 提供结构化搜索能力。

## 入口文件说明

### `mcp-server/main.py`
- 这是早期/兼容版本的 MCP 服务实现。
- 采用标准输入输出（STDIO）模式，适合直接接入传统 MCP 客户端或本地命令行工具。
- 这是一个更“原始”的 JSON-RPC 处理方式，主要用于兼容旧流程。

### `mcp-server/main2.py`
- 这是当前默认、推荐使用的实现。
- 采用 `MCPServer` / FastMCP 风格，支持更现代的传输配置。
- 当前支持三种模式：
  - `stdio`
  - `sse`
  - `streamable-http`
- Docker 和本地启动脚本都已指向 `main2.py`。

> 结论：当前项目实际运行入口是 `main2.py`，而不是 `main.py`。

## 项目结构

```text
searxng-mcp/
├── pyproject.toml              # Python 依赖与项目配置
├── mcp-server/
│   ├── main.py                 # 旧版/兼容版 MCP 入口
│   ├── main2.py                # 当前主入口，支持多传输
│   ├── Dockerfile              # Docker 镜像定义
│   └── .venv                   # 本地 Python 虚拟环境
├── searxng/
│   ├── settings.yml            # SearXNG 配置文件，挂载到 Docker 容器内
│   └── data/                   # SearXNG 缓存/数据目录
├── mcp/
│   └── searxng-mcp.yaml        # MCP client/server 配置示例
├── docker-compose.yml          # Docker 编排配置
├── .env.example                # 环境变量模板
├── .env                        # 本地实际配置（未跟踪）
├── run_local.sh                # 本地运行脚本（默认启动 main2.py）
├── create_venv.sh              # 虚拟环境初始化脚本
├── deploy.sh                   # 一键部署脚本
├── logs/                       # 日志目录
├── tests/                      # 测试代码
└── README.md                   # 项目说明
```

## 快速开始

### 方式一：Docker 运行（推荐）

```bash
cp .env.example .env

docker compose up -d

docker compose logs -f local-server
```

当前 `local-server` 会按 `streamable-http` 模式启动，服务地址为：

```text
http://localhost:17777/mcp
```

这个地址对应的是 `main2.py` 启动时的 `streamable-http` 路径 `/mcp`。

### 方式二：本地开发运行

```bash
./create_venv.sh
./run_local.sh
```

本地脚本会读取 `.env` 中的 `MCP_TRANSPORT`，并调用 `main2.py`。

## 环境变量

示例配置如下：

```env
SEARXNG_API_URL=http://127.0.0.1:7777/search
SEARXNG_BIND_PORT=7777
HTTP_PROXY=
HTTPS_PROXY=

MCP_LOG_LEVEL=INFO
MCP_LOG_PATH=./logs/mcp_server.log
VENV_PATH=./mcp-server/.venv

MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_SSE_PATH=/sse
MCP_MESSAGE_PATH=/messages/
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_JSON_RESPONSE=false
MCP_STATELESS=true
```

说明：
- `MCP_TRANSPORT=http` 在代码中会被映射为 `streamable-http`
- `MCP_STREAMABLE_HTTP_PATH=/mcp` 与外部访问路径保持一致
- Docker 中暴露端口是 `17777:8000`，因此外部访问为 `http://localhost:17777/mcp`

## 传输方式

### 1) stdio

```bash
python mcp-server/main2.py --transport stdio
```

适合本地桌面客户端、IDE 集成、命令行工具等。

### 2) SSE

```bash
python mcp-server/main2.py --transport sse --host 0.0.0.0 --port 8000 --sse-path /sse --message-path /messages/
```

访问地址：

```text
http://localhost:8000/sse
```

### 3) streamable-http

```bash
python mcp-server/main2.py --transport streamable-http --host 0.0.0.0 --port 8000 --streamable-http-path /mcp
```

访问地址：

```text
http://localhost:8000/mcp
```

## Tool：`searxng_search`

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 搜索关键词 |
| `language` | string | `zh-CN` | 语言，例如 `zh-CN`, `en`, `ja` |
| `safesearch` | integer | `1` | 安全搜索等级：`0`, `1`, `2` |
| `time_range` | string | `none` | 时间范围：`none`, `day`, `week`, `month`, `year` |
| `page` | integer | `1` | 页码，从 `1` 开始 |

### 返回示例

```json
{
  "query": "Python tutorial",
  "language": "zh-CN",
  "safesearch": 1,
  "time_range": "none",
  "page": 1,
  "total": 42,
  "results": [
    {
      "title": "Python Tutorial",
      "url": "https://example.com/python-tutorial",
      "snippet": "A concise guide to Python programming.",
      "source": "bing"
    }
  ]
}
```

## SearXNG 配置挂载说明

SearXNG 的配置是通过 Docker bind mount 方式挂载到容器的：

```yaml
./searxng/settings.yml:/etc/searxng/settings.yml:ro
```

因此：
- 修改宿主机上的 [searxng/settings.yml](searxng/settings.yml) 即可生效
- 只需重启 `searxng` 容器，不需要重新构建镜像或重新发布

## 安全和兼容性改进

当前代码中已经包含这些关键修正：

- 允许 Docker 内部主机名和本地网络地址访问 SearXNG
- `time_range="none"` 时不会再被错误地传给 SearXNG，避免 `HTTP 400`
- `main2.py` 对 `stdio`, `sse`, `streamable-http` 做了统一启动逻辑
- SearXNG API URL 校验支持本地 / Docker / 内网场景

## 故障排查

### 1) SearXNG 不可访问

```bash
curl -sS http://127.0.0.1:7777/search?q=test&format=json
```

如果失败，先检查：

```bash
docker compose logs searxng
```

### 2) MCP 服务未启动

```bash
docker compose logs -f local-server
cat ./logs/mcp_server.log
```

### 3) 端口不通

```bash
curl -I http://localhost:17777/mcp
```

如果返回 `200`，说明 Streamable HTTP 服务正常。

## 依赖

- Python 3.12+
- httpx
- pydantic
- python-dotenv
- mcp

## 许可证

MIT
