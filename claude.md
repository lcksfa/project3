# Claude AI 助手开发指南

## 项目概述

本项目是一个企业级多功能AI助手，采用模块化设计，集成 DeepSeek API，提供聊天、总结、翻译等多种AI功能。

## 开发原则

### 1. 代码质量标准
- **类型安全**: 所有函数必须有类型注解
- **文档完整**: 所有公共函数和类必须有 docstring
- **错误处理**: 完善的异常处理机制
- **测试覆盖**: 单元测试覆盖率 >= 80%
- **代码风格**: 使用 Black + Ruff 统一代码风格

### 2. 架构设计原则
- **单一职责**: 每个模块只负责一个功能领域
- **依赖注入**: 使用依赖注入提高可测试性
- **配置驱动**: 所有配置通过配置文件管理
- **接口抽象**: 定义清晰的接口契约
- **异步优先**: I/O 操作使用异步编程

### 3. 开发流程规范

#### 文件创建流程
1. **永远优先编辑现有文件**，而不是创建新文件
2. 必须先使用 Read 工具了解现有代码结构
3. 创建新文件前必须先规划其在整体架构中的位置
4. 新文件必须包含完整的类型注解和文档

#### 代码审查要点
- 函数和类是否符合单一职责原则
- 是否有适当的错误处理
- 是否有完整的类型注解
- 是否有必要的安全检查
- 是否符合项目的代码风格

#### 测试要求
- 每个服务类必须有对应的单元测试
- API 集成测试必须覆盖主要场景
- UI 组件必须有交互测试
- 性能关键路径必须有基准测试

## 项目结构约定

### 目录结构
```
src/ai_assistant/
├── core/           # 核心基础设施
├── services/       # 业务服务层
├── ui/            # 用户界面层
└── utils/         # 通用工具
```

### 命名规范
- **文件名**: 使用 snake_case (例: `deepseek_client.py`)
- **类名**: 使用 PascalCase (例: `DeepSeekClient`)
- **函数名**: 使用 snake_case (例: `get_chat_response`)
- **常量**: 使用 UPPER_SNAKE_CASE (例: `API_BASE_URL`)
- **私有方法**: 以下划线开头 (例: `_validate_input`)

### 导入规范
```python
# 标准库
import asyncio
from typing import Optional, Dict, Any

# 第三方库
import httpx
from pydantic import BaseModel

# 本地模块
from ai_assistant.core.config import Settings
from ai_assistant.services.deepseek_client import DeepSeekClient
```

## 配置管理规范

### 配置文件结构
```yaml
# config/settings.yaml
app:
  name: "AI Assistant"
  version: "1.0.0"
  debug: false

api:
  deepseek:
    base_url: "https://api.deepseek.com"
    timeout: 30
    max_retries: 3

logging:
  level: "INFO"
  format: "json"
  file: "logs/app.log"
```

### 环境变量
- 敏感信息通过环境变量传递
- 使用 `.env.example` 作为模板
- 生产环境密钥不在代码中出现

## 错误处理规范

### 自定义异常类
```python
# core/exceptions.py
class AIAssistantError(Exception):
    """基础异常类"""
    pass

class APIError(AIAssistantError):
    """API调用异常"""
    pass

class ConfigError(AIAssistantError):
    """配置异常"""
    pass
```

### 错误处理策略
- API 调用失败时自动重试
- 记录详细的错误日志
- 向用户返回友好的错误信息
- 关键错误需要告警通知

## 日志记录规范

### 日志级别
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息记录
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 日志格式
```python
import structlog

logger = structlog.get_logger()

# 使用结构化日志
logger.info("API call started",
           api_name="deepseek",
           endpoint="/v1/chat",
           request_id="req_123")
```

## 测试策略

### 测试类型
1. **单元测试**: 测试单个函数或方法
2. **集成测试**: 测试模块间交互
3. **端到端测试**: 测试完整用户流程
4. **性能测试**: 测试系统性能指标

### 测试命名规范
```python
def test_deepseek_client_send_message_success():
    """测试发送消息成功场景"""
    pass

def test_deepseek_client_send_message_api_error():
    """测试API错误处理"""
    pass
```

### Mock 策略
- 外部 API 调用必须使用 Mock
- 数据库操作使用内存数据库
- 文件系统操作使用临时目录

## 性能要求

### 响应时间
- API 调用响应时间 < 10秒
- UI 操作响应时间 < 2秒
- 页面加载时间 < 5秒

### 资源使用
- 内存使用 < 1GB
- CPU 使用率 < 50%
- 并发支持 >= 10 用户

## 安全要求

### 数据安全
- API 密钥加密存储
- 用户数据本地处理
- 敏感信息日志脱敏
- 定期安全扫描

### 输入验证
- 所有用户输入必须验证
- 防止注入攻击
- 文件上传安全检查
- 请求大小限制

## 部署规范

### Docker 化
- 使用多阶段构建
- 最小化镜像大小
- 非 root 用户运行
- 健康检查配置

### CI/CD 流程
1. 代码提交触发构建
2. 自动运行测试套件
3. 代码质量检查
4. 安全扫描
5. 自动部署到测试环境
6. 手动部署到生产环境

## 监控和维护

### 监控指标
- API 调用成功率
- 响应时间分布
- 错误率统计
- 资源使用情况

### 维护计划
- 每周安全更新
- 每月依赖更新
- 季度性能优化
- 年度架构评估

## 开发工具配置

### 本地开发环境
```bash
# 安装依赖
uv sync

# 运行测试
pytest

# 代码格式化
black .
ruff check .

# 类型检查
mypy .
```

### VSCode 配置
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true
}
```

## 文档要求

### 代码文档
- 每个模块必须有模块级文档
- 公共接口必须有详细说明
- 复杂算法必须有注释解释
- 配置项必须有说明文档

### API 文档
- 使用 OpenAPI 规范
- 包含请求/响应示例
- 错误码说明
- 认证方式说明

## 版本管理

### 语义化版本
- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 分支策略
- `main`: 生产环境代码
- `develop`: 开发环境代码
- `feature/*`: 功能开发分支
- `hotfix/*`: 紧急修复分支

---

**注意**: 本文档是项目的开发指南，所有开发人员必须严格遵守这些规范，确保代码质量和项目的长期可维护性。