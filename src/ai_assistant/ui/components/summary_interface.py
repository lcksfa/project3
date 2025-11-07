"""
文本总结界面组件

提供文本总结功能的用户界面。
"""

import streamlit as st
import asyncio
from typing import Optional
import time

from ...services.summary_service import SummaryService, SummaryType
from ...core.exceptions import AIAssistantError
from .common import (
    show_error, show_success, show_info, loading_spinner,
    text_input_area, selectbox_with_search, expandable_section,
    file_upload_area, copy_to_clipboard_button
)


class SummaryInterface:
    """文本总结界面类"""

    def __init__(self, summary_service: SummaryService):
        self.summary_service = summary_service
        self.logger = self._get_logger()

    def _get_logger(self):
        """获取日志记录器"""
        from ...core.logger import get_logger
        return get_logger("summary_ui")

    def render(self):
        """渲染总结界面"""
        st.markdown("### 📝 智能文本总结")
        st.markdown("将长文本智能总结为简洁的要点、段落或关键洞察。")

        # 初始化会话状态
        self._init_session_state()

        # 布局
        col1, col2 = st.columns([2, 1])

        with col1:
            # 输入区域
            self._render_input_section()

        with col2:
            # 设置区域
            self._render_settings_section()

        # 结果区域
        self._render_result_section()

        # 示例文本
        self._render_examples_section()

    def _init_session_state(self):
        """初始化会话状态"""
        if 'summary_text_input' not in st.session_state:
            st.session_state.summary_text_input = ""

        if 'summary_result' not in st.session_state:
            st.session_state.summary_result = ""

        if 'summary_settings' not in st.session_state:
            st.session_state.summary_settings = {
                'summary_type': SummaryType.PARAGRAPH,
                'max_length': 500,
                'language': '中文',
                'focus_areas': [],
                'temperature': 0.3
            }

    def _render_input_section(self):
        """渲染输入区域"""
        st.subheader("📄 输入文本")

        # 文本输入方式选择
        input_method = st.radio(
            "输入方式",
            ["文本输入", "文件上传"],
            horizontal=True
        )

        if input_method == "文本输入":
            # 文本输入框
            text_input = text_input_area(
                "请输入要总结的文本",
                placeholder="在此粘贴或输入您要总结的文本...",
                height=300,
                max_chars=10000,
                key="summary_text_input"
            )

            # 文本统计
            if text_input:
                self._show_text_stats(text_input)

        else:
            # 文件上传
            uploaded_file = file_upload_area(
                "上传文本文件",
                "支持 .txt, .md 格式的文件",
                accepted_types=['txt', 'md'],
                key="summary_file_upload"
            )

            if uploaded_file is not None:
                try:
                    # 读取文件内容
                    content = uploaded_file.read().decode('utf-8')
                    st.session_state.summary_text_input = content
                    st.success(f"文件 '{uploaded_file.name}' 上传成功")
                    self._show_text_stats(content)
                except Exception as e:
                    show_error(f"文件读取失败: {e}")

        # 总结按钮
        if st.button(
            "🚀 开始总结",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.summary_text_input.strip()
        ):
            self._generate_summary()

    def _show_text_stats(self, text: str):
        """显示文本统计"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("字符数", len(text))

        with col2:
            word_count = len(text.split())
            st.metric("词数", word_count)

        with col3:
            sentence_count = text.count('.') + text.count('!') + text.count('?') + text.count('。') + text.count('！') + text.count('？')
            st.metric("句子数", sentence_count)

        with col4:
            # 估算阅读时间（假设每分钟阅读200字）
            reading_time = max(1, len(text) // 200)
            st.metric("阅读时间", f"{reading_time}分钟")

    def _render_settings_section(self):
        """渲染设置区域"""
        st.subheader("⚙️ 总结设置")

        # 总结类型
        summary_types = {
            "段落总结": SummaryType.PARAGRAPH,
            "要点总结": SummaryType.BULLET_POINTS,
            "关键洞察": SummaryType.KEY_INSIGHTS,
            "执行总结": SummaryType.EXECUTIVE,
            "详细总结": SummaryType.DETAILED
        }

        selected_type_name = st.selectbox(
            "总结类型",
            options=list(summary_types.keys()),
            index=0,
            help="选择总结的格式和详细程度"
        )

        st.session_state.summary_settings['summary_type'] = summary_types[selected_type_name]

        # 语言选择
        languages = ["中文", "English", "日本語", "Español", "Français", "Deutsch"]
        selected_language = st.selectbox(
            "输出语言",
            options=languages,
            index=0,
            help="选择总结输出的语言"
        )
        st.session_state.summary_settings['language'] = selected_language

        # 最大长度
        max_length = st.slider(
            "最大长度",
            min_value=100,
            max_value=2000,
            value=st.session_state.summary_settings['max_length'],
            step=50,
            help="限制总结的最大字符数"
        )
        st.session_state.summary_settings['max_length'] = max_length

        # 温度参数
        temperature = st.slider(
            "创造性",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.summary_settings['temperature'],
            step=0.1,
            help="控制总结的创造性，较低值更注重准确性"
        )
        st.session_state.summary_settings['temperature'] = temperature

        # 重点关注领域
        st.subheader("🎯 重点关注")
        focus_areas_input = st.text_input(
            "关注领域（可选）",
            placeholder="例如：技术、商业、教育...",
            help="指定需要特别关注的方面，用逗号分隔"
        )

        if focus_areas_input:
            focus_areas = [area.strip() for area in focus_areas_input.split(',') if area.strip()]
            st.session_state.summary_settings['focus_areas'] = focus_areas
            st.write(f"已设置关注领域: {', '.join(focus_areas)}")

    def _render_result_section(self):
        """渲染结果区域"""
        if st.session_state.summary_result:
            st.subheader("📋 总结结果")

            # 结果显示
            result_container = st.container()
            with result_container:
                st.markdown(st.session_state.summary_result)

                # 操作按钮
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📋 复制结果"):
                        st.success("结果已复制到剪贴板")

                with col2:
                    if st.button("💾 保存结果"):
                        self._save_result()

                with col3:
                    if st.button("🔄 重新总结"):
                        self._generate_summary()

            # 统计信息
            self._show_result_stats()

    def _show_result_stats(self):
        """显示结果统计"""
        if st.session_state.summary_result:
            col1, col2, col3 = st.columns(3)

            original_length = len(st.session_state.summary_text_input)
            summary_length = len(st.session_state.summary_result)
            compression_ratio = (1 - summary_length / original_length) * 100 if original_length > 0 else 0

            with col1:
                st.metric("原文长度", original_length)

            with col2:
                st.metric("总结长度", summary_length)

            with col3:
                st.metric("压缩率", f"{compression_ratio:.1f}%")

    def _render_examples_section(self):
        """渲染示例文本区域"""
        with st.expander("📚 示例文本", expanded=False):
            example_texts = {
                "技术文章": """
                人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
                这些任务包括学习、推理、问题解决、感知和语言理解。AI技术包括机器学习、深度学习、
                自然语言处理、计算机视觉等。近年来，AI在医疗诊断、自动驾驶、金融分析等领域
                取得了重大突破，正在改变我们的生活方式和工作模式。
                """,

                "商业报告": """
                2024年第三季度，公司营收达到5.2亿美元，同比增长15%。净利润为8000万美元，
                同比增长12%。主要增长动力来自云服务业务，该部门营收增长25%。传统业务保持稳定，
                新兴市场表现突出。公司预计第四季度将继续保持增长态势，全年营收有望超过20亿美元。
                """,

                "科学研究": """
                一项发表在《自然》杂志上的研究显示，科学家们发现了一种新的材料，
                能够在室温下实现超导。这种材料是由特定比例的氢、硫和碳组成的化合物。
                如果这一发现得到验证，将彻底改变能源传输和存储技术，对电力系统、
                磁悬浮列车等领域产生深远影响。
                """
            }

            selected_example = st.selectbox(
                "选择示例文本",
                options=list(example_texts.keys())
            )

            st.text_area(
                "示例内容",
                value=example_texts[selected_example],
                height=200,
                disabled=True
            )

            if st.button("使用此示例"):
                st.session_state.summary_text_input = example_texts[selected_example]
                st.rerun()

    def _generate_summary(self):
        """生成总结"""
        if not st.session_state.summary_text_input.strip():
            show_error("请输入要总结的文本")
            return

        try:
            settings = st.session_state.summary_settings

            with loading_spinner("正在生成总结..."):
                result = asyncio.run(
                    self.summary_service.summarize(
                        text=st.session_state.summary_text_input,
                        summary_type=settings['summary_type'],
                        max_length=settings['max_length'],
                        language=settings['language'],
                        focus_areas=settings['focus_areas'],
                        temperature=settings['temperature']
                    )
                )

                st.session_state.summary_result = result
                show_success("总结生成完成！")
                st.rerun()

        except AIAssistantError as e:
            show_error(f"总结生成失败: {e}")
        except Exception as e:
            self.logger.error(f"生成总结时发生未知错误: {e}", exc_info=True)
            show_error(f"生成总结时发生错误: {e}")

    def _save_result(self):
        """保存结果"""
        if not st.session_state.summary_result:
            show_error("没有可保存的结果")
            return

        try:
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.txt"

            # 创建下载链接
            st.download_button(
                label="💾 下载总结结果",
                data=st.session_state.summary_result,
                file_name=filename,
                mime="text/plain"
            )

            show_success("文件已准备好下载")

        except Exception as e:
            show_error(f"保存失败: {e}")