"""
Streamlit 主应用

多功能AI助手的Web界面。
"""

import streamlit as st
import asyncio
from typing import Dict, Any
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_assistant.core.config_simple import get_settings, init_settings
from ai_assistant.core.logger import setup_logging, get_logger
from ai_assistant.core.exceptions import AIAssistantError
from ai_assistant.services.chat_service import ChatService
from ai_assistant.services.summary_service import SummaryService, SummaryType
from ai_assistant.services.translate_service import TranslationService, TranslationStyle
from ai_assistant.ui.components import (
    render_header, render_footer, show_error,
    ChatInterface, SummaryInterface, TranslateInterface
)

# 配置页面
st.set_page_config(
    page_title="多功能AI助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化配置和日志
@st.cache_resource
def initialize_app():
    """初始化应用"""
    try:
        # 初始化配置
        settings = init_settings()

        # 设置日志
        setup_logging(settings.logging)

        # 获取logger
        logger = get_logger("app")
        logger.info("应用初始化成功")

        return settings, logger
    except Exception as e:
        st.error(f"应用初始化失败: {e}")
        st.stop()

def main():
    """主函数"""
    try:
        # 初始化应用
        settings, logger = initialize_app()

        # 渲染页面头部
        render_header()

        # 侧边栏配置
        render_sidebar(settings)

        # 主内容区域
        render_main_content()

        # 渲染页面底部
        render_footer()

    except Exception as e:
        logger = get_logger("app")
        logger.error(f"应用运行错误: {e}", exc_info=True)
        show_error(f"应用运行出错: {e}")

def render_sidebar(settings):
    """渲染侧边栏"""
    with st.sidebar:
        st.title("⚙️ 设置")

        # API配置
        st.subheader("API配置")
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            help="请输入您的DeepSeek API密钥"
        )

        if api_key:
            st.session_state.api_key = api_key
            settings.deepseek.api_key = api_key

        # 应用设置
        st.subheader("应用设置")

        # 模型选择
        model = st.selectbox(
            "模型选择",
            ["deepseek-chat", "deepseek-coder"],
            index=0,
            help="选择要使用的AI模型"
        )

        # 温度参数
        temperature = st.slider(
            "温度参数",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="控制回复的创造性，越高越有创造性"
        )

        # 最大token数
        max_tokens = st.number_input(
            "最大Token数",
            min_value=100,
            max_value=8192,
            value=2048,
            step=100,
            help="限制回复的最大长度"
        )

        # 保存设置到session state
        st.session_state.update({
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        })

        # 系统信息
        st.subheader("系统信息")
        st.info(f"""
        **应用版本**: {settings.app.version}
        **调试模式**: {'开启' if settings.app.debug else '关闭'}
        **日志级别**: {settings.logging.level}
        """)

        # 清除数据按钮
        if st.button("🗑️ 清除所有数据", type="secondary"):
            clear_all_data()
            st.rerun()

def render_main_content():
    """渲染主内容区域"""
    # 功能选择标签页
    tab1, tab2, tab3 = st.tabs(["💬 智能聊天", "📝 文本总结", "🌍 语言翻译"])

    with tab1:
        render_chat_tab()

    with tab2:
        render_summary_tab()

    with tab3:
        render_translate_tab()

def render_chat_tab():
    """渲染聊天标签页"""
    st.header("💬 智能聊天")

    # 检查API密钥
    if not check_api_key():
        st.warning("请在侧边栏设置API密钥以使用聊天功能")
        return

    try:
        # 初始化聊天服务
        if 'chat_service' not in st.session_state:
            st.session_state.chat_service = ChatService()

        # 渲染聊天界面
        chat_interface = ChatInterface(st.session_state.chat_service)
        chat_interface.render()

    except Exception as e:
        show_error(f"聊天服务初始化失败: {e}")

def render_summary_tab():
    """渲染总结标签页"""
    st.header("📝 文本总结")

    # 检查API密钥
    if not check_api_key():
        st.warning("请在侧边栏设置API密钥以使用总结功能")
        return

    try:
        # 初始化总结服务
        if 'summary_service' not in st.session_state:
            st.session_state.summary_service = SummaryService()

        # 渲染总结界面
        summary_interface = SummaryInterface(st.session_state.summary_service)
        summary_interface.render()

    except Exception as e:
        show_error(f"总结服务初始化失败: {e}")

def render_translate_tab():
    """渲染翻译标签页"""
    st.header("🌍 语言翻译")

    # 检查API密钥
    if not check_api_key():
        st.warning("请在侧边栏设置API密钥以使用翻译功能")
        return

    try:
        # 初始化翻译服务
        if 'translate_service' not in st.session_state:
            st.session_state.translate_service = TranslationService()

        # 渲染翻译界面
        translate_interface = TranslateInterface(st.session_state.translate_service)
        translate_interface.render()

    except Exception as e:
        show_error(f"翻译服务初始化失败: {e}")

def check_api_key() -> bool:
    """检查API密钥是否已设置"""
    return 'api_key' in st.session_state and st.session_state.api_key

def clear_all_data():
    """清除所有会话数据"""
    # 清除聊天会话
    if 'chat_service' in st.session_state:
        st.session_state.chat_service.sessions.clear()

    # 清除session state中的其他数据
    keys_to_clear = [
        'chat_messages', 'summary_result', 'translation_result',
        'current_session_id'
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    st.success("所有数据已清除")

def run_async(coro):
    """运行异步函数的辅助函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)

if __name__ == "__main__":
    main()