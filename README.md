# 多功能AI助手

一个企业级的Python AI助手应用，集成DeepSeek API，提供聊天、文本总结、翻译等多种AI功能。

## ✨ 功能特性

- 🤖 **智能聊天**: 基于DeepSeek大模型的多轮对话
- 📝 **文本总结**: 智能提取和总结长文本内容
- 🌍 **多语言翻译**: 支持多种语言之间的互译
- 🖥️ **现代化界面**: 基于Streamlit的直观Web界面
- ⚙️ **配置驱动**: 灵活的配置管理系统
- 📊 **日志监控**: 完整的操作日志记录
- 🔒 **企业级安全**: 遵循安全最佳实践
- 🚀 **容器化部署**: 支持Docker一键部署

## 🏗️ 技术架构

### 技术栈
- **后端**: Python 3.11+
- **Web框架**: Streamlit
- **AI服务**: DeepSeek API
- **异步处理**: httpx, asyncio
- **配置管理**: Pydantic + YAML
- **日志系统**: structlog
- **测试框架**: pytest
- **代码质量**: Black, Ruff, MyPy

### 架构设计
```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                        │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │Chat Service │ │Summary Svc  │ │Translate Svc│      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│                    Core Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │Config Mgmt  │ │Logger System│ │DeepSeek API │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- uv (推荐的包管理器)
- Docker (可选，用于容器化部署)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/ai-assistant.git
cd ai-assistant
```

2. **安装依赖**
```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements/dev.txt
```

3. **配置环境**
```bash
# 复制配置文件模板
cp config/settings.example.yaml config/settings.yaml
cp .env.example .env

# 编辑配置文件，填入你的API密钥
# 编辑 .env 文件，添加环境变量
```

4. **启动应用**
```bash
# 开发模式
uv run streamlit run src/ai_assistant/ui/streamlit_app.py

# 或使用 Python
python -m streamlit run src/ai_assistant/ui/streamlit_app.py
```

5. **访问应用**
打开浏览器访问 `http://localhost:8501`

### Docker 部署

1. **构建镜像**
```bash
docker build -t ai-assistant .
```

2. **运行容器**
```bash
docker run -p 8501:8501 --env-file .env ai-assistant
```

3. **使用 Docker Compose**
```bash
docker-compose up -d
```

## 📖 使用指南

### 配置说明

#### 环境变量 (.env)
```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 应用配置
APP_ENV=development
LOG_LEVEL=INFO
```

#### 配置文件 (config/settings.yaml)
```yaml
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

### 功能使用

#### 1. 智能聊天
- 在聊天界面输入你的问题
- 支持多轮对话上下文
- 可调整AI回复的创造性程度

#### 2. 文本总结
- 粘贴或上传需要总结的文本
- 选择总结类型（要点总结/详细总结）
- 获取智能提炼的关键信息

#### 3. 多语言翻译
- 输入或粘贴需要翻译的文本
- 选择源语言和目标语言
- 获得高质量的翻译结果

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=src/ai_assistant --cov-report=html
```

### 测试结构
```
tests/
├── unit/              # 单元测试
│   ├── services/      # 服务层测试
│   └── utils/         # 工具函数测试
├── integration/       # 集成测试
│   └── api/          # API集成测试
└── conftest.py       # 测试配置
```

## 🔧 开发指南

### 代码规范
- 遵循 [PEP 8](https://pep8.org/) 代码风格
- 使用 Black 进行代码格式化
- 使用 Ruff 进行代码检查
- 使用 MyPy 进行类型检查

### 开发流程
1. 创建功能分支
2. 编写代码和测试
3. 运行代码质量检查
4. 提交代码审查
5. 合并到主分支

### 代码质量检查
```bash
# 代码格式化
black .

# 代码检查
ruff check .

# 类型检查
mypy .

# 运行所有质量检查
pre-commit run --all-files
```

## 📁 项目结构

```
ai-assistant/
├── src/
│   └── ai_assistant/
│       ├── core/                 # 核心基础设施
│       │   ├── config.py        # 配置管理
│       │   ├── logger.py        # 日志系统
│       │   └── exceptions.py    # 自定义异常
│       ├── services/            # 业务服务层
│       │   ├── deepseek_client.py
│       │   ├── chat_service.py
│       │   ├── summary_service.py
│       │   └── translate_service.py
│       ├── ui/                  # 用户界面
│       │   ├── streamlit_app.py
│       │   └── components/
│       └── utils/               # 通用工具
├── tests/                       # 测试代码
├── config/                      # 配置文件
├── docs/                        # 文档
├── scripts/                     # 脚本工具
├── requirements/                # 依赖文件
├── .github/workflows/           # CI/CD配置
├── pyproject.toml              # 项目配置
├── Dockerfile                  # Docker配置
└── docker-compose.yml          # Docker Compose配置
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 贡献类型
- 🐛 Bug修复
- ✨ 新功能开发
- 📝 文档改进
- 🎨 UI/UX改进
- ⚡ 性能优化
- 🔒 安全增强

## 📄 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [DeepSeek](https://deepseek.com/) - 提供强大的AI语言模型
- [Streamlit](https://streamlit.io/) - 现代化的Web应用框架
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证和设置管理

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/your-username/ai-assistant)
- 问题反馈: [Issues](https://github.com/your-username/ai-assistant/issues)
- 功能建议: [Discussions](https://github.com/your-username/ai-assistant/discussions)

## 🗺️ 路线图

### v1.0.0 (当前版本)
- [x] 基础聊天功能
- [x] 文本总结功能
- [x] 多语言翻译功能
- [x] Web界面
- [x] 基础配置管理

### v1.1.0 (计划中)
- [ ] 用户会话管理
- [ ] 文件上传支持
- [ ] 响应时间优化
- [ ] 更多AI模型支持

### v1.2.0 (未来版本)
- [ ] 插件系统
- [ ] 自定义提示模板
- [ ] 批量处理功能
- [ ] API接口开放

---

**开始使用**: 如果这是你第一次使用，请先查看 [快速开始](#-快速开始) 部分。如果你是开发者，建议阅读 [开发指南](#-开发指南) 了解项目的开发规范。