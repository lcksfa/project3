#!/bin/bash

# AI Assistant 设置验证脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔍 AI Assistant 设置验证"
echo "======================"

# 检查 Python 环境
log_info "检查 Python 环境..."
if ! command -v python &> /dev/null; then
    log_error "Python 未安装"
    exit 1
fi
python_version=$(python --version 2>&1 | awk '{print $2}')
log_success "Python 版本: $python_version"

# 检查 uv
log_info "检查 uv 包管理器..."
if ! command -v uv &> /dev/null; then
    log_error "uv 未安装"
    exit 1
fi
log_success "uv 已安装"

# 检查依赖
log_info "检查项目依赖..."
if python -c "import streamlit, httpx, pydantic" 2>/dev/null; then
    log_success "核心依赖已安装"
else
    log_error "缺少核心依赖，请运行: make install"
    exit 1
fi

# 检查配置文件
log_info "检查配置文件..."
if [[ ! -f ".env" ]]; then
    log_warning ".env 文件不存在，创建默认配置..."
    cp .env.example .env
    log_info "请编辑 .env 文件并添加您的 DEEPSEEK_API_KEY"
fi

if [[ -f ".env" ]]; then
    api_key=$(grep "DEEPSEEK_API_KEY=" .env | cut -d'=' -f2)
    if [[ "$api_key" == "your_api_key_here" ]] || [[ -z "$api_key" ]]; then
        log_warning "请在 .env 文件中设置您的 DeepSeek API 密钥"
        log_info "编辑命令: nano .env"
    else
        log_success "API 密钥已配置"
    fi
fi

# 检查项目结构
log_info "检查项目结构..."
required_files=(
    "src/ai_assistant/__init__.py"
    "src/ai_assistant/ui/streamlit_app.py"
    "src/ai_assistant/core/config_simple.py"
    "scripts/start.sh"
    "Makefile"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        log_success "✓ $file"
    else
        log_error "✗ $file 缺失"
        exit 1
    fi
done

# 测试配置系统
log_info "测试配置系统..."
if python -c "from ai_assistant.core.config_simple import get_settings; settings = get_settings(); print('配置系统正常')" 2>/dev/null; then
    log_success "配置系统工作正常"
else
    log_error "配置系统有问题"
    exit 1
fi

# 测试导入
log_info "测试应用导入..."
if python -c "from ai_assistant.ui.streamlit_app import main; print('应用导入正常')" 2>/dev/null; then
    log_success "应用导入正常"
else
    log_error "应用导入失败"
    exit 1
fi

# 端口检查
log_info "检查可用端口..."
for port in {8501..8505}; do
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        available_port=$port
        break
    fi
done

if [[ -n "$available_port" ]]; then
    log_success "端口 $available_port 可用"
else
    log_warning "端口 8501-8505 都被占用，可能需要使用其他端口"
fi

# 环境变量检查
log_info "检查环境变量..."
if [[ -n "$DEEPSEEK_API_KEY" ]]; then
    log_success "DEEPSEEK_API_KEY 已设置"
else
    log_warning "DEEPSEEK_API_KEY 未设置，将在运行时配置"
fi

echo ""
log_success "🎉 设置验证完成！"
echo ""
echo "现在您可以启动应用："
echo ""
echo "方法一 - 使用 Makefile："
echo "  make dev                    # 默认启动"
echo "  make dev-port PORT=8502   # 指定端口"
echo "  make dev-public            # 允许外部访问"
echo ""
echo "方法二 - 使用启动脚本："
echo "  ./scripts/start.sh"
echo "  ./scripts/start.sh --port 8502"
echo "  ./scripts/start.sh --host 0.0.0.0"
echo ""
echo "方法三 - 直接启动："
echo "  uv run streamlit run src/ai_assistant/ui/streamlit_app.py"
echo ""
echo "📚 更多帮助："
echo "  - 快速开始指南: cat QUICK_START.md"
echo "  - 完整文档: cat README.md"
echo "  - 开发规范: cat claude.md"
echo ""
echo "🚀 准备启动 AI Assistant！"