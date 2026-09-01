import argparse
import json
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field, field_validator

# ---------- 加载环境变量 ----------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)

# ---------- 日志配置 ----------
LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
LOG_PATH = os.getenv("MCP_LOG_PATH")
if not LOG_PATH:
    LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "mcp_server.log")

os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")],
)
logger = logging.getLogger("local_server")

# ---------- SearXNG URL 安全校验 ----------
_SEARXNG_API_URL = os.getenv("SEARXNG_API_URL", "http://127.0.0.1:7777/search")

_ALLOWED_SEARXNG_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "host.docker.internal",
    "gateway.docker.internal",
    "docker.internal",
}

def _is_allowed_searxng_host(host: str) -> bool:
    if not host:
        return True
    if host in _ALLOWED_SEARXNG_HOSTS:
        return True
    if host.endswith((".internal", ".local", ".docker.internal")):
        return True
    if "." not in host:
        return True
    return False

def _validated_searxng_url(raw_url: str) -> str:
    try:
        parsed = httpx.URL(raw_url)
    except Exception as exc:
        raise ValueError(f"Invalid SEARXNG_API_URL: {raw_url}") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"SEARXNG_API_URL must use http/https: {raw_url}")

    host = (parsed.host or "").lower()
    if host and not _is_allowed_searxng_host(host):
        raise ValueError(f"SEARXNG_API_URL host is not allowed: {host}")

    return str(parsed) if host else "http://127.0.0.1:7777/search"

SEARXNG_API_URL = _validated_searxng_url(_SEARXNG_API_URL)

# ---------- 语言列表 ----------
COMMON_LANGUAGES = {
    "zh", "zh-CN", "zh-Hans", "zh-Hant", "zh-TW",
    "en", "en-US", "en-GB",
    "es", "es-ES", "es-MX",
    "fr", "de", "it", "pt", "pt-BR", "ru", "ja", "ko",
    "ar", "tr", "pl", "nl", "sv", "da", "no", "fi",
}

# ---------- Pydantic 参数验证（保留用于内部校验） ----------
class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, description="搜索查询")
    language: str = Field(default="zh-CN", description="搜索语言")
    safesearch: int = Field(default=1, description="安全搜索等级")
    time_range: str = Field(default="none", description="时间范围过滤")
    page: int = Field(default=1, description="页码，从1开始")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query must be a non-empty string")
        return v.strip()

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in COMMON_LANGUAGES:
            raise ValueError(f"Unsupported language: {v}. Supported: {', '.join(sorted(COMMON_LANGUAGES))}")
        return v

    @field_validator("safesearch")
    @classmethod
    def validate_safesearch(cls, v: int) -> int:
        if v not in (0, 1, 2):
            raise ValueError("safesearch must be one of 0, 1, or 2")
        return v

    @field_validator("time_range")
    @classmethod
    def validate_time_range(cls, v: str) -> str:
        valid_ranges = {"none", "day", "week", "month", "year"}
        if v not in valid_ranges:
            raise ValueError(f"time_range must be one of: {', '.join(valid_ranges)}")
        return v

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page must be >= 1")
        return v

# ---------- 搜索结果清洗 ----------
def _normalize_result(item: dict[str, Any]) -> dict[str, Any]:
    title = (item.get("title") or "").strip()
    url = (item.get("url") or "").strip()
    snippet = (item.get("content") or item.get("snippet") or item.get("description") or "").strip()
    source = (item.get("source") or item.get("engine") or item.get("host") or "").strip()
    published = (item.get("published") or item.get("publishedDate") or item.get("date") or "").strip()

    if not title or not url:
        return {}
    if len(snippet) > 500:
        snippet = snippet[:497].rstrip() + "..."

    result = {
        "title": title,
        "url": url,
        "snippet": snippet,
        "source": source,
        "published": published,
    }
    if not result["source"]:
        result.pop("source")
    if not result["published"]:
        result.pop("published")
    return result

# ---------- 搜索执行 ----------
def _search_searxng(params: SearchParams) -> dict[str, Any]:
    """执行 SearXNG 搜索请求（同步方式，FastMCP 会自动在 executor 中运行同步函数）"""
    try:
        api_params: dict[str, Any] = {
            "q": params.query,
            "language": params.language,
            "safesearch": params.safesearch,
            "pageno": params.page,
            "format": "json",
        }
        if params.time_range != "none":
            api_params["time_range"] = params.time_range

        response = httpx.get(
            SEARXNG_API_URL,
            params=api_params,
            timeout=httpx.Timeout(15.0, connect=10.0),
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        logger.exception("SearXNG request timed out")
        raise RuntimeError(f"SearXNG request timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        logger.exception("SearXNG API returned HTTP error")
        raise RuntimeError(f"SearXNG API returned HTTP {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        logger.exception("SearXNG network error")
        raise RuntimeError(f"SearXNG network error: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        logger.exception("SearXNG response is not valid JSON")
        raise RuntimeError("SearXNG response is not valid JSON") from exc

    results = payload.get("results", [])
    cleaned = []
    for result in results:
        normalized = _normalize_result(result)
        if normalized:
            cleaned.append(normalized)

    return {
        "query": params.query,
        "language": params.language,
        "safesearch": params.safesearch,
        "time_range": params.time_range,
        "page": params.page,
        "total": payload.get("number_of_results", len(cleaned)),
        "results": cleaned,
    }

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SearXNG MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http", "http"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="MCP transport mode (default: stdio)",
    )
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "0.0.0.0"), help="Host for HTTP/SSE transports")
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8000")), help="Port for HTTP/SSE transports")
    parser.add_argument("--sse-path", default=os.getenv("MCP_SSE_PATH", "/sse"), help="SSE endpoint path")
    parser.add_argument(
        "--message-path",
        default=os.getenv("MCP_MESSAGE_PATH", "/messages/"),
        help="SSE message path",
    )
    parser.add_argument(
        "--streamable-http-path",
        default=os.getenv("MCP_STREAMABLE_HTTP_PATH", "/mcp"),
        help="Streamable HTTP endpoint path",
    )
    parser.add_argument(
        "--json-response",
        action="store_true",
        default=os.getenv("MCP_JSON_RESPONSE", "false").lower() == "true",
        help="Use JSON responses for streamable HTTP",
    )
    parser.add_argument(
        "--stateless",
        action="store_true",
        default=os.getenv("MCP_STATELESS", "false").lower() == "true",
        help="Use stateless HTTP mode for streamable HTTP",
    )
    return parser.parse_args()


# ---------- 创建 FastMCP 服务器 ----------
mcp = MCPServer("local-server")

@mcp.tool()
def searxng_search(
    query: str,
    language: str = "zh-CN",
    safesearch: int = 1,
    time_range: str = "none",
    page: int = 1
) -> dict[str, Any]:
    """
    通过 SearXNG 进行网页搜索，返回结构化的结果。

    Args:
        query: 搜索查询（必填）
        language: 搜索语言（ISO 639-1 代码），默认 zh-CN
        safesearch: 安全搜索等级，0=关闭，1=中等，2=严格，默认 1
        time_range: 时间范围过滤，可选 none/day/week/month/year，默认 none
        page: 页码，从 1 开始，默认 1

    Returns:
        包含查询参数、结果总数和结果列表的字典
    """
    # 使用 Pydantic 模型进行严格校验，也支持自动转换和错误提示
    # 但 FastMCP 已经根据类型提示做了基础校验，这里仍保留以保证一致性
    params = SearchParams(
        query=query,
        language=language,
        safesearch=safesearch,
        time_range=time_range,
        page=page,
    )
    logger.info(f"Searching: {params.query} (lang={params.language})")
    result = _search_searxng(params)
    logger.info(f"Found {len(result['results'])} results")
    return result

# ---------- 启动服务器 ----------
if __name__ == "__main__":
    args = _parse_args()
    transport = "streamable-http" if args.transport == "http" else args.transport

    logger.info("local-server starting with %s transport", transport)

    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port,
            sse_path=args.sse_path,
            message_path=args.message_path,
        )
    elif transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            streamable_http_path=args.streamable_http_path,
            json_response=args.json_response,
            stateless_http=args.stateless,
        )
    else:
        raise ValueError(f"Unsupported transport: {transport}")