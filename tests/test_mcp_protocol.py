"""
MCP 协议实现测试
测试 MCP 协议的各个方法实现
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# 添加 mcp-server 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from main import _handle_request


class TestMCPInitialize:
    """测试 MCP 初始化方法"""

    def test_initialize_response_structure(self, mcp_initialize_request):
        """测试初始化响应结构"""
        response = _handle_request(mcp_initialize_request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == mcp_initialize_request["id"]
        assert "result" in response
        assert "error" not in response

    def test_initialize_protocol_version(self, mcp_initialize_request):
        """测试协议版本"""
        response = _handle_request(mcp_initialize_request)
        result = response["result"]

        assert result["protocolVersion"] == "2024-11-05"

    def test_initialize_server_info(self, mcp_initialize_request):
        """测试服务器信息"""
        response = _handle_request(mcp_initialize_request)
        result = response["result"]

        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "local-server"
        assert "version" in result["serverInfo"]

    def test_initialize_capabilities(self, mcp_initialize_request):
        """测试服务器能力"""
        response = _handle_request(mcp_initialize_request)
        result = response["result"]

        assert "capabilities" in result
        assert "tools" in result["capabilities"]

    def test_initialize_preserves_request_id(self):
        """测试初始化保留请求 ID"""
        for req_id in [1, 100, "test-id", None]:
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "initialize",
                "params": {},
            }
            response = _handle_request(request)
            assert response["id"] == req_id


class TestMCPToolsList:
    """测试 MCP 工具列表方法"""

    def test_tools_list_response_structure(self, mcp_tools_list_request):
        """测试工具列表响应结构"""
        response = _handle_request(mcp_tools_list_request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == mcp_tools_list_request["id"]
        assert "result" in response
        assert "tools" in response["result"]

    def test_tools_list_contains_searxng_search(self, mcp_tools_list_request):
        """测试工具列表包含 searxng_search"""
        response = _handle_request(mcp_tools_list_request)
        tools = response["result"]["tools"]

        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "searxng_search" in tool_names

    def test_searxng_search_tool_definition(self, mcp_tools_list_request):
        """测试 searxng_search 工具定义"""
        response = _handle_request(mcp_tools_list_request)
        tools = response["result"]["tools"]

        searxng_tool = next((t for t in tools if t["name"] == "searxng_search"), None)
        assert searxng_tool is not None

        # 检查工具属性
        assert "description" in searxng_tool
        assert "inputSchema" in searxng_tool

        # 检查输入 Schema
        schema = searxng_tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert "query" in schema["required"]

    def test_tool_schema_query_property(self, mcp_tools_list_request):
        """测试工具 Schema 中的 query 属性"""
        response = _handle_request(mcp_tools_list_request)
        tools = response["result"]["tools"]
        searxng_tool = next((t for t in tools if t["name"] == "searxng_search"), None)

        schema = searxng_tool["inputSchema"]
        query_prop = schema["properties"]["query"]

        assert query_prop["type"] == "string"
        assert "description" in query_prop

    def test_tool_schema_language_enum(self, mcp_tools_list_request):
        """测试工具 Schema 中的 language 枚举"""
        response = _handle_request(mcp_tools_list_request)
        tools = response["result"]["tools"]
        searxng_tool = next((t for t in tools if t["name"] == "searxng_search"), None)

        schema = searxng_tool["inputSchema"]
        language_prop = schema["properties"]["language"]

        assert "enum" in language_prop
        assert "zh-CN" in language_prop["enum"]
        assert "en" in language_prop["enum"]
        assert language_prop["default"] == "zh-CN"

    def test_tool_schema_safesearch_enum(self, mcp_tools_list_request):
        """测试工具 Schema 中的 safesearch 枚举"""
        response = _handle_request(mcp_tools_list_request)
        tools = response["result"]["tools"]
        searxng_tool = next((t for t in tools if t["name"] == "searxng_search"), None)

        schema = searxng_tool["inputSchema"]
        safesearch_prop = schema["properties"]["safesearch"]

        assert safesearch_prop["enum"] == [0, 1, 2]
        assert safesearch_prop["default"] == 1

    def test_tool_schema_time_range_enum(self, mcp_tools_list_request):
        """测试工具 Schema 中的 time_range 枚举"""
        response = _handle_request(mcp_tools_list_request)
        tools = response["result"]["tools"]
        searxng_tool = next((t for t in tools if t["name"] == "searxng_search"), None)

        schema = searxng_tool["inputSchema"]
        time_range_prop = schema["properties"]["time_range"]

        assert time_range_prop["enum"] == ["none", "day", "week", "month", "year"]
        assert time_range_prop["default"] == "none"

    def test_tool_schema_additional_properties(self, mcp_tools_list_request):
        """测试工具 Schema 不允许额外属性"""
        response = _handle_request(mcp_tools_list_request)
        tools = response["result"]["tools"]
        searxng_tool = next((t for t in tools if t["name"] == "searxng_search"), None)

        schema = searxng_tool["inputSchema"]
        assert schema["additionalProperties"] is False

    def test_tools_list_preserves_request_id(self):
        """测试工具列表保留请求 ID"""
        for req_id in [1, 999, "list-tools-id"]:
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/list",
            }
            response = _handle_request(request)
            assert response["id"] == req_id


class TestMCPPing:
    """测试 MCP Ping 方法"""

    def test_ping_response_structure(self, mcp_ping_request):
        """测试 Ping 响应结构"""
        response = _handle_request(mcp_ping_request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == mcp_ping_request["id"]
        assert "result" in response
        assert response["result"]["ok"] is True

    def test_ping_preserves_request_id(self):
        """测试 Ping 保留请求 ID"""
        for req_id in [1, 42, "ping-id"]:
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "ping",
            }
            response = _handle_request(request)
            assert response["id"] == req_id


class TestMCPErrorHandling:
    """测试 MCP 错误处理"""

    def test_unknown_method_error(self):
        """测试未知方法错误"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown_method",
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32601"
        assert "Method not found" in response["error"]["message"]
        assert response["id"] == 1

    def test_invalid_tool_name_error(self):
        """测试无效工具名称错误"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {},
            },
        }
        response = _handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == "-32601"
        assert "Unknown tool" in response["error"]["message"]
        assert response["id"] == 1

    def test_error_preserves_request_id(self):
        """测试错误响应保留请求 ID"""
        for req_id in [1, 500, "error-id"]:
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "invalid_method",
            }
            response = _handle_request(request)
            assert response["id"] == req_id
            assert "error" in response

    def test_missing_params_not_crash(self):
        """测试缺少 params 不会崩溃"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        }
        response = _handle_request(request)
        assert "result" in response or "error" in response
