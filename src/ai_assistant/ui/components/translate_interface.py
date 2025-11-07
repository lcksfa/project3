"""
翻译界面组件

提供语言翻译功能的用户界面。
"""

import streamlit as st
import asyncio
from typing import Optional, Tuple
import time

from ...services.translate_service import TranslationService, TranslationStyle
from ...core.exceptions import AIAssistantError
from .common import (
    show_error, show_success, show_info, loading_spinner,
    text_input_area, selectbox_with_search, file_upload_area,
    copy_to_clipboard_button, button_with_confirmation
)


class TranslateInterface:
    """翻译界面类"""

    def __init__(self, translate_service: TranslationService):
        self.translate_service = translate_service
        self.logger = self._get_logger()

    def _get_logger(self):
        """获取日志记录器"""
        from ...core.logger import get_logger
        return get_logger("translate_ui")

    def render(self):
        """渲染翻译界面"""
        st.markdown("### 🌍 智能语言翻译")
        st.markdown("支持多种语言之间的高质量翻译，保持原文语义和风格。")

        # 初始化会话状态
        self._init_session_state()

        # 布局
        self._render_layout()

        # 功能特性
        self._render_features_section()

    def _init_session_state(self):
        """初始化会话状态"""
        if 'translate_text_input' not in st.session_state:
            st.session_state.translate_text_input = ""

        if 'translate_result' not in st.session_state:
            st.session_state.translate_result = ""

        if 'translate_settings' not in st.session_state:
            st.session_state.translate_settings = {
                'source_language': '自动检测',
                'target_language': 'English',
                'style': TranslationStyle.CASUAL,
                'preserve_formatting': True,
                'context': '',
                'temperature': 0.3
            }

        if 'translation_history' not in st.session_state:
            st.session_state.translation_history = []

    def _render_layout(self):
        """渲染主布局"""
        # 语言选择区域
        self._render_language_selection()

        # 文本输入输出区域
        col1, col2 = st.columns([1, 1])

        with col1:
            self._render_input_section()

        with col2:
            self._render_output_section()

        # 操作按钮
        self._render_action_buttons()

        # 设置区域
        with st.expander("⚙️ 翻译设置", expanded=False):
            self._render_settings_section()

        # 历史记录
        if st.session_state.translation_history:
            with st.expander("📜 翻译历史", expanded=False):
                self._render_history_section()

    def _render_language_selection(self):
        """渲染语言选择区域"""
        st.subheader("🌐 语言选择")

        # 获取支持的语言
        supported_languages = self.translate_service.get_supported_languages()
        supported_languages.insert(0, "自动检测")  # 添加自动检测选项

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # 源语言
            source_language = st.selectbox(
                "源语言",
                options=supported_languages,
                index=0,
                key="source_language_select"
            )

            # 如果选择自动检测，在输入文本后进行检测
            if source_language == "自动检测" and st.session_state.translate_text_input:
                detected_language = self.translate_service.detect_language(st.session_state.translate_text_input)
                st.info(f"🔍 检测到语言: {detected_language}")

        with col2:
            # 语言交换按钮
            st.markdown("<br>", unsafe_allow_html=True)  # 添加垂直间距
            if st.button("⇄ 交换语言", key="swap_languages"):
                self._swap_languages()

        with col3:
            # 目标语言
            target_language = st.selectbox(
                "目标语言",
                options=supported_languages[1:],  # 排除"自动检测"
                index=1 if len(supported_languages) > 1 else 0,
                key="target_language_select"
            )

        # 更新设置
        st.session_state.translate_settings['source_language'] = source_language
        st.session_state.translate_settings['target_language'] = target_language

    def _render_input_section(self):
        """渲染输入区域"""
        st.markdown("#### 📝 原文")

        # 输入方式选择
        input_method = st.radio(
            "输入方式",
            ["文本输入", "文件上传"],
            key="translate_input_method",
            horizontal=True
        )

        if input_method == "文本输入":
            # 文本输入
            text_input = text_input_area(
                "请输入要翻译的文本",
                placeholder="在此输入或粘贴您要翻译的文本...",
                height=200,
                max_chars=5000,
                key="translate_text_input"
            )

            # 文本统计
            if text_input:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("字符数", len(text_input))
                with col2:
                    st.metric("词数", len(text_input.split()))

        else:
            # 文件上传
            uploaded_file = file_upload_area(
                "上传文本文件",
                "支持 .txt, .md 格式的文件",
                accepted_types=['txt', 'md'],
                key="translate_file_upload"
            )

            if uploaded_file is not None:
                try:
                    content = uploaded_file.read().decode('utf-8')
                    st.session_state.translate_text_input = content
                    st.success(f"文件 '{uploaded_file.name}' 上传成功")
                except Exception as e:
                    show_error(f"文件读取失败: {e}")

    def _render_output_section(self):
        """渲染输出区域"""
        st.markdown("#### 📄 译文")

        if st.session_state.translate_result:
            # 显示翻译结果
            st.text_area(
                "翻译结果",
                value=st.session_state.translate_result,
                height=200,
                key="translate_result_display"
            )

            # 操作按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📋 复制译文", key="copy_translation"):
                    st.success("译文已复制到剪贴板")

            with col2:
                if st.button("💾 下载译文", key="download_translation"):
                    self._download_translation()

            with col3:
                if st.button("🔄 重新翻译", key="retranslate"):
                    self._translate_text()

            # 统计信息
            col1, col2 = st.columns(2)
            with col1:
                st.metric("译文字符数", len(st.session_state.translate_result))
            with col2:
                if st.session_state.translate_text_input:
                    ratio = len(st.session_state.translate_result) / len(st.session_state.translate_text_input)
                    st.metric("长度比", f"{ratio:.2f}")
        else:
            # 占位符
            st.text_area(
                "翻译结果将显示在这里",
                value="",
                height=200,
                disabled=True,
                key="translate_result_placeholder"
            )

    def _render_action_buttons(self):
        """渲染操作按钮"""
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # 翻译按钮
            if st.button(
                "🚀 开始翻译",
                type="primary",
                use_container_width=True,
                disabled=not st.session_state.translate_text_input.strip()
            ):
                self._translate_text()

        with col2:
            # 清除按钮
            if st.button("🗑️ 清除内容", use_container_width=True):
                self._clear_content()

        with col3:
            # 批量翻译按钮
            if st.button("📋 批量翻译", use_container_width=True):
                st.session_state.show_batch_translate = True

        # 批量翻译模态框
        if st.session_state.get('show_batch_translate', False):
            self._render_batch_translate_modal()

    def _render_settings_section(self):
        """渲染设置区域"""
        # 翻译风格
        styles = {
            "随意": TranslationStyle.CASUAL,
            "正式": TranslationStyle.FORMAL,
            "专业": TranslationStyle.PROFESSIONAL,
            "文学": TranslationStyle.LITERARY,
            "技术": TranslationStyle.TECHNICAL
        }

        selected_style_name = st.selectbox(
            "翻译风格",
            options=list(styles.keys()),
            index=0,
            help="选择翻译的语言风格"
        )
        st.session_state.translate_settings['style'] = styles[selected_style_name]

        # 保留格式
        preserve_formatting = st.checkbox(
            "保留原文格式",
            value=st.session_state.translate_settings['preserve_formatting'],
            help="尽量保留原文的段落结构和格式"
        )
        st.session_state.translate_settings['preserve_formatting'] = preserve_formatting

        # 上下文信息
        context = st.text_area(
            "上下文信息（可选）",
            value=st.session_state.translate_settings['context'],
            height=100,
            help="提供相关背景信息，有助于提高翻译准确性"
        )
        st.session_state.translate_settings['context'] = context

        # 温度参数
        temperature = st.slider(
            "创造性",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.translate_settings['temperature'],
            step=0.1,
            help="控制翻译的创造性，较低值更注重准确性"
        )
        st.session_state.translate_settings['temperature'] = temperature

    def _render_history_section(self):
        """渲染历史记录区域"""
        history = st.session_state.translation_history

        for i, record in enumerate(reversed(history[-5:])):  # 只显示最近5条
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**{record['source_language']} → {record['target_language']}**")
                    st.text_area(
                        "原文",
                        value=record['original_text'][:100] + "..." if len(record['original_text']) > 100 else record['original_text'],
                        height=80,
                        disabled=True,
                        key=f"history_original_{i}"
                    )

                with col2:
                    st.text_area(
                        "译文",
                        value=record['translated_text'][:100] + "..." if len(record['translated_text']) > 100 else record['translated_text'],
                        height=80,
                        disabled=True,
                        key=f"history_translated_{i}"
                    )

                with col3:
                    st.write(record['timestamp'])
                    if st.button("📋 使用", key=f"use_history_{i}"):
                        st.session_state.translate_text_input = record['original_text']
                        st.session_state.translate_result = record['translated_text']
                        st.rerun()

                st.divider()

        # 清除历史记录
        if st.button("🗑️ 清除历史记录"):
            if button_with_confirmation("确认清除", "这将删除所有翻译历史"):
                st.session_state.translation_history = []
                show_success("历史记录已清除")
                st.rerun()

    def _render_features_section(self):
        """渲染功能特性区域"""
        st.markdown("---")
        st.markdown("#### ✨ 功能特性")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("支持语言", len(self.translate_service.get_supported_languages()))

        with col2:
            st.metric("翻译风格", 5)

        with col3:
            st.metric("批量处理", "支持")

        with col4:
            st.metric("格式保留", "智能")

        # 语言支持说明
        with st.expander("🌍 支持的语言", expanded=False):
            languages = self.translate_service.get_supported_languages()
            for i in range(0, len(languages), 3):
                cols = st.columns(3)
                for j, lang in enumerate(languages[i:i+3]):
                    with cols[j]:
                        st.write(f"• {lang}")

    def _swap_languages(self):
        """交换源语言和目标语言"""
        source = st.session_state.translate_settings['source_language']
        target = st.session_state.translate_settings['target_language']

        # 不能交换自动检测
        if source == "自动检测":
            show_error("不能交换自动检测语言")
            return

        # 交换语言
        st.session_state.translate_settings['source_language'] = target
        st.session_state.translate_settings['target_language'] = source

        # 交换文本
        st.session_state.translate_text_input, st.session_state.translate_result = \
            st.session_state.translate_result, st.session_state.translate_text_input

        # 更新选择框
        st.session_state.source_language_select = target
        st.session_state.target_language_select = source

        show_success("语言已交换")
        st.rerun()

    def _translate_text(self):
        """执行翻译"""
        if not st.session_state.translate_text_input.strip():
            show_error("请输入要翻译的文本")
            return

        try:
            settings = st.session_state.translate_settings

            # 处理自动检测
            source_language = settings['source_language']
            if source_language == "自动检测":
                source_language = self.translate_service.detect_language(st.session_state.translate_text_input)

            with loading_spinner("正在翻译..."):
                result = asyncio.run(
                    self.translate_service.translate(
                        text=st.session_state.translate_text_input,
                        source_language=source_language,
                        target_language=settings['target_language'],
                        style=settings['style'],
                        preserve_formatting=settings['preserve_formatting'],
                        context=settings['context'],
                        temperature=settings['temperature']
                    )
                )

                # 保存结果
                st.session_state.translate_result = result

                # 添加到历史记录
                self._add_to_history(
                    original_text=st.session_state.translate_text_input,
                    translated_text=result,
                    source_language=source_language,
                    target_language=settings['target_language']
                )

                show_success("翻译完成！")
                st.rerun()

        except AIAssistantError as e:
            show_error(f"翻译失败: {e}")
        except Exception as e:
            self.logger.error(f"翻译时发生未知错误: {e}", exc_info=True)
            show_error(f"翻译时发生错误: {e}")

    def _clear_content(self):
        """清除内容"""
        st.session_state.translate_text_input = ""
        st.session_state.translate_result = ""
        show_success("内容已清除")

    def _download_translation(self):
        """下载翻译结果"""
        if not st.session_state.translate_result:
            show_error("没有可下载的译文")
            return

        try:
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            source_lang = st.session_state.translate_settings['source_language'][:2]
            target_lang = st.session_state.translate_settings['target_language'][:2]
            filename = f"translation_{source_lang}_to_{target_lang}_{timestamp}.txt"

            # 创建下载链接
            st.download_button(
                label="💾 下载译文",
                data=st.session_state.translate_result,
                file_name=filename,
                mime="text/plain"
            )

        except Exception as e:
            show_error(f"下载失败: {e}")

    def _add_to_history(self, original_text: str, translated_text: str, source_language: str, target_language: str):
        """添加到历史记录"""
        record = {
            'original_text': original_text,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        st.session_state.translation_history.append(record)

        # 限制历史记录数量
        if len(st.session_state.translation_history) > 50:
            st.session_state.translation_history = st.session_state.translation_history[-50:]

    def _render_batch_translate_modal(self):
        """渲染批量翻译模态框"""
        st.markdown("#### 📋 批量翻译")

        # 批量输入
        batch_input = st.text_area(
            "批量文本（每行一条）",
            height=200,
            placeholder="请输入要批量翻译的文本，每行一条...",
            key="batch_translate_input"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 开始批量翻译", type="primary"):
                self._batch_translate()

        with col2:
            if st.button("❌ 关闭"):
                st.session_state.show_batch_translate = False
                st.rerun()

    def _batch_translate(self):
        """批量翻译"""
        batch_input = st.session_state.get('batch_translate_input', '')
        if not batch_input.strip():
            show_error("请输入要批量翻译的文本")
            return

        try:
            lines = [line.strip() for line in batch_input.split('\n') if line.strip()]
            if not lines:
                show_error("没有有效的文本行")
                return

            settings = st.session_state.translate_settings

            with loading_spinner(f"正在批量翻译 {len(lines)} 条文本..."):
                results = asyncio.run(
                    self.translate_service.batch_translate(
                        texts=lines,
                        source_language=settings['source_language'],
                        target_language=settings['target_language'],
                        style=settings['style'],
                        temperature=settings['temperature'],
                        concurrent_limit=3
                    )
                )

                # 显示结果
                st.success("批量翻译完成！")

                for i, (original, translated) in enumerate(zip(lines, results)):
                    with st.expander(f"第 {i+1} 条", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.text_area("原文", value=original, height=100, disabled=True)
                        with col2:
                            st.text_area("译文", value=translated, height=100)

        except Exception as e:
            show_error(f"批量翻译失败: {e}")