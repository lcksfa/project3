# 🚀 快速使用指南

## 前提条件

确保您的 Python 环境已经安装并配置好了所有依赖：
```bash
make install
```

## 1. 配置 DeepSeek API 密钥

编辑 `.env` 文件，添加您的 DeepSeek API 密钥：

```bash
# 打开 .env 文件
nano .env

# 找到这一行并替换为您的 API 密钥
DEEPSEEK_API_KEY=your_actual_api_key_here
```

> 💡 **获取 API 密钥**: 访问 [DeepSeek API 官网](https://platform.deepseek.com) 注册并获取您的 API 密钥

## 2. 启动应用

### 方法一：使用 Makefile（推荐）
```bash
# 默认启动
make dev

# 指定端口启动
make dev-port PORT=8502

# 允许外部访问
make dev-public
```

### 方法二：使用启动脚本
```bash
# 默认启动
./scripts/start.sh

# 指定端口启动
./scripts/start.sh --port 8502

# 允许外部访问
./scripts/start.sh --host 0.0.0.0

# 无头模式（后台运行）
./scripts/start.sh --headless
```

### 方法三：直接使用 Streamlit
```bash
uv run streamlit run src/ai_assistant/ui/streamlit_app.py
```

## 3. 访问应用

启动成功后，在浏览器中打开以下地址：
- **本地访问**: http://localhost:8501
- **网络访问**: http://your-ip:8501

## 4. 使用功能

### 💬 智能聊天
1. 在侧边栏输入您的 DeepSeek API 密钥
2. 在聊天界面输入您的问题
3. AI 将实时回复您的问题
4. 支持多轮对话和会话管理

### 📝 文本总结
1. 切换到"文本总结"标签页
2. 输入或上传您要总结的文本
3. 选择总结类型（段落、要点、关键洞察等）
4. 点击"开始总结"获取智能总结

### 🌍 语言翻译
1. 切换到"语言翻译"标签页
2. 选择源语言和目标语言
3. 输入或上传要翻译的文本
4. 点击"开始翻译"获取翻译结果

## 5. 高级功能

### 自定义系统提示
在聊天功能的侧边栏中，您可以设置系统提示来定制 AI 助手的行为：

```示例
专业助手：
"你是一个专业的AI助手，请用准确、专业的语言回答问题。"

创意助手：
"你是一个富有创造力的AI助手，请用生动、有趣的方式回答问题。"
```

### 批量处理
- **批量翻译**: 在翻译界面使用"批量翻译"功能
- **批量总结**: 上传多个文件进行批量总结

### 会话管理
- 创建多个独立的聊天会话
- 查看和管理会话历史
- 导出和分享对话记录

## 6. 故障排除

### 常见问题

**Q: 应用启动失败，显示配置错误**
A: 确保 `.env` 文件中的 `DEEPSEEK_API_KEY` 已正确配置

**Q: API 调用失败**
A: 检查您的 API 密钥是否有效，以及网络连接是否正常

**Q: 端口被占用**
A: 使用 `make dev-port PORT=8502` 指定其他端口

**Q: 应用响应慢**
A: 检查网络连接，或调整 API 调用超时设置

### 查看日志
```bash
# 查看应用日志
tail -f logs/app.log

# 如果使用 Docker
docker-compose logs -f ai-assistant
```

### 重置配置
```bash
# 清理临时文件
make clean

# 重新安装依赖
make install

# 重新启动
make dev
```

## 7. 开发模式

如果您想进行开发或调试：

```bash
# 开发模式（启用调试）
./scripts/start.sh --env development

# 查看详细日志
export LOG_LEVEL=DEBUG
make dev

# 运行测试
make test

# 代码检查
make lint
```

## 8. 生产部署

### Docker 部署
```bash
# 构建镜像
docker build -t ai-assistant .

# 运行容器
docker run -p 8501:8501 --env-file .env ai-assistant

# 或使用 Docker Compose
docker-compose up -d
```

### 自动化部署
```bash
# 部署到开发环境
./scripts/deploy.sh development

# 部署到生产环境
./scripts/deploy.sh production --push --migrate
```

## 9. 性能优化

### 提升响应速度
- 使用更快的网络连接
- 调整 `temperature` 和 `max_tokens` 参数
- 启用缓存功能

### 减少延迟
- 使用流式输出模式
- 减少文本长度
- 选择合适的API模型

## 10. 获取帮助

- 📖 **完整文档**: 查看 [README.md](README.md)
- 🐛 **问题反馈**: [GitHub Issues](https://github.com/your-username/ai-assistant/issues)
- 💬 **社区讨论**: [GitHub Discussions](https://github.com/your-username/ai-assistant/discussions)

---

🎉 **恭喜！您已经成功启动了多功能AI助手！**

开始探索智能对话、文本总结和语言翻译的强大功能吧！