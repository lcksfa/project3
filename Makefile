.PHONY: help install dev test lint format clean build deploy docker-build docker-up docker-down

# 默认目标
help:
	@echo "AI Assistant - 可用命令:"
	@echo ""
	@echo "  install     - 安装项目依赖"
	@echo "  dev         - 启动开发服务器"
	@echo "  dev-port    - 在指定端口启动 (PORT=端口号)"
	@echo "  dev-public  - 允许外部访问启动"
	@echo "  test        - 运行测试套件"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo "  build       - 构建Docker镜像"
	@echo "  deploy      - 部署应用"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-up   - 启动Docker服务"
	@echo "  docker-down - 停止Docker服务"

# 安装依赖
install:
	uv sync
	@echo "✅ 依赖安装完成"

# 开发模式
dev:
	./scripts/start.sh

# 开发模式 (指定端口)
dev-port:
	@if [ -z "$(PORT)" ]; then echo "使用方法: make dev-port PORT=8502"; exit 1; fi
	./scripts/start.sh --port $(PORT)

# 允许外部访问
dev-public:
	./scripts/start.sh --host 0.0.0.0

# 运行测试
test:
	uv run pytest tests/ -v --cov=src/ai_assistant --cov-report=html

# 快速测试（不生成覆盖率报告）
test-quick:
	uv run pytest tests/ -v

# 代码检查
lint:
	uv run ruff check .
	uv run mypy .

# 代码格式化
format:
	uv run black .
	uv run ruff check . --fix

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "✅ 清理完成"

# 构建Docker镜像
docker-build:
	docker build -t ai-assistant:latest .

# 启动Docker服务
docker-up:
	docker-compose up -d

# 停止Docker服务
docker-down:
	docker-compose down

# 查看Docker日志
docker-logs:
	docker-compose logs -f ai-assistant

# 部署到开发环境
deploy-dev:
	./scripts/deploy.sh development

# 部署到测试环境
deploy-staging:
	./scripts/deploy.sh staging --push

# 部署到生产环境
deploy-prod:
	./scripts/deploy.sh production --push --migrate

# 安全检查
security:
	uv run bandit -r src/
	uv run safety check

# 生成依赖报告
deps-report:
	uv pip list --format=freeze > requirements-freeze.txt
	@echo "✅ 依赖报告已生成: requirements-freeze.txt"

# 检查过时的依赖
deps-outdated:
	uv pip list --outdated

# 数据库迁移（如果需要）
migrate:
	@echo "数据库迁移功能待实现"

# 启动Redis（如果需要）
redis-up:
	docker-compose up -d redis

# 备份数据（如果需要）
backup:
	@echo "备份功能待实现"

# 性能测试
perf-test:
	@echo "性能测试功能待实现"

# 文档生成
docs:
	@echo "文档生成功能待实现"

# 发布前检查
pre-release: lint test security
	@echo "✅ 发布前检查完成"