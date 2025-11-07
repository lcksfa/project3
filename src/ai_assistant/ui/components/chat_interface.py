"""
聊天界面组件

提供智能聊天功能的用户界面。
"""

import streamlit as st
import asyncio
from typing import List, Dict, Optional
import time

from ...services.chat_service import ChatService
from ...core.exceptions import AIAssistantError
from .common import (
    show_error, show_success, show_info, loading_spinner,
    text_input_area, slider_with_value, button_with_confirmation
)


class ChatInterface:
    """聊天界面类"""

    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
        self.logger = self._get_logger()

    def _get_logger(self):
        """获取日志记录器"""
        from ...core.logger import get_logger
        return get_logger("chat_ui")

    def render(self):
        """渲染聊天界面"""
        # 初始化会话状态
        self._init_session_state()

        # 布局
        self._render_layout()

    def _init_session_state(self):
        """初始化会话状态"""
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = "default"

        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []

        if 'chat_settings' not in st.session_state:
            st.session_state.chat_settings = {
                'temperature': 0.7,
                'max_tokens': 2048,
                'stream': True
            }

    def _render_layout(self):
        """渲染布局"""
        # 侧边栏 - 聊天设置
        self._render_sidebar()

        # 主区域
        col1, col2 = st.columns([3, 1])

        with col1:
            # 聊天消息区域
            self._render_messages()

            # 输入区域
            self._render_input_area()

        with col2:
            # 会话管理
            self._render_session_management()

    def _render_sidebar(self):
        """渲染侧边栏设置"""
        st.sidebar.subheader("💬 聊天设置")

        # 温度参数
        st.session_state.chat_settings['temperature'] = slider_with_value(
            "创造性",
            0.0, 2.0,
            st.session_state.chat_settings['temperature'],
            help_text="较高的值使回复更有创造性"
        )

        # 最大token数
        max_tokens = st.sidebar.slider(
            "最大回复长度",
            min_value=100,
            max_value=4096,
            value=st.session_state.chat_settings['max_tokens'],
            step=100,
            help_text="限制AI回复的最大长度"
        )
        st.session_state.chat_settings['max_tokens'] = max_tokens

        # 流式输出
        stream_output = st.sidebar.checkbox(
            "流式输出",
            value=st.session_state.chat_settings['stream'],
            help_text="实时显示AI回复过程"
        )
        st.session_state.chat_settings['stream'] = stream_output

        # 系统消息设置
        st.sidebar.subheader("🤖 系统消息")
        system_message = st.sidebar.text_area(
            "系统提示",
            value=self._get_current_system_message(),
            height=100,
            help_text="设置AI助手的角色和行为"
        )

        if st.sidebar.button("应用系统消息"):
            self.chat_service.set_system_message(
                st.session_state.current_session_id,
                system_message
            )
            show_success("系统消息已更新")

    def _get_current_system_message(self) -> str:
        """获取当前系统消息"""
        try:
            history = self.chat_service.get_session_history(
                st.session_state.current_session_id,
                include_system=True
            )
            system_messages = [msg for msg in history if msg['role'] == 'system']
            return system_messages[0]['content'] if system_messages else ""
        except:
            return ""

    def _render_messages(self):
        """渲染聊天消息"""
        # 消息容器
        messages_container = st.container()

        with messages_container:
            # 显示所有消息
            for i, message in enumerate(st.session_state.chat_messages):
                self._render_message(message, i)

            # 自动滚动到底部
            if st.session_state.chat_messages:
                st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)

    def _render_message(self, message: Dict, index: int):
        """渲染单个消息"""
        role = message['role']
        content = message['content']
        timestamp = message.get('timestamp', '')

        if role == 'user':
            # 用户消息 - 右对齐
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                <div style="background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; max-width: 80%; margin-left: auto;">
                    <strong>你:</strong>
                    <br>{content}
                    <br><small style="color: #666;">{timestamp}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif role == 'assistant':
            # AI消息 - 左对齐
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 1rem;">
                <div style="background-color: #f5f5f5; padding: 1rem; border-radius: 0.5rem; max-width: 80%;">
                    <strong>🤖 AI助手:</strong>
                    <br>{content}
                    <br><small style="color: #666;">{timestamp}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 添加操作按钮
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("📋 复制", key=f"copy_{index}"):
                    st.write("已复制到剪贴板")  # 在实际应用中需要实现复制功能
            with col2:
                if st.button("👍", key=f"like_{index}"):
                    st.write("感谢您的反馈！")
            with col3:
                if st.button("🔄 重新生成", key=f"regenerate_{index}"):
                    self._regenerate_response(index)

    def _render_input_area(self):
        """渲染输入区域"""
        st.divider()

        # 输入框
        user_input = st.chat_input(
            "请输入您的消息...",
            key="chat_input"
        )

        if user_input:
            self._handle_user_input(user_input)

    def _handle_user_input(self, user_input: str):
        """处理用户输入"""
        if not user_input.strip():
            return

        # 添加用户消息
        user_message = {
            'role': 'user',
            'content': user_input,
            'timestamp': time.strftime('%H:%M:%S')
        }
        st.session_state.chat_messages.append(user_message)

        # 生成AI回复
        self._generate_ai_response(user_input)

    def _generate_ai_response(self, user_input: str):
        """生成AI回复"""
        try:
            settings = st.session_state.chat_settings

            with loading_spinner("AI正在思考..."):
                if settings['stream']:
                    # 流式生成
                    self._stream_response(user_input, settings)
                else:
                    # 非流式生成
                    self._single_response(user_input, settings)

        except AIAssistantError as e:
            show_error(f"AI回复生成失败: {e}")
        except Exception as e:
            self.logger.error(f"生成回复时发生未知错误: {e}", exc_info=True)
            show_error(f"生成回复时发生错误: {e}")

    def _single_response(self, user_input: str, settings: Dict):
        """非流式生成回复"""
        response = asyncio.run(
            self.chat_service.chat(
                message=user_input,
                session_id=st.session_state.current_session_id,
                temperature=settings['temperature'],
                max_tokens=settings['max_tokens'],
                stream=False
            )
        )

        ai_message = {
            'role': 'assistant',
            'content': response,
            'timestamp': time.strftime('%H:%M:%S')
        }
        st.session_state.chat_messages.append(ai_message)
        st.rerun()

    def _stream_response(self, user_input: str, settings: Dict):
        """流式生成回复"""
        # 创建临时消息容器
        message_placeholder = st.empty()
        full_response = ""

        # 流式生成回复
        response_stream = asyncio.run(
            self.chat_service.chat_stream(
                message=user_input,
                session_id=st.session_state.current_session_id,
                temperature=settings['temperature'],
                max_tokens=settings['max_tokens']
            )
        )

        # 实时显示回复
        for chunk in response_stream:
            full_response += chunk
            message_placeholder.markdown(f"""
            <div style="background-color: #f5f5f5; padding: 1rem; border-radius: 0.5rem; max-width: 80%;">
                <strong>🤖 AI助手:</strong>
                <br>{full_response}
                <div class="typing-indicator">▌</div>
            </div>
            """, unsafe_allow_html=True)

        # 移除输入指示器并保存完整回复
        message_placeholder.markdown(f"""
        <div style="background-color: #f5f5f5; padding: 1rem; border-radius: 0.5rem; max-width: 80%;">
            <strong>🤖 AI助手:</strong>
            <br>{full_response}
            <br><small style="color: #666;">{time.strftime('%H:%M:%S')}</small>
        </div>
        """, unsafe_allow_html=True)

        # 保存到会话状态
        ai_message = {
            'role': 'assistant',
            'content': full_response,
            'timestamp': time.strftime('%H:%M:%S')
        }
        st.session_state.chat_messages.append(ai_message)

    def _regenerate_response(self, message_index: int):
        """重新生成回复"""
        if message_index <= 0:
            show_error("无法重新生成第一条消息")
            return

        # 找到对应的用户消息
        user_message = None
        for i in range(message_index - 1, -1, -1):
            if st.session_state.chat_messages[i]['role'] == 'user':
                user_message = st.session_state.chat_messages[i]
                break

        if not user_message:
            show_error("找不到对应的用户消息")
            return

        # 删除原AI回复
        st.session_state.chat_messages = st.session_state.chat_messages[:message_index]

        # 重新生成回复
        self._generate_ai_response(user_message['content'])

    def _render_session_management(self):
        """渲染会话管理"""
        st.subheader("💾 会话管理")

        # 当前会话ID
        st.info(f"当前会话: {st.session_state.current_session_id}")

        # 新建会话
        new_session_name = st.text_input("新会话名称", key="new_session_name")
        if st.button("➕ 新建会话"):
            if new_session_name.strip():
                st.session_state.current_session_id = new_session_name.strip()
                st.session_state.chat_messages = []
                show_success(f"已创建新会话: {new_session_name}")
                st.rerun()

        # 会话列表
        sessions = self.chat_service.list_sessions()
        if sessions:
            st.subheader("📂 会话列表")
            selected_session = st.selectbox(
                "选择会话",
                options=sessions,
                index=sessions.index(st.session_state.current_session_id) if st.session_state.current_session_id in sessions else 0
            )

            if selected_session != st.session_state.current_session_id:
                st.session_state.current_session_id = selected_session
                self._load_session_messages(selected_session)
                st.rerun()

        # 清除历史
        if st.button("🗑️ 清除当前会话历史"):
            if button_with_confirmation("确认清除", "这将删除当前会话的所有消息"):
                self.chat_service.clear_session_history(st.session_state.current_session_id)
                st.session_state.chat_messages = []
                show_success("会话历史已清除")
                st.rerun()

        # 删除会话
        if st.button("🔥 删除当前会话"):
            if button_with_confirmation("确认删除", "这将永久删除当前会话"):
                self.chat_service.delete_session(st.session_state.current_session_id)
                st.session_state.current_session_id = "default"
                st.session_state.chat_messages = []
                show_success("会话已删除")
                st.rerun()

    def _load_session_messages(self, session_id: str):
        """加载会话消息"""
        try:
            history = self.chat_service.get_session_history(session_id)
            messages = []

            for msg in history:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': time.strftime('%H:%M:%S')
                })

            st.session_state.chat_messages = messages
        except Exception as e:
            self.logger.error(f"加载会话消息失败: {e}")
            st.session_state.chat_messages = []