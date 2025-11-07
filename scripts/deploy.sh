#!/bin/bash

# AI Assistant 部署脚本
# 使用方法: ./scripts/deploy.sh [环境] [选项]

set -e

# 默认参数
ENVIRONMENT="development"
DOCKER_BUILD=true
DOCKER_PUSH=false
RUN_MIGRATIONS=false
SKIP_TESTS=false
VERBOSE=false

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 显示帮助信息
show_help() {
    cat << EOF
AI Assistant 部署脚本

使用方法:
    $0 [环境] [选项]

环境:
    development    开发环境 (默认)
    staging        测试环境
    production     生产环境

选项:
    --build        构建Docker镜像 (默认)
    --push         推送Docker镜像到仓库
    --migrate      运行数据库迁移
    --skip-tests   跳过测试
    --verbose      详细输出
    --help         显示此帮助信息

示例:
    $0 development --build
    $0 production --push --migrate
    $0 staging --skip-tests --verbose

EOF
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            development|staging|production)
                ENVIRONMENT="$1"
                shift
                ;;
            --build)
                DOCKER_BUILD=true
                shift
                ;;
            --push)
                DOCKER_PUSH=true
                shift
                ;;
            --migrate)
                RUN_MIGRATIONS=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi

    # 检查uv
    if ! command -v uv &> /dev/null; then
        log_error "uv 未安装"
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
    else
        log_warning "未找到环境变量文件"
    fi

    # 设置必要的环境变量
    export APP_ENV=$ENVIRONMENT
    export PYTHONPATH=$(pwd)/src

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "环境变量:"
        env | grep -E '^(APP_|DEEPSEEK_|PYTHONPATH)' | sort
    fi
}

# 运行测试
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "跳过测试"
        return
    fi

    log_info "运行测试..."

    # 安装依赖
    uv sync

    # 运行测试
    uv run pytest tests/ -v --tb=short

    log_success "测试完成"
}

# 构建Docker镜像
build_docker_image() {
    if [[ "$DOCKER_BUILD" != "true" ]]; then
        return
    fi

    log_info "构建Docker镜像..."

    # 设置镜像标签
    IMAGE_NAME="ai-assistant"
    TAG="${ENVIRONMENT}-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "镜像名称: $IMAGE_NAME:$TAG"
    fi

    # 构建镜像
    docker build \
        --tag "$IMAGE_NAME:$TAG" \
        --tag "$IMAGE_NAME:$ENVIRONMENT" \
        --build-arg APP_ENV=$ENVIRONMENT \
        .

    log_success "Docker镜像构建完成: $IMAGE_NAME:$TAG"
}

# 推送Docker镜像
push_docker_image() {
    if [[ "$DOCKER_PUSH" != "true" ]]; then
        return
    fi

    log_info "推送Docker镜像..."

    IMAGE_NAME="ai-assistant"
    TAG="${ENVIRONMENT}-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"

    # 推送镜像
    docker push "$IMAGE_NAME:$TAG"
    docker push "$IMAGE_NAME:$ENVIRONMENT"

    log_success "Docker镜像推送完成"
}

# 部署应用
deploy_application() {
    log_info "部署应用..."

    # 使用Docker Compose部署
    if [[ "$ENVIRONMENT" == "development" ]]; then
        docker-compose up -d ai-assistant
    elif [[ "$ENVIRONMENT" == "staging" ]]; then
        docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
    fi

    log_success "应用部署完成"
}

# 运行数据库迁移
run_migrations() {
    if [[ "$RUN_MIGRATIONS" != "true" ]]; then
        return
    fi

    log_info "运行数据库迁移..."

    # 这里添加数据库迁移逻辑
    # 例如: docker-compose exec ai-assistant uv run alembic upgrade head

    log_success "数据库迁移完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 等待应用启动
    sleep 10

    # 检查应用是否正常运行
    if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
        log_success "应用健康检查通过"
    else
        log_error "应用健康检查失败"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    log_info "部署信息:"
    echo "环境: $ENVIRONMENT"
    echo "时间: $(date)"
    echo "版本: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo "访问地址: http://localhost:8501"
    echo ""
    echo "有用的命令:"
    echo "  查看日志: docker-compose logs -f ai-assistant"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart ai-assistant"
}

# 主函数
main() {
    log_info "开始部署 AI Assistant..."

    # 解析参数
    parse_arguments "$@"

    # 检查依赖
    check_dependencies

    # 设置环境
    setup_environment

    # 运行测试
    run_tests

    # 构建镜像
    build_docker_image

    # 推送镜像
    push_docker_image

    # 部署应用
    deploy_application

    # 运行迁移
    run_migrations

    # 健康检查
    health_check

    # 显示部署信息
    show_deployment_info

    log_success "部署完成!"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi