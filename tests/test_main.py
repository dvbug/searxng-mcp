"""
测试 searxng-mcp 服务器
"""
import json
import sys
from pathlib import Path

import pytest

# 添加 mcp-server 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from main import COMMON_LANGUAGES, SearchParams, _validated_searxng_url


class TestSearchParams:
    """测试 SearchParams 参数验证模型"""

    def test_valid_params(self):
        """测试有效的参数"""
        params = SearchParams(
            query="python",
            language="en",
            safesearch=1,
            time_range="week",
            page=1,
        )
        assert params.query == "python"
        assert params.language == "en"
        assert params.safesearch == 1
        assert params.time_range == "week"
        assert params.page == 1

    def test_default_params(self):
        """测试默认参数"""
        params = SearchParams(query="test")
        assert params.query == "test"
        assert params.language == "zh-CN"
        assert params.safesearch == 1
        assert params.time_range == "none"
        assert params.page == 1

    def test_valid_docker_service_host(self):
        """测试 Docker 内部服务主机名允许访问"""
        assert _validated_searxng_url("http://searxng:8080/search") == "http://searxng:8080/search"
        assert _validated_searxng_url("http://host.docker.internal:8080/search") == "http://host.docker.internal:8080/search"

    def test_invalid_public_host(self):
        """测试公共外部域名被拒绝"""
        with pytest.raises(ValueError, match="host is not allowed"):
            _validated_searxng_url("https://example.com/search")

    def test_invalid_query_empty(self):
        """测试空查询"""
        with pytest.raises(ValueError):
            SearchParams(query="")

    def test_invalid_query_whitespace(self):
        """测试空白查询"""
        with pytest.raises(ValueError):
            SearchParams(query="   ")

    def test_invalid_language(self):
        """测试无效语言代码"""
        with pytest.raises(ValueError, match="Unsupported language"):
            SearchParams(query="test", language="invalid-lang")

    def test_valid_languages(self):
        """测试所有支持的语言代码"""
        for lang in list(COMMON_LANGUAGES)[:5]:  # 测试前 5 个
            params = SearchParams(query="test", language=lang)
            assert params.language == lang

    def test_invalid_safesearch_value(self):
        """测试无效的安全搜索值"""
        with pytest.raises(ValueError, match="safesearch must be"):
            SearchParams(query="test", safesearch=3)

    def test_valid_safesearch_values(self):
        """测试有效的安全搜索值"""
        for value in [0, 1, 2]:
            params = SearchParams(query="test", safesearch=value)
            assert params.safesearch == value

    def test_invalid_time_range(self):
        """测试无效的时间范围"""
        with pytest.raises(ValueError, match="time_range must be"):
            SearchParams(query="test", time_range="invalid")

    def test_valid_time_ranges(self):
        """测试有效的时间范围"""
        for time_range in ["none", "day", "week", "month", "year"]:
            params = SearchParams(query="test", time_range=time_range)
            assert params.time_range == time_range

    def test_invalid_page_zero(self):
        """测试页码为 0"""
        with pytest.raises(ValueError, match="page must be >= 1"):
            SearchParams(query="test", page=0)

    def test_invalid_page_negative(self):
        """测试负数页码"""
        with pytest.raises(ValueError, match="page must be >= 1"):
            SearchParams(query="test", page=-1)

    def test_valid_page_values(self):
        """测试有效的页码"""
        for page in [1, 2, 10, 100]:
            params = SearchParams(query="test", page=page)
            assert params.page == page

    def test_params_model_json_schema(self):
        """测试参数模型的 JSON Schema"""
        schema = SearchParams.model_json_schema()
        assert "properties" in schema
        assert "required" in schema
        assert schema["required"] == ["query"]
        assert "query" in schema["properties"]
        assert "language" in schema["properties"]
        assert "safesearch" in schema["properties"]


class TestCommonLanguages:
    """测试支持的语言列表"""

    def test_languages_not_empty(self):
        """测试语言列表非空"""
        assert len(COMMON_LANGUAGES) > 0

    def test_chinese_supported(self):
        """测试中文支持"""
        assert "zh-CN" in COMMON_LANGUAGES
        assert "zh" in COMMON_LANGUAGES

    def test_english_supported(self):
        """测试英文支持"""
        assert "en" in COMMON_LANGUAGES
        assert "en-US" in COMMON_LANGUAGES
