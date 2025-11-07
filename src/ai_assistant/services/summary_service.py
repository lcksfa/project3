"""
文本总结服务模块

提供智能文本总结功能。
"""

from typing import List, Dict, Optional
from enum import Enum
import asyncio

from .deepseek_client import DeepSeekClient, Message, ChatCompletionRequest
from ..core.config_simple import get_settings
from ..core.logger import get_logger
from ..core.exceptions import ValidationError, ServiceError
from ..utils.validators import validate_text_input, validate_temperature, validate_max_tokens
from ..utils.helpers import truncate_text, Timer, generate_request_id, clean_text


class SummaryType(str, Enum):
    """总结类型枚举"""
    BULLET_POINTS = "bullet_points"  # 要点总结
    PARAGRAPH = "paragraph"         # 段落总结
    KEY_INSIGHTS = "key_insights"   # 关键洞察
    EXECUTIVE = "executive"         # 执行总结
    DETAILED = "detailed"          # 详细总结


class SummaryRequest:
    """总结请求对象"""

    def __init__(
        self,
        text: str,
        summary_type: SummaryType = SummaryType.PARAGRAPH,
        max_length: Optional[int] = None,
        language: str = "中文",
        focus_areas: Optional[List[str]] = None
    ):
        self.text = text
        self.summary_type = summary_type
        self.max_length = max_length
        self.language = language
        self.focus_areas = focus_areas or []


class SummaryService:
    """文本总结服务"""

    def __init__(self, client: Optional[DeepSeekClient] = None):
        self.client = client or DeepSeekClient()
        self.settings = get_settings()
        self.logger = get_logger("summary_service")

        # 预定义的提示模板
        self.prompts = {
            SummaryType.BULLET_POINTS: self._get_bullet_points_prompt,
            SummaryType.PARAGRAPH: self._get_paragraph_prompt,
            SummaryType.KEY_INSIGHTS: self._get_key_insights_prompt,
            SummaryType.EXECUTIVE: self._get_executive_prompt,
            SummaryType.DETAILED: self._get_detailed_prompt,
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def summarize(
        self,
        text: str,
        summary_type: SummaryType = SummaryType.PARAGRAPH,
        max_length: Optional[int] = None,
        language: str = "中文",
        focus_areas: Optional[List[str]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        总结文本

        Args:
            text: 待总结的文本
            summary_type: 总结类型
            max_length: 最大长度
            language: 输出语言
            focus_areas: 重点关注领域
            temperature: 温度参数

        Returns:
            总结后的文本

        Raises:
            ValidationError: 输入验证失败
            ServiceError: 服务处理失败
        """
        # 验证输入
        text = validate_text_input(
            text,
            min_length=50,
            max_length=self.settings.services.max_input_length
        )

        if max_length is not None:
            max_length = validate_max_tokens(max_length)

        if temperature is not None:
            temperature = validate_temperature(temperature)

        request_id = generate_request_id()
        request = SummaryRequest(
            text=text,
            summary_type=summary_type,
            max_length=max_length,
            language=language,
            focus_areas=focus_areas
        )

        self.logger.info(
            "处理文本总结请求",
            request_id=request_id,
            summary_type=summary_type.value,
            text_length=len(text),
            language=language,
            max_length=max_length
        )

        try:
            with Timer(f"文本总结 {request_id}"):
                # 检查文本是否需要分段处理
                if len(text) > 8000:  # 如果文本过长，分段处理
                    summary = await self._summarize_long_text(request, request_id)
                else:
                    summary = await self._summarize_single_text(request, request_id)

                self.logger.info(
                    "文本总结完成",
                    request_id=request_id,
                    summary_length=len(summary)
                )

                return summary

        except Exception as e:
            self.logger.error(
                "文本总结失败",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise ServiceError(f"文本总结失败: {e}")

    async def _summarize_single_text(self, request: SummaryRequest, request_id: str) -> str:
        """处理单个文本的总结"""
        # 生成系统提示
        system_prompt = self.prompts[request.summary_type](request)

        # 构建消息
        messages = [
            self.client.create_system_message(system_prompt),
            self.client.create_user_message(request.text)
        ]

        # 准备API请求
        api_request = ChatCompletionRequest(
            model=self.settings.deepseek.model,
            messages=messages,
            temperature=temperature or self.settings.services.temperature,
            max_tokens=request.max_length or self.settings.services.max_summary_length
        )

        # 发送请求
        response = await self.client.chat_completion(api_request, request_id)

        if not response.choices or not response.choices[0]["message"]:
            raise ServiceError("API返回空响应")

        return response.choices[0]["message"]["content"].strip()

    async def _summarize_long_text(self, request: SummaryRequest, request_id: str) -> str:
        """处理长文本的总结"""
        self.logger.info(
            "开始分段总结长文本",
            request_id=request_id,
            text_length=len(request.text)
        )

        # 将文本分成段落
        paragraphs = self._split_text_into_paragraphs(request.text)
        chunk_size = 3  # 每次处理3个段落
        summaries = []

        # 分批处理
        for i in range(0, len(paragraphs), chunk_size):
            chunk = paragraphs[i:i + chunk_size]
            chunk_text = "\n\n".join(chunk)

            # 创建段落总结请求
            chunk_request = SummaryRequest(
                text=chunk_text,
                summary_type=SummaryType.PARAGRAPH,
                max_length=min(500, request.max_length or 500),
                language=request.language,
                focus_areas=request.focus_areas
            )

            chunk_summary = await self._summarize_single_text(chunk_request, f"{request_id}_chunk_{i}")
            summaries.append(chunk_summary)

            # 添加延迟以避免API限制
            await asyncio.sleep(0.5)

        # 合并段落总结
        combined_summary = "\n\n".join(summaries)

        # 如果总结仍然很长，进行最终总结
        if len(combined_summary) > (request.max_length or 1000):
            final_request = SummaryRequest(
                text=combined_summary,
                summary_type=request.summary_type,
                max_length=request.max_length,
                language=request.language,
                focus_areas=request.focus_areas
            )
            return await self._summarize_single_text(final_request, f"{request_id}_final")

        return combined_summary

    def _split_text_into_paragraphs(self, text: str) -> List[str]:
        """将文本分割成段落"""
        import re

        # 清理文本
        text = clean_text(text)

        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)

        # 过滤空段落和过短的段落
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]

        return paragraphs

    def _get_bullet_points_prompt(self, request: SummaryRequest) -> str:
        """生成要点总结的提示"""
        prompt = f"""你是一个专业的文本总结专家。请将以下文本总结为简洁的要点形式。

要求：
1. 使用项目符号（- 或 •）列出要点
2. 每个要点不超过{request.max_length or 50}个字符
3. 提取最重要的信息和关键数据
4. 保持逻辑清晰，层次分明
5. 输出语言：{request.language}"""

        if request.focus_areas:
            prompt += f"\n6. 特别关注以下方面：{', '.join(request.focus_areas)}"

        return prompt

    def _get_paragraph_prompt(self, request: SummaryRequest) -> str:
        """生成段落总结的提示"""
        prompt = f"""你是一个专业的文本总结专家。请将以下文本总结为一个连贯的段落。

要求：
1. 段落长度控制在{request.max_length or 200}字符以内
2. 保持原文的主要信息和逻辑结构
3. 语言简洁、准确、流畅
4. 突出核心观点和重要细节
5. 输出语言：{request.language}"""

        if request.focus_areas:
            prompt += f"\n6. 特别关注以下方面：{', '.join(request.focus_areas)}"

        return prompt

    def _get_key_insights_prompt(self, request: SummaryRequest) -> str:
        """生成关键洞察的提示"""
        prompt = f"""你是一个专业的分析师。请从以下文本中提取关键洞察和有价值的信息。

要求：
1. 识别并提取最重要的洞察和观点
2. 分析趋势、模式和潜在影响
3. 突出数据支撑的关键结论
4. 使用简洁的语言表达复杂概念
5. 输出语言：{request.language}"""

        if request.focus_areas:
            prompt += f"\n6. 特别关注以下方面：{', '.join(request.focus_areas)}"

        return prompt

    def _get_executive_prompt(self, request: SummaryRequest) -> str:
        """生成执行总结的提示"""
        prompt = f"""你是一个资深的商业顾问。请为高层管理者准备一份执行总结。

要求：
1. 高度概括核心信息和关键结论
2. 突出对决策有重要影响的信息
3. 识别机会、风险和关键行动项
4. 语言简洁、专业、有影响力
5. 输出语言：{request.language}"""

        if request.focus_areas:
            prompt += f"\n6. 特别关注以下方面：{', '.join(request.focus_areas)}"

        return prompt

    def _get_detailed_prompt(self, request: SummaryRequest) -> str:
        """生成详细总结的提示"""
        prompt = f"""你是一个专业的研究员。请提供一份详细的总结，保留原文的重要细节。

要求：
1. 保留原文的主要结构和逻辑
2. 提取并整合关键信息和数据
3. 提供背景和上下文说明
4. 确保信息的完整性和准确性
5. 输出语言：{request.language}"""

        if request.focus_areas:
            prompt += f"\n6. 特别关注以下方面：{', '.join(request.focus_areas)}"

        return prompt

    async def batch_summarize(
        self,
        texts: List[str],
        summary_type: SummaryType = SummaryType.PARAGRAPH,
        max_length: Optional[int] = None,
        language: str = "中文",
        temperature: Optional[float] = None,
        concurrent_limit: int = 3
    ) -> List[str]:
        """
        批量总结文本

        Args:
            texts: 待总结的文本列表
            summary_type: 总结类型
            max_length: 最大长度
            language: 输出语言
            temperature: 温度参数
            concurrent_limit: 并发限制

        Returns:
            总结结果列表
        """
        if not texts:
            return []

        self.logger.info(
            "开始批量总结",
            text_count=len(texts),
            summary_type=summary_type.value
        )

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def summarize_single(text: str, index: int) -> tuple[int, str]:
            async with semaphore:
                try:
                    summary = await self.summarize(
                        text=text,
                        summary_type=summary_type,
                        max_length=max_length,
                        language=language,
                        temperature=temperature
                    )
                    return index, summary
                except Exception as e:
                    self.logger.error(
                        "批量总结中单个文本失败",
                        index=index,
                        error=str(e)
                    )
                    return index, f"总结失败: {e}"

        # 并发处理
        tasks = [
            summarize_single(text, i)
            for i, text in enumerate(texts)
        ]

        results = await asyncio.gather(*tasks)

        # 按索引排序结果
        results.sort(key=lambda x: x[0])
        summaries = [result[1] for result in results]

        self.logger.info(
            "批量总结完成",
            total_count=len(texts),
            success_count=len([s for s in summaries if not s.startswith("总结失败")])
        )

        return summaries