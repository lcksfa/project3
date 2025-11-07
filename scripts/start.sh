#!/bin/bash

# AI Assistant 启动脚本

set -e

# 默认参数
PORT=8501
HOST="localhost"
HEADLESS=false
ENVIRONMENT="development"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# 显示帮助信息
show_help() {
    cat << EOF
AI Assistant 启动脚本

使用方法:
    $0 [选项]

选项:
    --port PORT        设置端口号 (默认: 8501)
    --host HOST        设置主机地址 (默认: localhost)
    --headless        以无头模式运行
    --env ENVIRONMENT  设置环境 (development/staging/production)
    --help            显示此帮助信息

示例:
    $0                          # 默认启动
    $0 --port 8502              # 在端口8502启动
    $0 --host 0.0.0.0           # 允许外部访问
    $0 --headless               # 无头模式
    $0 --env production         # 生产环境

EOF
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                PORT="$2"
                shift 2
                ;;
            --host)
                HOST="$2"
                shift 2
                ;;
            --headless)
                HEADLESS=true
                shift
                ;;
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_warning "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    # 检查uv
    if ! command -v uv &> /dev/null; then
        log_error "uv 未安装，请先安装 uv"
        exit 1
    fi

    # 检查Python
    if ! command -v python &> /dev/null; then
        log_error "Python 未安装"
        exit 1
    fi

    log_success "依赖检查完成"
}

# 设置环境变量
setup_environment() {
    log_info "设置环境: $ENVIRONMENT"

    # 加载环境变量文件
    if [[ -f ".env.$ENVIRONMENT" ]]; then
        export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)
        log_success "已加载 .env.$ENVIRONMENT"
    elif [[ -f ".env" ]]; then
        export $(cat .env | grep -v '^#' | xargs)
        log_success "已加载 .env"
    fi

    # 设置Python路径
    export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
    export APP_ENV="$ENVIRONMENT"
}

# 检查端口是否可用
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "端口 $PORT 已被占用"
        log_info "尝试寻找可用端口..."

        # 寻找可用端口
        for i in {8502..8600}; do
            if ! lsof -Pi :$i -sTCP:LISTEN -t >/dev/null 2>&1; then
                PORT=$i
                log_info "使用端口: $PORT"
                break
            fi
        done
    fi
}

# 启动应用
start_application() {
    log_info "启动 AI Assistant 应用..."
    log_info "访问地址: http://$HOST:$PORT"

    # 构建启动命令
    CMD="uv run streamlit run src/ai_assistant/ui/streamlit_app.py"
    CMD="$CMD --server.port=$PORT"
    CMD="$CMD --server.address=$HOST"

    if [[ "$HEADLESS" == "true" ]]; then
        CMD="$CMD --server.headless=true"
    fi

    # 如果是开发环境，添加开发选项
    if [[ "$ENVIRONMENT" == "development" ]]; then
        CMD="$CMD --server.fileWatcherType=watchdog"
    fi

    log_info "执行命令: $CMD"

    # 启动应用
    exec $CMD
}

# 显示启动后信息
show_startup_info() {
    echo ""
    log_success "AI Assistant 已启动!"
    echo ""
    echo "访问地址:"
    echo "  本地:   http://$HOST:$PORT"
    if [[ "$HOST" == "0.0.0.0" ]]; then
        echo "  网络:   http://$(hostname -I | awk '{print $1}'):$PORT"
    fi
    echo ""
    echo "停止应用: Ctrl+C"
    echo ""
    echo "有用的命令:"
    echo "  查看日志: docker-compose logs -f ai-assistant"
    echo "  重启应用: make dev"
    echo "  运行测试: make test"
    echo ""
}

# 主函数
main() {
    echo "🤖 AI Assistant 启动脚本"
    echo "================================"

    # 解析参数
    parse_arguments "$@"

    # 检查依赖
    check_dependencies

    # 设置环境
    setup_environment

    # 检查端口
    check_port

    # 显示启动信息
    show_startup_info

    # 启动应用
    start_application
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi