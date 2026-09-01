"""
MCP 协议测试 fixtures 和通用工具
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# 添加 mcp-server 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from main import SearchParams


@pytest.fixture
def mcp_initialize_request() -> Dict[str, Any]:
    """初始化请求 fixture"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }


@pytest.fixture
def mcp_tools_list_request() -> Dict[str, Any]:
    """工具列表请求 fixture"""
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }


@pytest.fixture
def mcp_search_request() -> Dict[str, Any]:
    """搜索工具调用请求 fixture"""
    return {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "searxng_search",
            "arguments": {
                "query": "python programming",
                "language": "en",
                "safesearch": 1,
                "time_range": "none",
                "page": 1,
            },
        },
    }


@pytest.fixture
def mcp_ping_request() -> Dict[str, Any]:
    """Ping 请求 fixture"""
    return {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "ping",
    }


@pytest.fixture
def mock_searxng_response() -> Dict[str, Any]:
    """模拟 SearXNG 搜索响应"""
    return {
        "number_of_results": 100,
        "results": [
            {
                "title": "Python.org",
                "url": "https://www.python.org",
                "content": "The official home of the Python Programming Language",
                "engine": "google",
                "published": "2024-01-01",
            },
            {
                "title": "Real Python",
                "url": "https://realpython.com",
                "snippet": "Learn Python programming with in-depth tutorials",
                "engine": "bing",
            },
            {
                "title": "Example without title",
                "url": "",  # 无效，应该被过滤
                "content": "This should be filtered out",
                "engine": "test",
            },
            {
                "title": "Missing snippet",
                "url": "https://example.com",
                "engine": "test",
            },
        ],
    }


@pytest.fixture
def mock_httpx_client(mock_searxng_response):
    """模拟 httpx 客户端"""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_searxng_response
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def valid_search_params() -> SearchParams:
    """有效的搜索参数"""
    return SearchParams(
        query="test query",
        language="en",
        safesearch=1,
        time_range="week",
        page=1,
    )


@pytest.fixture
def chinese_search_params() -> SearchParams:
    """中文搜索参数"""
    return SearchParams(
        query="机器学习",
        language="zh-CN",
        safesearch=1,
        time_range="month",
        page=1,
    )
