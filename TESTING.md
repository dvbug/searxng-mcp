# 测试指南

本文档介绍如何运行和编写项目的单元测试和集成测试。

## 测试套件概览

### 测试文件结构

```
tests/
├── __init__.py                # 包初始化
├── conftest.py               # pytest fixtures 和通用配置
├── run_tests.py              # 测试运行脚本
├── test_main.py              # SearchParams 参数验证测试
├── test_mcp_protocol.py      # MCP 协议实现测试
├── test_request_handling.py  # 请求处理和工具调用测试
└── test_integration.py       # 集成测试和网络错误处理
```

### 测试覆盖范围

| 测试文件 | 覆盖范围 | 测试数量 |
|---------|---------|--------|
| `test_main.py` | 参数验证、语言支持 | 15+ |
| `test_mcp_protocol.py` | 初始化、工具列表、Ping、错误处理 | 20+ |
| `test_request_handling.py` | 工具调用、结果规范化、参数验证 | 30+ |
| `test_integration.py` | 网络错误、集成场景、HTTP 参数 | 20+ |
| **总计** | - | **85+** |

## 快速开始

### 安装测试依赖

```bash
# 安装项目及开发依赖
pip install -e ".[dev]"
```

### 运行所有测试

```bash
# 方法 1：使用 pytest
pytest

# 方法 2：使用测试脚本
python tests/run_tests.py --all

# 方法 3：生成覆盖率报告
pytest --cov=mcp_server --cov-report=html
```

### 运行特定测试

```bash
# 运行特定测试文件
pytest tests/test_main.py
pytest tests/test_mcp_protocol.py

# 运行特定测试类
pytest tests/test_main.py::TestSearchParams
pytest tests/test_mcp_protocol.py::TestMCPInitialize

# 运行特定测试方法
pytest tests/test_main.py::TestSearchParams::test_valid_params
pytest tests/test_mcp_protocol.py::TestMCPInitialize::test_initialize_response_structure

# 运行匹配关键词的测试
pytest -k "test_invalid_language"
pytest -k "test_search" -v
```

### 生成详细报告

```bash
# 显示测试覆盖率
pytest --cov=mcp_server --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=mcp_server --cov-report=html
# 打开 htmlcov/index.html 查看报告

# 显示所有 print 输出
pytest -s

# 显示最慢的 10 个测试
pytest --durations=10

# 详细的失败信息
pytest -vv --tb=long
```

## 测试类别说明

### 1. 参数验证测试 (`test_main.py`)

验证 `SearchParams` 数据模型的参数验证功能。

**包括：**
- ✓ 有效参数接受
- ✓ 默认值设置
- ✓ 无效语言代码拒绝
- ✓ 无效 safesearch 值拒绝
- ✓ 无效 time_range 拒绝
- ✓ 无效 page 值拒绝

```bash
# 运行参数验证测试
pytest tests/test_main.py -v
```

### 2. MCP 协议测试 (`test_mcp_protocol.py`)

测试 MCP 协议的各个方法实现。

**包括：**
- ✓ `initialize` 方法（初始化）
- ✓ `tools/list` 方法（工具列表）
- ✓ `ping` 方法（心跳检测）
- ✓ 错误响应处理
- ✓ 请求 ID 正确传递

```bash
# 运行 MCP 协议测试
pytest tests/test_mcp_protocol.py -v

# 只运行初始化测试
pytest tests/test_mcp_protocol.py::TestMCPInitialize -v

# 只运行错误处理测试
pytest tests/test_mcp_protocol.py::TestMCPErrorHandling -v
```

### 3. 请求处理测试 (`test_request_handling.py`)

测试工具调用和搜索结果处理。

**包括：**
- ✓ 有效搜索调用
- ✓ 不同语言搜索
- ✓ 结果规范化
- ✓ 参数错误处理
- ✓ 请求 ID 传递

```bash
# 运行请求处理测试
pytest tests/test_request_handling.py -v

# 只运行工具调用测试
pytest tests/test_request_handling.py::TestToolCall -v

# 只运行结果规范化测试
pytest tests/test_request_handling.py::TestResultNormalization -v
```

### 4. 集成测试 (`test_integration.py`)

测试与 SearXNG 的集成和网络故障场景。

**包括：**
- ✓ 网络超时错误
- ✓ 连接错误
- ✓ HTTP 错误处理
- ✓ 无效 JSON 响应
- ✓ 空结果处理
- ✓ HTTP 请求参数验证

```bash
# 运行集成测试
pytest tests/test_integration.py -v

# 只运行网络错误测试
pytest tests/test_integration.py::TestNetworkErrors -v

# 只运行参数验证测试
pytest tests/test_integration.py::TestHTTPRequestParameters -v
```

## Fixtures 说明

### MCP 请求 Fixtures (`conftest.py`)

- `mcp_initialize_request` - 初始化请求
- `mcp_tools_list_request` - 工具列表请求
- `mcp_search_request` - 搜索请求
- `mcp_ping_request` - Ping 请求

### 数据 Fixtures

- `mock_searxng_response` - 模拟 SearXNG 响应
- `mock_httpx_client` - 模拟 httpx 客户端
- `valid_search_params` - 有效搜索参数
- `chinese_search_params` - 中文搜索参数

## 编写新测试

### 测试文件命名规则

- 文件名以 `test_` 开头
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头

### 基本测试模板

```python
import pytest
from main import some_function

class TestSomeFeature:
    """测试某个功能"""
    
    def test_valid_case(self):
        """测试有效情况"""
        result = some_function("valid_input")
        assert result == "expected_output"
    
    def test_invalid_case(self):
        """测试无效情况"""
        with pytest.raises(ValueError):
            some_function("invalid_input")
    
    def test_with_fixture(self, mcp_search_request):
        """使用 fixture 的测试"""
        # mcp_search_request 是来自 conftest.py 的 fixture
        assert mcp_search_request["method"] == "tools/call"
```

### 使用 Mock 和 Patch

```python
from unittest.mock import patch, MagicMock

def test_with_mock(self, mock_httpx_client):
    """使用 mock 的测试"""
    with patch("main.httpx.get", return_value=mock_httpx_client):
        result = some_function()
        assert result is not None
```

## 持续集成

### GitHub Actions 配置示例

创建 `.github/workflows/tests.yml`：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12']
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: pytest --cov=mcp_server --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 测试最佳实践

1. **单一职责** - 每个测试只测试一个功能
2. **清晰的名称** - 测试名称应该描述测试的内容
3. **使用 Fixtures** - 复用常见的测试数据和设置
4. **模拟外部服务** - 不依赖真实的 SearXNG 服务
5. **错误情况** - 同时测试正常和异常情况
6. **文档字符串** - 为复杂测试添加文档说明

## 常见问题

### Q: 如何只运行快速测试？
```bash
pytest -m "not slow"
```

### Q: 如何调试测试？
```bash
pytest -s -vv --tb=long tests/test_file.py::TestClass::test_method
```

### Q: 测试覆盖率不足怎么办？
```bash
# 查看未覆盖的代码行
pytest --cov=mcp_server --cov-report=term-missing

# 生成 HTML 报告
pytest --cov=mcp_server --cov-report=html
# 在 htmlcov/index.html 中查看详细信息
```

### Q: 如何跳过某些测试？
```bash
# 跳过特定测试
pytest --deselect tests/test_file.py::test_name

# 跳过包含某个关键词的测试
pytest -k "not slow"
```

## 性能测试

```bash
# 显示测试执行时间
pytest --durations=10

# 只运行快速测试
pytest -m "not slow"
```

## 输出示例

```
tests/test_main.py::TestSearchParams::test_valid_params PASSED
tests/test_main.py::TestSearchParams::test_invalid_language PASSED
tests/test_mcp_protocol.py::TestMCPInitialize::test_initialize_response_structure PASSED
tests/test_mcp_protocol.py::TestMCPToolsList::test_searxng_search_tool_definition PASSED
tests/test_request_handling.py::TestToolCall::test_valid_search_call PASSED
tests/test_integration.py::TestNetworkErrors::test_searxng_timeout_error PASSED

========================= 85 passed in 0.42s =========================
```

## 下一步

- 添加性能基准测试
- 集成真实的 SearXNG 实例进行 E2E 测试
- 生成测试覆盖率徽章
- 配置 CI/CD 流水线
