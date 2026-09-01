"""
工具调用和请求处理测试
测试 searxng_search 工具的调用和参数处理
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# 添加 mcp-server 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from main import _handle_request, _mcp_error, _normalize_result, _tool_result


class TestToolCall:
    """测试工具调用请求"""

    def test_valid_search_call(self, mcp_search_request, mock_httpx_client):
        """测试有效的搜索调用"""
        with patch("main.httpx.get", return_value=mock_httpx_client):
            response = _handle_request(mcp_search_request)

            assert response["jsonrpc"] == "2.0"
            assert response["id"] == mcp_search_request["id"]
            assert "result" in response
            assert "content" in response["result"]

    def test_search_with_minimal_params(self, mock_httpx_client):
        """测试最少参数的搜索"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "python"},
            },
        }
        with patch("main.httpx.get", return_value=mock_httpx_client):
            response = _handle_request(request)
            assert "result" in response
            assert response["id"] == 1

    def test_search_with_chinese_query(self, mock_httpx_client):
        """测试中文查询"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {
                    "query": "机器学习",
                    "language": "zh-CN",
                },
            },
        }
        with patch("main.httpx.get", return_value=mock_httpx_client):
            response = _handle_request(request)
            assert "result" in response

    def test_search_result_structure(self, mcp_search_request, mock_httpx_client):
        """测试搜索结果结构"""
        with patch("main.httpx.get", return_value=mock_httpx_client):
            response = _handle_request(mcp_search_request)

            result = response["result"]
            assert "content" in result
            assert isinstance(result["content"], list)
            assert len(result["content"]) > 0
            assert result["content"][0]["type"] == "text"

            # 检查结构化内容
            assert "structuredContent" in result
            structured = result["structuredContent"]
            assert "query" in structured
            assert "language" in structured
            assert "results" in structured
            assert "total" in structured

    def test_search_result_content_is_json_string(self, mcp_search_request, mock_httpx_client):
        """测试搜索结果内容是有效的 JSON 字符串"""
        with patch("main.httpx.get", return_value=mock_httpx_client):
            response = _handle_request(mcp_search_request)

            content_text = response["result"]["content"][0]["text"]
            parsed = json.loads(content_text)

            assert "query" in parsed
            assert "results" in parsed

    def test_search_with_different_languages(self, mock_httpx_client):
        """测试不同语言的搜索"""
        languages = ["en", "es", "fr", "de", "ja", "zh-CN"]
        for lang in languages:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "searxng_search",
                    "arguments": {
                        "query": "test",
                        "language": lang,
                    },
                },
            }
            with patch("main.httpx.get", return_value=mock_httpx_client):
                response = _handle_request(request)
                assert "result" in response
                assert response["id"] == 1

    def test_search_with_different_safesearch_levels(self, mock_httpx_client):
        """测试不同的安全搜索等级"""
        for level in [0, 1, 2]:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "searxng_search",
                    "arguments": {
                        "query": "test",
                        "safesearch": level,
                    },
                },
            }
            with patch("main.httpx.get", return_value=mock_httpx_client):
                response = _handle_request(request)
                assert "result" in response

    def test_search_with_different_time_ranges(self, mock_httpx_client):
        """测试不同的时间范围"""
        for time_range in ["none", "day", "week", "month", "year"]:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "searxng_search",
                    "arguments": {
                        "query": "test",
                        "time_range": time_range,
                    },
                },
            }
            with patch("main.httpx.get", return_value=mock_httpx_client) as mock_get:
                response = _handle_request(request)
                assert "result" in response
                call_params = mock_get.call_args.kwargs["params"]
                if time_range == "none":
                    assert "time_range" not in call_params
                else:
                    assert call_params["time_range"] == time_range

    def test_search_with_pagination(self, mock_httpx_client):
        """测试分页功能"""
        for page in [1, 2, 5, 10]:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "searxng_search",
                    "arguments": {
                        "query": "test",
                        "page": page,
                    },
                },
            }
            with patch("main.httpx.get", return_value=mock_httpx_client):
                response = _handle_request(request)
                assert "result" in response

    def test_search_preserves_request_id(self, mock_httpx_client):
        """测试搜索保留请求 ID"""
        for req_id in [1, 999, "search-id"]:
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/call",
                "params": {
                    "name": "searxng_search",
                    "arguments": {"query": "test"},
                },
            }
            with patch("main.httpx.get", return_value=mock_httpx_client):
                response = _handle_request(request)
                assert response["id"] == req_id


class TestToolCallErrors:
    """测试工具调用错误处理"""

    def test_missing_query_parameter(self):
        """测试缺少 query 参数"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {},
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"
        assert response["id"] == 1

    def test_empty_query_parameter(self):
        """测试空 query 参数"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": ""},
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"

    def test_whitespace_query_parameter(self):
        """测试空白 query 参数"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {"query": "   "},
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"

    def test_invalid_language_parameter(self):
        """测试无效的 language 参数"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {
                    "query": "test",
                    "language": "invalid-language-code",
                },
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"

    def test_invalid_safesearch_parameter(self):
        """测试无效的 safesearch 参数"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {
                    "query": "test",
                    "safesearch": 99,
                },
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"

    def test_invalid_time_range_parameter(self):
        """测试无效的 time_range 参数"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {
                    "query": "test",
                    "time_range": "invalid-range",
                },
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"

    def test_invalid_page_parameter_zero(self):
        """测试无效的 page 参数（0）"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {
                    "query": "test",
                    "page": 0,
                },
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"

    def test_invalid_page_parameter_negative(self):
        """测试无效的 page 参数（负数）"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "searxng_search",
                "arguments": {
                    "query": "test",
                    "page": -5,
                },
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32602"


class TestResultNormalization:
    """测试结果规范化"""

    def test_normalize_result_with_all_fields(self):
        """测试包含所有字段的结果规范化"""
        result = {
            "title": "Python.org",
            "url": "https://www.python.org",
            "content": "The official Python website",
            "engine": "google",
            "published": "2024-01-01",
        }
        normalized = _normalize_result(result)

        assert normalized["title"] == "Python.org"
        assert normalized["url"] == "https://www.python.org"
        assert normalized["snippet"] == "The official Python website"
        assert normalized["source"] == "google"
        assert normalized["published"] == "2024-01-01"

    def test_normalize_result_with_snippet_field(self):
        """测试使用 snippet 字段的结果规范化"""
        result = {
            "title": "Example",
            "url": "https://example.com",
            "snippet": "Example snippet",
            "engine": "bing",
        }
        normalized = _normalize_result(result)

        assert normalized["snippet"] == "Example snippet"

    def test_normalize_result_missing_fields(self):
        """测试缺少字段的结果规范化"""
        result = {
            "title": "Title only",
            "url": "https://example.com",
        }
        normalized = _normalize_result(result)

        assert "source" not in normalized
        assert "published" not in normalized
        assert "snippet" in normalized and normalized["snippet"] == ""

    def test_normalize_result_missing_title_or_url(self):
        """测试缺少标题或 URL 的结果应该被过滤"""
        # 缺少标题
        result1 = {"url": "https://example.com", "content": "content"}
        assert _normalize_result(result1) == {}

        # 缺少 URL
        result2 = {"title": "Title", "content": "content"}
        assert _normalize_result(result2) == {}

    def test_normalize_result_truncate_long_snippet(self):
        """测试长摘要被截断"""
        long_content = "a" * 600
        result = {
            "title": "Title",
            "url": "https://example.com",
            "content": long_content,
        }
        normalized = _normalize_result(result)

        assert len(normalized["snippet"]) <= 500
        assert normalized["snippet"].endswith("...")

    def test_normalize_result_strip_whitespace(self):
        """测试修剪空白"""
        result = {
            "title": "  Title with spaces  ",
            "url": "  https://example.com  ",
            "content": "  Content with spaces  ",
            "source": "  engine  ",
        }
        normalized = _normalize_result(result)

        assert normalized["title"] == "Title with spaces"
        assert normalized["url"] == "https://example.com"
        assert normalized["snippet"] == "Content with spaces"
        assert normalized["source"] == "engine"
