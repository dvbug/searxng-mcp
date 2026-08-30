import json
import logging
import os
import sys
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)

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

SEARXNG_API_URL = os.getenv("SEARXNG_API_URL", "http://searxng:8080/search")

_ALLOWED_SEARXNG_HOSTS = {"searxng", "localhost", "127.0.0.1", "::1"}


def _validated_searxng_url(raw_url: str) -> str:
    try:
        parsed = httpx.URL(raw_url)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Invalid SEARXNG_API_URL: {raw_url}") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"SEARXNG_API_URL must use http/https: {raw_url}")

    host = (parsed.host or "").lower()
    if host and host not in _ALLOWED_SEARXNG_HOSTS and not host.endswith(".internal"):
        raise ValueError(f"SEARXNG_API_URL host is not allowed: {host}")

    if host in {"localhost", "127.0.0.1", "::1"}:
        return str(parsed)
    return f"http://searxng:8080/search"


SEARXNG_API_URL = _validated_searxng_url(SEARXNG_API_URL)


def _read_json_line() -> dict[str, Any] | None:
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        if not line.strip():
            return None
        return json.loads(line)
    except json.JSONDecodeError as exc:
        logger.warning("Received invalid JSON from stdin: %s", exc)
        return None


def _write_json(data: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _mcp_error(code: str, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if data is not None:
        payload["error"]["data"] = data
    return payload


def _normalize_result(item: dict[str, Any]) -> dict[str, Any]:
    title = (item.get("title") or "").strip()
    url = (item.get("url") or "").strip()
    snippet = (item.get("content") or item.get("snippet") or item.get("description") or "").strip()
    source = item.get("source") or item.get("engine") or item.get("host") or ""
    published = item.get("published") or item.get("publishedDate") or item.get("date") or ""

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


def _search_searxng(query: str, language: str = "zh-CN", safesearch: int = 1, time_range: str = "none", page: int = 1) -> dict[str, Any]:
    if page < 1:
        raise ValueError("page must be >= 1")
    if safesearch not in (0, 1, 2):
        raise ValueError("safesearch must be one of 0, 1, or 2")
    if time_range not in {"none", "day", "week", "month", "year"}:
        raise ValueError("time_range must be one of: none, day, week, month, year")

    params = {
        "q": query,
        "language": language,
        "safesearch": safesearch,
        "time_range": time_range,
        "pageno": page,
        "format": "json",
    }

    try:
        response = httpx.get(
            SEARXNG_API_URL,
            params=params,
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
        "query": query,
        "language": language,
        "safesearch": safesearch,
        "time_range": time_range,
        "page": page,
        "total": payload.get("number_of_results", len(cleaned)),
        "results": cleaned,
    }


def _tool_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": None,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2),
                }
            ],
            "structuredContent": result,
        },
    }


def _handle_request(request: dict[str, Any]) -> dict[str, Any]:
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "local-server",
                    "version": "1.0.0",
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "searxng_search",
                        "description": "Search the web via SearXNG and return structured, cleaned results.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query."},
                                "language": {"type": "string", "description": "Search language, default zh-CN.", "default": "zh-CN"},
                                "safesearch": {"type": "integer", "enum": [0, 1, 2], "description": "Safe search level.", "default": 1},
                                "time_range": {"type": "string", "enum": ["none", "day", "week", "month", "year"], "description": "Time filter for results.", "default": "none"},
                                "page": {"type": "integer", "description": "Page number starting from 1.", "default": 1},
                            },
                            "required": ["query"],
                            "additionalProperties": False,
                        },
                    }
                ],
            },
        }

    if method == "tools/call":
        tool_name = (params.get("name") or "").strip()
        arguments = params.get("arguments") or {}
        if tool_name != "searxng_search":
            return _mcp_error("-32601", f"Unknown tool: {tool_name}")

        try:
            query = arguments.get("query")
            if not isinstance(query, str) or not query.strip():
                raise ValueError("query must be a non-empty string")
            result = _search_searxng(
                query=query.strip(),
                language=arguments.get("language", "zh-CN"),
                safesearch=int(arguments.get("safesearch", 1)),
                time_range=arguments.get("time_range", "none"),
                page=int(arguments.get("page", 1)),
            )
            return _tool_result(result)
        except ValueError as exc:
            logger.warning("Invalid tool arguments: %s", exc)
            return _mcp_error("-32602", str(exc), {"tool": tool_name, "arguments": arguments})
        except RuntimeError as exc:
            logger.exception("Tool execution failed")
            return _mcp_error("-32603", str(exc), {"tool": tool_name, "arguments": arguments})
        except Exception as exc:  # pragma: no cover - safeguard for unexpected issues
            logger.exception("Unexpected tool failure")
            return _mcp_error("-32603", f"Unexpected error: {exc}", {"tool": tool_name, "arguments": arguments})

    if method == "ping":
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {"ok": True}}

    return _mcp_error("-32601", f"Method not found: {method}")


def main() -> None:
    logger.info("local-server starting; SearXNG_API_URL=%s", SEARXNG_API_URL)
    while True:
        try:
            request = _read_json_line()
            if request is None:
                logger.info("stdin closed; exiting cleanly")
                break
            if not isinstance(request, dict):
                _write_json(_mcp_error("-32600", "Request must be a JSON object"))
                continue
            response = _handle_request(request)
            _write_json(response)
        except BrokenPipeError:
            logger.warning("stdin closed; exiting cleanly")
            break
        except KeyboardInterrupt:
            logger.info("Received interrupt; shutting down")
            break
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("Unhandled MCP dispatch error")
            _write_json(_mcp_error("-32603", f"Unhandled server error: {exc}"))


if __name__ == "__main__":
    main()
