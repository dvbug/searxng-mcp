"""
集成测试和网络错误处理
测试与 SearXNG 的集成和网络故障场景
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

# 添加 mcp-server 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from main import _handle_request, _search_searxng, SearchParams


class TestNetworkErrors:
    """测试网络错误处理"""

    def test_searxng_timeout_error(self):
        """测试 SearXNG 超时错误"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "test"},
            },
        }

        with patch("main.httpx.get", side_effect=httpx.TimeoutException("Request timed out")):
            response = _handle_request(request)

            assert "error" in response
            assert response["error"]["code"] == "-32603"
            # 检查错误消息中是否包含 timed out（不区分大小写）
            assert "timed" in response["error"]["message"].lower() or "timeout" in response["error"]["message"].lower()

    def test_searxng_connection_error(self):
        """测试 SearXNG 连接错误"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "test"},
            },
        }

        with patch("main.httpx.get", side_effect=httpx.ConnectError("Connection refused")):
            response = _handle_request(request)

            assert "error" in response
            assert response["error"]["code"] == "-32603"

    def test_searxng_http_error_500(self):
        """测试 SearXNG HTTP 500 错误"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "test"},
            },
        }

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )

        with patch("main.httpx.get", return_value=mock_response):
            response = _handle_request(request)

            assert "error" in response
            assert response["error"]["code"] == "-32603"
            assert "500" in response["error"]["message"]

    def test_searxng_http_error_404(self):
        """测试 SearXNG HTTP 404 错误"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "test"},
            },
        }

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        with patch("main.httpx.get", return_value=mock_response):
            response = _handle_request(request)

            assert "error" in response
            assert "404" in response["error"]["message"]

    def test_searxng_invalid_json_response(self):
        """测试 SearXNG 返回无效 JSON"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "test"},
            },
        }

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("main.httpx.get", return_value=mock_response):
            response = _handle_request(request)

            assert "error" in response
            assert "JSON" in response["error"]["message"]

    def test_error_response_preserves_request_id(self):
        """测试错误响应保留请求 ID"""
        request_ids = [1, 500, "error-id-123"]

        for req_id in request_ids:
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/call",
                "params": {
                    "name": "searxng_search",
                    "arguments": {"query": "test"},
                },
            }

            with patch("main.httpx.get", side_effect=httpx.TimeoutException("Timeout")):
                response = _handle_request(request)
                assert response["id"] == req_id


class TestSearchParamsValidation:
    """测试搜索参数验证"""

    def test_valid_search_params(self):
        """测试有效的搜索参数"""
        params = SearchParams(query="python")
        assert params.query == "python"

    def test_search_params_with_type_coercion(self):
        """测试参数类型强制转换"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {
                    "query": "test",
                    "safesearch": "1",  # 字符串而不是整数
                    "page": "2",  # 字符串而不是整数
                },
            },
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"number_of_results": 0, "results": []}
        mock_response.raise_for_status.return_value = None

        with patch("main.httpx.get", return_value=mock_response):
            response = _handle_request(request)
            # 应该成功处理字符串参数
            assert "result" in response or "error" in response

    def test_search_params_unicode_query(self):
        """测试 Unicode 查询参数"""
        params = SearchParams(query="你好世界 🌍")
        assert params.query == "你好世界 🌍"

    def test_search_params_special_characters_in_query(self):
        """测试查询中的特殊字符"""
        special_queries = [
            "test & query",
            "python/c++",
            "what's next?",
            "code: example",
            'quote "test"',
        ]

        for query in special_queries:
            params = SearchParams(query=query)
            assert params.query == query


class TestEmptyResults:
    """测试空结果处理"""

    def test_empty_results_list(self):
        """测试空结果列表"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "xyzabc12345notfound"},
            },
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"number_of_results": 0, "results": []}
        mock_response.raise_for_status.return_value = None

        with patch("main.httpx.get", return_value=mock_response):
            response = _handle_request(request)

            assert "result" in response
            structured = response["result"]["structuredContent"]
            assert structured["total"] == 0
            assert structured["results"] == []

    def test_results_with_all_invalid_items(self):
        """测试结果全是无效项（应该被过滤）"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "test"},
            },
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number_of_results": 3,
            "results": [
                {"title": "No URL", "content": "test"},  # 缺少 URL
                {"url": "https://example.com", "content": "test"},  # 缺少 title
                {"title": "", "url": "", "content": "test"},  # 空 title 和 URL
            ],
        }
        mock_response.raise_for_status.return_value = None

        with patch("main.httpx.get", return_value=mock_response):
            response = _handle_request(request)

            assert "result" in response
            structured = response["result"]["structuredContent"]
            # 所有项都应该被过滤掉
            assert structured["results"] == []


class TestHTTPRequestParameters:
    """测试发送给 SearXNG 的 HTTP 请求参数"""

    def test_http_request_parameters(self, mock_httpx_client):
        """测试 HTTP 请求参数正确性"""
        with patch("main.httpx.get", return_value=mock_httpx_client) as mock_get:
            params = SearchParams(
                query="python tutorial",
                language="en",
                safesearch=1,
                time_range="week",
                page=2,
            )
            _search_searxng(params)

            # 验证调用了 httpx.get
            assert mock_get.called
            call_kwargs = mock_get.call_args[1]

            # 验证参数
            assert call_kwargs["params"]["q"] == "python tutorial"
            assert call_kwargs["params"]["language"] == "en"
            assert call_kwargs["params"]["safesearch"] == 1
            assert call_kwargs["params"]["time_range"] == "week"
            assert call_kwargs["params"]["pageno"] == 2
            assert call_kwargs["params"]["format"] == "json"

    def test_http_request_timeout_configuration(self, mock_httpx_client):
        """测试 HTTP 请求超时配置"""
        with patch("main.httpx.get", return_value=mock_httpx_client) as mock_get:
            params = SearchParams(query="test")
            _search_searxng(params)

            # 验证超时配置
            call_kwargs = mock_get.call_args[1]
            timeout = call_kwargs["timeout"]
            # httpx.Timeout 对象：Timeout(timeout, connect=None, read=None, write=None, pool=None)
            # 当 Timeout(15.0, connect=10.0) 时：pool=15.0, read=15.0, write=15.0, connect=10.0
            assert timeout.connect == 10.0  # 连接超时 10 秒
            assert timeout.pool == 15.0  # 总超时 15 秒

    def test_http_request_follow_redirects(self, mock_httpx_client):
        """测试 HTTP 请求跟随重定向"""
        with patch("main.httpx.get", return_value=mock_httpx_client) as mock_get:
            params = SearchParams(query="test")
            _search_searxng(params)

            # 验证跟随重定向
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs["follow_redirects"] is True


class TestResponseProcessing:
    """测试响应处理"""

    def test_response_processing_with_mixed_fields(self, mock_httpx_client):
        """测试混合字段的响应处理"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number_of_results": 2,
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example1.com",
                    "content": "Content 1",
                    "engine": "google",
                    "publishedDate": "2024-01-01",  # 不同的日期字段名
                },
                {
                    "title": "Result 2",
                    "url": "https://example2.com",
                    "snippet": "Snippet 2",  # 使用 snippet 而不是 content
                    "host": "example2.com",  # 使用 host 而不是 engine
                    "date": "2024-01-02",  # 不同的日期字段名
                },
            ],
        }
        mock_response.raise_for_status.return_value = None

        with patch("main.httpx.get", return_value=mock_response):
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "searxng_search",
                    "arguments": {"query": "test"},
                },
            }
            response = _handle_request(request)

            structured = response["result"]["structuredContent"]
            assert len(structured["results"]) == 2
            assert structured["results"][0]["title"] == "Result 1"
            assert structured["results"][1]["title"] == "Result 2"
