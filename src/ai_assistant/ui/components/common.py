"""
通用UI组件

提供可复用的Streamlit组件。
"""

import streamlit as st
import time
from typing import Optional, Any
from ...core.logger import get_logger


def render_header():
    """渲染页面头部"""
    st.title("🤖 多功能AI助手")
    st.markdown("""
    集成DeepSeek API的企业级AI助手，提供智能聊天、文本总结、语言翻译等功能。
    """)
    st.divider()


def render_footer():
    """渲染页面底部"""
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        © 2024 多功能AI助手 | Powered by DeepSeek |
        <a href='https://github.com/your-username/ai-assistant' target='_blank'>GitHub</a>
    </div>
    """, unsafe_allow_html=True)


def show_error(message: str, exception: Optional[Exception] = None):
    """显示错误信息"""
    logger = get_logger("ui")
    logger.error(f"UI错误: {message}", exc_info=exception)

    st.error(f"❌ {message}")
    if exception and st.session_state.get('debug', False):
        st.exception(exception)


def show_success(message: str):
    """显示成功信息"""
    st.success(f"✅ {message}")


def show_warning(message: str):
    """显示警告信息"""
    st.warning(f"⚠️ {message}")


def show_info(message: str):
    """显示信息"""
    st.info(f"ℹ️ {message}")


def loading_spinner(message: str = "处理中..."):
    """加载动画上下文管理器"""
    return st.spinner(message)


def countdown_timer(seconds: int, message: str = "请等待"):
    """倒计时器"""
    placeholder = st.empty()
    for i in range(seconds, 0, -1):
        placeholder.info(f"{message} {i}秒...")
        time.sleep(1)
    placeholder.empty()


def progress_bar(percentage: int, message: str = "进度"):
    """进度条"""
    st.progress(percentage / 100, text=message)


def expandable_section(title: str, content: str, expanded: bool = False):
    """可展开的内容区域"""
    with st.expander(title, expanded=expanded):
        st.markdown(content)


def code_block(code: str, language: str = "python", title: Optional[str] = None):
    """代码块显示"""
    if title:
        st.subheader(title)
    st.code(code, language=language)


def file_upload_area(
    label: str,
    help_text: str,
    accepted_types: list = None,
    key: Optional[str] = None
):
    """文件上传区域"""
    return st.file_uploader(
        label=label,
        type=accepted_types or ['txt', 'md', 'py'],
        help=help_text,
        key=key
    )


def text_input_area(
    label: str,
    placeholder: str = "",
    height: int = 200,
    max_chars: Optional[int] = None,
    key: Optional[str] = None
):
    """文本输入区域"""
    return st.text_area(
        label=label,
        placeholder=placeholder,
        height=height,
        max_chars=max_chars,
        key=key
    )


def slider_with_value(
    label: str,
    min_value: float,
    max_value: float,
    value: float,
    step: float = 0.1,
    help_text: str = ""
):
    """带值显示的滑块"""
    col1, col2 = st.columns([3, 1])
    with col1:
        result = st.slider(
            label=label,
            min_value=min_value,
            max_value=max_value,
            value=value,
            step=step,
            help=help_text
        )
    with col2:
        st.metric("值", f"{result:.1f}")
    return result


def selectbox_with_search(
    label: str,
    options: list,
    index: int = 0,
    help_text: str = "",
    key: Optional[str] = None
):
    """带搜索功能的选择框"""
    if len(options) > 10:
        # 如果选项太多，使用搜索框
        search_term = st.text_input(f"搜索{label}...", key=f"{key}_search")
        filtered_options = [opt for opt in options if search_term.lower() in str(opt).lower()]
        if not filtered_options:
            filtered_options = options
        return st.selectbox(label, filtered_options, index=0, help=help_text, key=key)
    else:
        return st.selectbox(label, options, index=index, help=help_text, key=key)


def button_with_confirmation(
    label: str,
    confirmation_message: str,
    button_type: str = "primary",
    key: Optional[str] = None
):
    """带确认的按钮"""
    if st.button(label, type=button_type, key=key):
        if st.checkbox(f"确认: {confirmation_message}", key=f"{key}_confirm"):
            return True
    return False


def metrics_row(metrics: dict):
    """指标行显示"""
    cols = st.columns(len(metrics))
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i]:
            st.metric(label, value)


def tabs_with_content(tab_names: list, content_functions: list):
    """带内容的标签页"""
    tabs = st.tabs(tab_names)
    for i, (tab, content_func) in enumerate(zip(tabs, content_functions)):
        with tab:
            content_func()


def sidebar_section(title: str, content_func):
    """侧边栏区域"""
    with st.sidebar:
        st.subheader(title)
        content_func()


def status_indicator(status: str, message: str):
    """状态指示器"""
    if status == "success":
        st.success(f"✅ {message}")
    elif status == "warning":
        st.warning(f"⚠️ {message}")
    elif status == "error":
        st.error(f"❌ {message}")
    else:
        st.info(f"ℹ️ {message}")


def tooltip(text: str, tooltip_text: str):
    """工具提示"""
    st.help(tooltip_text)
    st.write(text)


def link_button(text: str, url: str, use_container_width: bool = True):
    """链接按钮"""
    st.markdown(f"""
    <a href="{url}" target="_blank">
        <button style="
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            cursor: pointer;
            width: 100%;
        ">
            {text}
        </button>
    </a>
    """, unsafe_allow_html=True)


def card(title: str, content: str, image_url: Optional[str] = None):
    """卡片组件"""
    if image_url:
        st.image(image_url, width=100)
    st.subheader(title)
    st.write(content)


def timeline(events: list):
    """时间线组件"""
    for i, event in enumerate(events):
        with st.container():
            if i > 0:
                st.divider()

            col1, col2 = st.columns([1, 5])
            with col1:
                st.write(f"**{event.get('time', '')}**")
            with col2:
                st.write(event.get('content', ''))


def collapsible_code(title: str, code: str, language: str = "python"):
    """可折叠的代码块"""
    with st.expander(title):
        st.code(code, language=language)


def data_table(data, title: Optional[str] = None):
    """数据表格"""
    if title:
        st.subheader(title)
    st.dataframe(data, use_container_width=True)


def json_viewer(data: dict, title: Optional[str] = None):
    """JSON查看器"""
    if title:
        st.subheader(title)
    st.json(data)


def copy_to_clipboard_button(text: str, label: str = "复制"):
    """复制到剪贴板按钮"""
    st.markdown(f"""
    <button onclick="navigator.clipboard.writeText('{text}')" style="
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        cursor: pointer;
    ">
        {label}
    </button>
    """, unsafe_allow_html=True)