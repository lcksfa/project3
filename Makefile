.PHONY: help install dev test lint format clean build deploy docker-build docker-up docker-down test-unit test-integration test-all test-watch test-coverage test-report test-config test-services test-utils test-failed test-marked test-path test-parallel test-last-failed test-perf test-coverage-check clean-test verify security deps-report deps-outdated pre-release

# 默认目标
help:
	@echo "AI Assistant - 可用命令:"
	@echo ""
	@echo "  📦 依赖管理:"
	@echo "    install      - 安装项目依赖"
	@echo "    deps-report  - 生成依赖报告"
	@echo "    deps-outdated- 检查过时的依赖"
	@echo ""
	@echo "  🚀 开发环境:"
	@echo "    dev         - 启动开发服务器"
	@echo "    dev-port    - 在指定端口启动 (PORT=端口号)"
	@echo "    dev-public  - 允许外部访问启动"
	@echo "    verify      - 验证开发环境设置"
	@echo ""
	@echo "  🧪 测试相关:"
	@echo "    test        - 运行所有测试（包含覆盖率）"
	@echo "    test-quick  - 快速运行测试（无覆盖率）"
	@echo "    test-unit   - 运行单元测试"
	@echo "    test-integration - 运行集成测试"
	@echo "    test-all    - 运行所有测试类型"
	@echo "    test-watch  - 监视文件变化自动运行测试"
	@echo "    test-coverage - 生成详细覆盖率报告"
	@echo "    test-report - 生成测试报告"
	@echo "    test-config - 测试配置模块"
	@echo "    test-services - 测试服务模块"
	@echo "    test-utils  - 测试工具模块"
	@echo "    test-failed  - 重新运行失败的测试"
	@echo ""
	@echo "  🔍 代码质量:"
	@echo "    lint        - 代码检查"
	@echo "    format      - 代码格式化"
	@echo "    security    - 安全检查"
	@echo "    pre-release - 发布前检查"
	@echo ""
	@echo "  🐳 Docker:"
	@echo "    docker-build - 构建Docker镜像"
	@echo "    docker-up   - 启动Docker服务"
	@echo "    docker-down - 停止Docker服务"
	@echo "    docker-logs - 查看Docker日志"
	@echo ""
	@echo "  📋 其他:"
	@echo "    clean       - 清理临时文件"
	@echo "    migrate     - 数据库迁移"
	@echo "    docs        - 生成文档"

# 安装依赖
install:
	uv sync
	@echo "✅ 依赖安装完成"

# 安装测试依赖
install-test:
	uv add pytest pytest-cov pytest-asyncio pytest-mock pytest-html
	@echo "✅ 测试依赖安装完成"

# 安装开发依赖（包含测试依赖）
install-dev:
	uv sync --dev
	@echo "✅ 开发依赖安装完成"

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

# 验证开发环境
verify:
	./scripts/verify_setup.sh

# 运行所有测试（包含覆盖率）
test:
	@echo "🧪 运行完整测试套件..."
	PYTHONPATH=src uv run pytest tests/ -v --tb=short --cov=src --cov-report=html --cov-report=term --cov-report=xml --junitxml=test-results.xml
	@echo "✅ 测试完成"
	@echo "📊 覆盖率报告: htmlcov/index.html"

# 快速测试（无覆盖率）
test-quick:
	@echo "⚡ 快速测试运行..."
	PYTHONPATH=src uv run pytest tests/ -v --tb=line
	@echo "✅ 快速测试完成"

# 运行单元测试
test-unit:
	@echo "🔬 运行单元测试..."
	PYTHONPATH=src uv run pytest tests/unit/ -v --tb=short -m "not integration and not slow"
	@echo "✅ 单元测试完成"

# 运行集成测试
test-integration:
	@echo "🔗 运行集成测试..."
	PYTHONPATH=src uv run pytest tests/integration/ -v --tb=short
	@echo "✅ 集成测试完成"

# 运行所有测试类型
test-all:
	@echo "🧪 运行所有测试类型..."
	PYTHONPATH=src uv run pytest tests/ -v --tb=short --cov=src --cov-report=html --cov-report=term
	@echo "✅ 所有测试完成"

# 监视文件变化自动运行测试
test-watch:
	@echo "👀 启动测试监视模式..."
	PYTHONPATH=src uv run pytest-watch tests/ -v --tb=short

# 生成详细覆盖率报告
test-coverage:
	@echo "📊 生成详细覆盖率报告..."
	PYTHONPATH=src uv run pytest tests/ --cov=src --cov-report=html --cov-report=term --cov-report=xml --cov-fail-under=80
	@echo "✅ 覆盖率报告生成完成"
	@echo "📈 查看报告: open htmlcov/index.html"

# 生成测试报告
test-report:
	@echo "📋 生成测试报告..."
	PYTHONPATH=src uv run pytest tests/ -v --tb=short --junitxml=test-results.xml --html=test-report.html --self-contained-html
	@echo "✅ 测试报告生成完成"
	@echo "📄 查看报告: open test-report.html"

# 测试配置模块
test-config:
	@echo "⚙️ 测试配置模块..."
	PYTHONPATH=src uv run pytest tests/unit/test_config*.py -v --tb=short
	@echo "✅ 配置模块测试完成"

# 测试服务模块
test-services:
	@echo "🛠️ 测试服务模块..."
	PYTHONPATH=src uv run pytest tests/unit/test_*_service.py -v --tb=short
	@echo "✅ 服务模块测试完成"

# 测试工具模块
test-utils:
	@echo "🔧 测试工具模块..."
	PYTHONPATH=src uv run pytest tests/unit/test_validators.py tests/unit/test_helpers.py tests/unit/test_exceptions.py -v --tb=short
	@echo "✅ 工具模块测试完成"

# 重新运行失败的测试
test-failed:
	@echo "🔄 重新运行失败的测试..."
	PYTHONPATH=src uv run pytest --lf -v --tb=short
	@echo "✅ 失败测试重跑完成"

# 运行特定标记的测试
test-marked:
	@if [ -z "$(MARK)" ]; then echo "使用方法: make test-marked MARK=unit|integration|slow"; exit 1; fi
	@echo "🏷️ 运行标记为 $(MARK) 的测试..."
	PYTHONPATH=src uv run pytest tests/ -v --tb=short -m $(MARK)
	@echo "✅ 标记测试完成"

# 运行特定文件/目录的测试
test-path:
	@if [ -z "$(PATH)" ]; then echo "使用方法: make test-path PATH=tests/unit/test_config.py"; exit 1; fi
	@echo "📁 运行指定路径的测试: $(PATH)"
	PYTHONPATH=src uv run pytest $(PATH) -v --tb=short
	@echo "✅ 指定路径测试完成"

# 并行运行测试
test-parallel:
	@echo "⚡ 并行运行测试..."
	PYTHONPATH=src uv run pytest tests/ -v --tb=short -n auto
	@echo "✅ 并行测试完成"

# 只运行上次失败的测试
test-last-failed:
	@echo "🔍 运行上次失败的测试..."
	PYTHONPATH=src uv run pytest --lf -v --tb=short
	@echo "✅ 失败测试重跑完成"

# 运行性能测试
test-perf:
	@echo "⚡ 运行性能测试..."
	PYTHONPATH=src uv run pytest tests/ -v --tb=short -m performance --benchmark-only
	@echo "✅ 性能测试完成"

# 测试覆盖率检查（要求最低覆盖率）
test-coverage-check:
	@echo "🎯 检查测试覆盖率（最低85%）..."
	PYTHONPATH=src uv run pytest tests/ --cov=src --cov-fail-under=85 --cov-report=term-missing
	@echo "✅ 覆盖率检查通过"

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
	@echo "🧹 清理临时文件..."
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
	rm -rf test-results.xml
	rm -rf test-report.html
	rm -rf .benchmarks/
	@echo "✅ 清理完成"

# 清理测试相关文件
clean-test:
	@echo "🧹 清理测试相关文件..."
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf test-results.xml
	rm -rf test-report.html
	rm -rf .benchmarks/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ 测试文件清理完成"

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