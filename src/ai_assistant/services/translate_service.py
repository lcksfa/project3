"""
翻译服务模块

提供多语言翻译功能。
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
import asyncio

from .deepseek_client import DeepSeekClient, Message, ChatCompletionRequest
from ..core.config import get_settings
from ..core.logger import get_logger
from ..core.exceptions import ValidationError, ServiceError
from ..utils.validators import validate_text_input, validate_temperature, validate_language_code
from ..utils.helpers import Timer, generate_request_id, clean_text, chunks


class LanguagePair:
    """语言对"""
    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target

    def __str__(self) -> str:
        return f"{self.source} -> {self.target}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, LanguagePair):
            return False
        return self.source == other.source and self.target == other.target

    def __hash__(self) -> int:
        return hash((self.source, self.target))


class TranslationStyle(str, Enum):
    """翻译风格"""
    FORMAL = "formal"           # 正式
    CASUAL = "casual"           # 随意
    PROFESSIONAL = "professional"  # 专业
    LITERARY = "literary"       # 文学
    TECHNICAL = "technical"     # 技术


class TranslationRequest:
    """翻译请求对象"""

    def __init__(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: TranslationStyle = TranslationStyle.CASUAL,
        preserve_formatting: bool = True,
        context: Optional[str] = None
    ):
        self.text = text
        self.source_language = source_language
        self.target_language = target_language
        self.style = style
        self.preserve_formatting = preserve_formatting
        self.context = context


class TranslationService:
    """翻译服务"""

    def __init__(self, client: Optional[DeepSeekClient] = None):
        self.client = client or DeepSeekClient()
        self.settings = get_settings()
        self.logger = get_logger("translate_service")

        # 支持的语言列表
        self.supported_languages = [
            "中文", "English", "日本語", "Español", "Français",
            "Deutsch", "한국어", "Português", "Italiano", "Русский",
            "العربية", "हिन्दी", "Türkçe", "Nederlands", "Svenska"
        ]

        # 语言代码映射
        self.language_codes = {
            "中文": "zh",
            "English": "en",
            "日本語": "ja",
            "Español": "es",
            "Français": "fr",
            "Deutsch": "de",
            "한국어": "ko",
            "Português": "pt",
            "Italiano": "it",
            "Русский": "ru",
            "العربية": "ar",
            "हिन्दी": "hi",
            "Türkçe": "tr",
            "Nederlands": "nl",
            "Svenska": "sv"
        }

        # 翻译风格提示模板
        self.style_prompts = {
            TranslationStyle.FORMAL: "请使用正式、礼貌的语言风格",
            TranslationStyle.CASUAL: "请使用自然、随意的语言风格",
            TranslationStyle.PROFESSIONAL: "请使用专业、准确的术语",
            TranslationStyle.LITERARY: "请使用优美、富有文学性的语言",
            TranslationStyle.TECHNICAL: "请使用技术术语和专业表达"
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: TranslationStyle = TranslationStyle.CASUAL,
        preserve_formatting: bool = True,
        context: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        翻译文本

        Args:
            text: 待翻译的文本
            source_language: 源语言
            target_language: 目标语言
            style: 翻译风格
            preserve_formatting: 是否保留格式
            context: 上下文信息
            temperature: 温度参数

        Returns:
            翻译后的文本

        Raises:
            ValidationError: 输入验证失败
            ServiceError: 服务处理失败
        """
        # 验证输入
        text = validate_text_input(
            text,
            min_length=1,
            max_length=self.settings.services.max_text_length
        )

        source_language = validate_language_code(
            source_language, self.supported_languages
        )
        target_language = validate_language_code(
            target_language, self.supported_languages
        )

        if temperature is not None:
            temperature = validate_temperature(temperature)

        request_id = generate_request_id()
        request = TranslationRequest(
            text=text,
            source_language=source_language,
            target_language=target_language,
            style=style,
            preserve_formatting=preserve_formatting,
            context=context
        )

        self.logger.info(
            "处理翻译请求",
            request_id=request_id,
            source_language=source_language,
            target_language=target_language,
            style=style.value,
            text_length=len(text)
        )

        try:
            with Timer(f"文本翻译 {request_id}"):
                # 检查文本是否需要分段处理
                if len(text) > 4000:  # 如果文本过长，分段处理
                    translation = await self._translate_long_text(request, request_id)
                else:
                    translation = await self._translate_single_text(request, request_id)

                self.logger.info(
                    "文本翻译完成",
                    request_id=request_id,
                    translation_length=len(translation)
                )

                return translation

        except Exception as e:
            self.logger.error(
                "文本翻译失败",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise ServiceError(f"文本翻译失败: {e}")

    async def _translate_single_text(self, request: TranslationRequest, request_id: str) -> str:
        """处理单个文本的翻译"""
        # 生成系统提示
        system_prompt = self._get_translation_prompt(request)

        # 构建消息
        user_message = self._build_user_message(request)
        messages = [
            self.client.create_system_message(system_prompt),
            self.client.create_user_message(user_message)
        ]

        # 准备API请求
        api_request = ChatCompletionRequest(
            model=self.settings.deepseek.model,
            messages=messages,
            temperature=temperature or self.settings.services.temperature,
            max_tokens=self.settings.services.max_tokens
        )

        # 发送请求
        response = await self.client.chat_completion(api_request, request_id)

        if not response.choices or not response.choices[0]["message"]:
            raise ServiceError("API返回空响应")

        translation = response.choices[0]["message"]["content"].strip()

        # 后处理：如果需要保留格式
        if request.preserve_formatting:
            translation = self._preserve_formatting(request.text, translation)

        return translation

    async def _translate_long_text(self, request: TranslationRequest, request_id: str) -> str:
        """处理长文本的翻译"""
        self.logger.info(
            "开始分段翻译长文本",
            request_id=request_id,
            text_length=len(request.text)
        )

        # 检测句子边界并分割
        segments = self._split_text_into_segments(request.text)
        translations = []

        # 分批处理
        for i, segment in enumerate(segments):
            if not segment.strip():
                translations.append("")
                continue

            # 创建分段翻译请求
            segment_request = TranslationRequest(
                text=segment,
                source_language=request.source_language,
                target_language=request.target_language,
                style=request.style,
                preserve_formatting=False,  # 分段时不保留格式
                context=request.context
            )

            segment_translation = await self._translate_single_text(
                segment_request, f"{request_id}_segment_{i}"
            )
            translations.append(segment_translation)

            # 添加延迟以避免API限制
            await asyncio.sleep(0.3)

        # 合并翻译结果
        return self._merge_translations(request.text, translations)

    def _split_text_into_segments(self, text: str) -> List[str]:
        """将文本分割成适合翻译的段落"""
        import re

        # 清理文本但保留基本格式
        text = clean_text(text)

        # 按句子分割
        sentences = re.split(r'[.!?。！？]+', text)

        # 合并短句，分割长句
        segments = []
        current_segment = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 如果当前段加入新句子后会太长，则开始新段落
            if len(current_segment) + len(sentence) > 1000:
                if current_segment:
                    segments.append(current_segment)
                current_segment = sentence
            else:
                current_segment += "。" if self._is_chinese_text(sentence) else ". " + sentence

        # 添加最后一段
        if current_segment:
            segments.append(current_segment)

        return segments

    def _is_chinese_text(self, text: str) -> bool:
        """检测文本是否主要为中文"""
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        return chinese_chars > len(text) * 0.3

    def _merge_translations(self, original_text: str, translations: List[str]) -> str:
        """合并翻译结果，尽量保持原文格式"""
        # 简单的合并策略
        result = ""
        for i, translation in enumerate(translations):
            if translation.strip():
                if result:
                    # 判断是否需要添加标点符号
                    if not translation.endswith(('.', '!', '?', '。', '！', '？')):
                        if self._is_chinese_text(translation):
                            translation += "。"
                        else:
                            translation += "."
                result += translation

        return result.strip()

    def _preserve_formatting(self, original: str, translation: str) -> str:
        """保留原文格式"""
        # 简单的格式保留策略
        # 保留段落结构
        original_paragraphs = original.split('\n\n')
        translation_paragraphs = translation.split('\n\n')

        if len(original_paragraphs) > 1 and len(translation_paragraphs) == 1:
            # 如果原文有段落但译文没有，尝试重新分段
            avg_length = len(translation) // len(original_paragraphs)
            if avg_length > 50:  # 只有当段落长度合理时才分段
                words = translation.split()
                paragraphs = []
                current_paragraph = []

                for word in words:
                    current_paragraph.append(word)
                    if len(' '.join(current_paragraph)) >= avg_length:
                        paragraphs.append(' '.join(current_paragraph))
                        current_paragraph = []

                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))

                return '\n\n'.join(paragraphs)

        return translation

    def _get_translation_prompt(self, request: TranslationRequest) -> str:
        """生成翻译提示"""
        base_prompt = f"""你是一个专业的翻译专家，精通{request.source_language}和{request.target_language}。

任务：将{request.source_language}文本准确、自然地翻译为{request.target_language}。

要求：
1. 保持原文意思不变，确保翻译准确性
2. 使用{request.target_language}的地道表达
3. {self.style_prompts[request.style]}
4. 确保译文流畅、自然、易读"""

        if request.context:
            base_prompt += f"\n5. 考虑以下上下文：{request.context}"

        base_prompt += f"\n\n请只返回翻译结果，不要添加任何解释或说明。"

        return base_prompt

    def _build_user_message(self, request: TranslationRequest) -> str:
        """构建用户消息"""
        if request.context:
            return f"""上下文：{request.context}

原文（{request.source_language}）：
{request.text}

请翻译为{request.target_language}："""
        else:
            return f"""原文（{request.source_language}）：
{request.text}

请翻译为{request.target_language}："""

    def detect_language(self, text: str) -> str:
        """
        检测文本语言（简单实现）

        Args:
            text: 待检测的文本

        Returns:
            检测到的语言
        """
        # 简单的语言检测逻辑
        if not text or len(text) < 10:
            return "Unknown"

        # 检测中文字符
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        if chinese_chars > len(text) * 0.3:
            return "中文"

        # 检测日语字符
        japanese_chars = len([c for c in text if c in 'ひらがなカタカナ漢字'])
        if japanese_chars > len(text) * 0.2:
            return "日本語"

        # 检测韩语字符
        korean_chars = len([c for c in text if '가' <= c <= '힣'])
        if korean_chars > len(text) * 0.2:
            return "한국어"

        # 检测阿拉伯语字符
        arabic_chars = len([c for c in text if '\u0600' <= c <= '\u06FF'])
        if arabic_chars > len(text) * 0.3:
            return "العربية"

        # 检测俄语字符
        russian_chars = len([c for c in text if '\u0400' <= c <= '\u04FF'])
        if russian_chars > len(text) * 0.3:
            return "Русский"

        # 默认返回英文
        return "English"

    async def batch_translate(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        style: TranslationStyle = TranslationStyle.CASUAL,
        temperature: Optional[float] = None,
        concurrent_limit: int = 3
    ) -> List[str]:
        """
        批量翻译

        Args:
            texts: 待翻译的文本列表
            source_language: 源语言
            target_language: 目标语言
            style: 翻译风格
            temperature: 温度参数
            concurrent_limit: 并发限制

        Returns:
            翻译结果列表
        """
        if not texts:
            return []

        self.logger.info(
            "开始批量翻译",
            text_count=len(texts),
            source_language=source_language,
            target_language=target_language
        )

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def translate_single(text: str, index: int) -> tuple[int, str]:
            async with semaphore:
                try:
                    translation = await self.translate(
                        text=text,
                        source_language=source_language,
                        target_language=target_language,
                        style=style,
                        temperature=temperature
                    )
                    return index, translation
                except Exception as e:
                    self.logger.error(
                        "批量翻译中单个文本失败",
                        index=index,
                        error=str(e)
                    )
                    return index, f"翻译失败: {e}"

        # 并发处理
        tasks = [
            translate_single(text, i)
            for i, text in enumerate(texts)
        ]

        results = await asyncio.gather(*tasks)

        # 按索引排序结果
        results.sort(key=lambda x: x[0])
        translations = [result[1] for result in results]

        self.logger.info(
            "批量翻译完成",
            total_count=len(texts),
            success_count=len([t for t in translations if not t.startswith("翻译失败")])
        )

        return translations

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return self.supported_languages.copy()

    def is_language_supported(self, language: str) -> bool:
        """检查语言是否支持"""
        return language in self.supported_languages