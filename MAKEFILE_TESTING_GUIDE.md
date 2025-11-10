# Makefile 测试使用指南

## 概述

本项目提供了完善的 Makefile 测试命令，支持各种测试场景和覆盖率报告生成。

## 🚀 快速开始

### 安装依赖

```bash
# 安装项目依赖
make install

# 安装测试依赖（如果需要）
make install-test

# 安装开发依赖（包含所有测试依赖）
make install-dev
```

### 基础测试命令

```bash
# 运行所有测试（包含覆盖率报告）
make test

# 快速测试（无覆盖率）
make test-quick

# 只运行单元测试
make test-unit

# 运行集成测试
make test-integration
```

## 📊 测试类型详解

### 1. 基础测试命令

- **`make test`** - 运行完整测试套件，生成 HTML、XML、终端和 JUnit 格式的覆盖率报告
- **`make test-quick`** - 快速运行测试，不生成覆盖率报告
- **`make test-unit`** - 只运行单元测试（排除集成测试和慢速测试）
- **`make test-integration`** - 只运行集成测试

### 2. 分类测试命令

- **`make test-config`** - 测试配置模块（config*.py）
- **`make test-services`** - 测试服务模块（*_service.py）
- **`make test-utils`** - 测试工具模块（validators.py, helpers.py, exceptions.py）

### 3. 高级测试命令

- **`make test-all`** - 运行所有测试类型
- **`make test-coverage`** - 生成详细覆盖率报告，要求最低80%覆盖率
- **`make test-report`** - 生成 HTML 格式的测试报告

### 4. 特殊测试命令

- **`make test-failed`** - 重新运行上次失败的测试
- **`make test-last-failed`** - 只运行上次失败的测试（与 test-failed 相同）
- **`make test-parallel`** - 并行运行测试（需要 pytest-xdist）
- **`make test-watch`** - 监视文件变化自动运行测试（需要 pytest-watch）

### 5. 参数化测试命令

```bash
# 运行特定标记的测试
make test-marked MARK=unit

# 运行特定路径的测试
make test-path PATH=tests/unit/test_config.py

# 运行性能测试
make test-perf

# 检查测试覆盖率（要求最低85%）
make test-coverage-check
```

## 🔧 环境配置

### Python 路径设置

所有测试命令都设置了 `PYTHONPATH=src`，确保能正确导入项目模块。

### 测试环境变量

测试运行时会自动设置以下环境变量：
- `APP_ENV=testing`
- `LOG_LEVEL=DEBUG`

## 📈 覆盖率报告

### 生成覆盖率报告

```bash
# 基础覆盖率报告
make test

# 详细覆盖率报告
make test-coverage

# 覆盖率检查（失败退出）
make test-coverage-check
```

### 查看覆盖率报告

```bash
# 在浏览器中打开HTML报告
open htmlcov/index.html

# 查看终端覆盖率摘要
# 自动显示在命令行输出中
```

## 🧹 清理命令

```bash
# 清理所有临时文件
make clean

# 只清理测试相关文件
make clean-test
```

## 🔍 测试调试

### 查看详细错误信息

```bash
# 显示简短错误信息
make test-quick

# 显示详细错误信息
PYTHONPATH=src uv run pytest tests/ -v --tb=long

# 只显示失败的测试详细信息
make test-failed
```

### 运行特定测试

```bash
# 运行特定文件
make test-path PATH=tests/unit/test_config_simple.py

# 运行特定测试函数
PYTHONPATH=src uv run pytest tests/unit/test_config_simple.py::TestSimpleSettings::test_default_settings -v
```

## 📝 测试报告

### 生成测试报告

```bash
# 生成HTML测试报告
make test-report

# 查看测试报告
open test-report.html
```

### JUnit XML 报告

```bash
# 自动生成 test-results.xml
make test

# 可用于CI/CD系统集成
```

## 🏷️ 测试标记

项目中支持以下测试标记：

- `unit` - 单元测试
- `integration` - 集成测试
- `slow` - �速测试
- `performance` - 性能测试

### 使用标记

```bash
# 运行单元测试
make test-marked MARK=unit

# 运行集成测试
make test-marked MARK=integration

# 排除慢速测试
PYTHONPATH=src uv run pytest tests/ -v -m "not slow"
```

## 🚨 故障排除

### 常见问题

1. **模块导入错误**
   ```bash
   # 确保PYTHONPATH设置正确
   echo $PYTHONPATH
   # 应该包含 src 目录
   ```

2. **依赖缺失**
   ```bash
   # 安装测试依赖
   make install-test
   ```

3. **权限问题**
   ```bash
   # 确保脚本可执行
   chmod +x scripts/*.sh
   ```

### 调试技巧

1. **运行单个测试**
   ```bash
   PYTHONPATH=src uv run pytest tests/unit/test_config.py::TestSimpleSettings::test_default_settings -v -s
   ```

2. **显示详细输出**
   ```bash
   PYTHONPATH=src uv run pytest tests/unit/test_config.py -v -s --tb=long
   ```

3. **进入调试模式**
   ```bash
   PYTHONPATH=src uv run pytest tests/unit/test_config.py -v --pdb
   ```

## 📋 最佳实践

### 开发工作流

1. **开发前**
   ```bash
   make install-dev
   make verify
   ```

2. **开发中**
   ```bash
   make test-quick  # 快速验证
   ```

3. **提交前**
   ```bash
   make test        # 完整测试
   make lint        # 代码检查
   make pre-release # 发布前检查
   ```

### 持续集成

在 CI/CD 管道中建议使用：

```bash
make install-dev
make test-coverage-check
make lint
make security
```

## 🔗 相关文档

- [TEST_REPORT.md](TEST_REPORT.md) - 详细测试报告
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- [README.md](README.md) - 项目说明

---

**更新时间**: 2025年11月7日
**版本**: 1.0