# 贡献指南

感谢您对 SearXNG MCP 项目的关注！本指南将帮助您了解如何贡献代码。

## 开发设置

### 1. 克隆仓库并创建虚拟环境

```bash
git clone <repository-url>
cd searxng-mcp
./create_venv.sh
source mcp-server/.venv/bin/activate
```

### 2. 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 3. 运行测试

```bash
pytest
pytest --cov=mcp_server  # 生成覆盖率报告
```

## 代码风格

### 格式化代码

```bash
black mcp-server/
ruff check mcp-server/ --fix
```

### 类型检查

```bash
mypy mcp-server/
```

## 提交更改

### 1. 创建新分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 遵循提交规范

使用清晰的提交消息：
- `feat:` - 新功能
- `fix:` - 错误修复
- `docs:` - 文档更新
- `refactor:` - 代码重构
- `test:` - 测试相关
- `chore:` - 构建/依赖更新

例子：
```
feat: add query result filtering

- Add filter_by_domain parameter to search tool
- Implement domain filtering logic
- Add unit tests for filtering
```

### 3. 推送分支并创建 Pull Request

```bash
git push origin feature/your-feature-name
```

## 测试要求

所有新功能必须包含相应的测试：

```bash
# 新增特性测试示例
def test_new_feature():
    """Test description"""
    result = new_feature("input")
    assert result == "expected"
```

## 文档更新

- 更新 README.md 中的相关部分
- 为新的公共 API 添加文档字符串
- 更新 CHANGELOG 或 CHANGELOG.md

## 问题报告

创建 Issue 时，请包括：
- 清晰的问题描述
- 复现步骤
- 预期行为 vs 实际行为
- 环境信息（Python 版本、OS 等）
- 相关日志输出

## 性能注意事项

- 避免同步阻塞操作
- 优化 API 请求超时时间
- 考虑结果缓存策略

## 安全考虑

- 不提交敏感信息（密钥、令牌等）
- 验证所有用户输入
- 定期更新依赖项

## 问题？

- 查看现有 Issues 和 PRs
- 提交新 Issue 或 Discussion
- 联系项目维护者

谢谢您的贡献！🎉
