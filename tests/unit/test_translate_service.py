"""
翻译服务单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from ai_assistant.services.translate_service import (
    TranslationService, TranslationRequest, LanguagePair,
    TranslationStyle
)
from ai_assistant.services.deepseek_client import DeepSeekClient, Message, ChatCompletionResponse
from ai_assistant.core.config_simple import SimpleSettings
from ai_assistant.core.exceptions import ValidationError, ServiceError


class TestLanguagePair:
    """语言对测试"""

    def test_language_pair_creation(self):
        """测试语言对创建"""
        pair = LanguagePair("中文", "English")
        assert pair.source == "中文"
        assert pair.target == "English"
        assert str(pair) == "中文 -> English"

    def test_language_pair_equality(self):
        """测试语言对相等性"""
        pair1 = LanguagePair("中文", "English")
        pair2 = LanguagePair("中文", "English")
        pair3 = LanguagePair("English", "中文")

        assert pair1 == pair2
        assert pair1 != pair3

    def test_language_pair_hash(self):
        """测试语言对哈希"""
        pair1 = LanguagePair("中文", "English")
        pair2 = LanguagePair("中文", "English")

        # 相同的语言对应该有相同的哈希值
        assert hash(pair1) == hash(pair2)

        # 可以用于集合
        language_set = {pair1, pair2}
        assert len(language_set) == 1


class TestTranslationRequest:
    """翻译请求测试"""

    def test_translation_request_creation(self):
        """测试翻译请求创建"""
        request = TranslationRequest(
            text="Hello, world!",
            source_language="English",
            target_language="中文",
            style=TranslationStyle.FORMAL,
            preserve_formatting=True,
            context="This is a greeting."
        )
        assert request.text == "Hello, world!"
        assert request.source_language == "English"
        assert request.target_language == "中文"
        assert request.style == TranslationStyle.FORMAL
        assert request.preserve_formatting is True
        assert request.context == "This is a greeting."

    def test_translation_request_defaults(self):
        """测试翻译请求默认值"""
        request = TranslationRequest(
            text="Hello",
            source_language="English",
            target_language="中文"
        )
        assert request.style == TranslationStyle.CASUAL
        assert request.preserve_formatting is True
        assert request.context is None


class TestTranslationService:
    """翻译服务测试"""

    @pytest.fixture
    def mock_settings(self):
        """创建模拟设置"""
        return SimpleSettings(
            app_name="Test App",
            deepseek_api_key="test_key",
            deepseek_base_url="https://api.test.com",
            deepseek_model="test-model",
            deepseek_temperature=0.7,
            deepseek_max_tokens=2048
        )

    @pytest.fixture
    def mock_client(self):
        """创建模拟客户端"""
        client = Mock(spec=DeepSeekClient)
        client.chat_completion = AsyncMock()
        client.create_system_message = Mock(side_effect=lambda content: Message(role="system", content=content))
        client.create_user_message = Mock(side_effect=lambda content: Message(role="user", content=content))
        return client

    @pytest.fixture
    def translation_service(self, mock_client, mock_settings):
        """创建翻译服务实例"""
        return TranslationService(mock_client, mock_settings)

    def test_service_initialization(self, mock_client, mock_settings):
        """测试服务初始化"""
        service = TranslationService(mock_client, mock_settings)
        assert service.client == mock_client
        assert service.settings == mock_settings
        assert len(service.supported_languages) > 0
        assert "中文" in service.supported_languages
        assert "English" in service.supported_languages

    def test_get_translation_prompt_formal(self, translation_service):
        """测试正式风格翻译提示"""
        request = TranslationRequest(
            text="Hello",
            source_language="English",
            target_language="中文",
            style=TranslationStyle.FORMAL
        )
        prompt = translation_service._get_translation_prompt(request)

        assert "专业的翻译专家" in prompt
        assert "精通English和中文" in prompt
        assert "正式、礼貌的语言风格" in prompt
        assert "准确、自然地翻译" in prompt

    def test_get_translation_prompt_casual(self, translation_service):
        """测试随意风格翻译提示"""
        request = TranslationRequest(
            text="Hello",
            source_language="English",
            target_language="中文",
            style=TranslationStyle.CASUAL
        )
        prompt = translation_service._get_translation_prompt(request)

        assert "自然、随意的语言风格" in prompt

    def test_get_translation_prompt_with_context(self, translation_service):
        """测试带上下文的翻译提示"""
        request = TranslationRequest(
            text="Break a leg",
            source_language="English",
            target_language="中文",
            context="This is said before a performance."
        )
        prompt = translation_service._get_translation_prompt(request)

        assert "考虑以下上下文" in prompt
        assert "This is said before a performance." in prompt

    def test_build_user_message_with_context(self, translation_service):
        """测试带上下文的用户消息构建"""
        request = TranslationRequest(
            text="Hello",
            source_language="English",
            target_language="中文",
            context="Greeting"
        )
        user_message = translation_service._build_user_message(request)

        assert "上下文：Greeting" in user_message
        assert "原文（English）" in user_message
        assert "Hello" in user_message
        assert "请翻译为中文" in user_message

    def test_build_user_message_without_context(self, translation_service):
        """测试不带上下文的用户消息构建"""
        request = TranslationRequest(
            text="Hello",
            source_language="English",
            target_language="中文"
        )
        user_message = translation_service._build_user_message(request)

        assert "上下文" not in user_message
        assert "Hello" in user_message
        assert "请翻译为中文" in user_message

    def test_split_text_into_segments(self, translation_service):
        """测试文本分割"""
        long_text = "This is sentence one. This is sentence two! This is sentence three? This is sentence four. " * 10
        segments = translation_service._split_text_into_segments(long_text)

        assert len(segments) > 1
        # 验证每个段的长度合理
        for segment in segments:
            assert len(segment) <= 1000

    def test_split_text_into_segments_chinese(self, translation_service):
        """测试中文文本分割"""
        chinese_text = "这是第一句话。这是第二句话！这是第三句话？这是第四句话。" * 10
        segments = translation_service._split_text_into_segments(chinese_text)

        assert len(segments) > 1
        # 验证中文文本被正确分割
        for segment in segments:
            assert len(segment) <= 1000

    def test_is_chinese_text_true(self, translation_service):
        """测试中文文本检测（真）"""
        chinese_text = "这是中文文本，包含很多汉字。"
        assert translation_service._is_chinese_text(chinese_text) is True

    def test_is_chinese_text_false(self, translation_service):
        """测试中文文本检测（假）"""
        english_text = "This is English text with ASCII characters."
        assert translation_service._is_chinese_text(english_text) is False

    def test_merge_translations_english(self, translation_service):
        """测试英文翻译合并"""
        translations = ["Hello world", "How are you", "Nice to meet you"]
        merged = translation_service._merge_translations("Hello world. How are you. Nice to meet you", translations)

        # 英文句子应该以句号结尾
        assert merged.endswith(".")
        assert "Hello world" in merged
        assert "How are you" in merged
        assert "Nice to meet you" in merged

    def test_merge_translations_chinese(self, translation_service):
        """测试中文翻译合并"""
        translations = ["你好世界", "你好吗", "很高兴见到你"]
        merged = translation_service._merge_translations("你好世界。你好吗。很高兴见到你", translations)

        # 中文句子应该以句号结尾
        assert merged.endswith("。")
        assert "你好世界" in merged
        assert "你好吗" in merged
        assert "很高兴见到你" in merged

    def test_preserve_formatting_no_change_needed(self, translation_service):
        """测试格式保留（无需更改）"""
        original = "Hello world.\n\nHow are you?"
        translation = "你好世界。\n\n你好吗？"

        preserved = translation_service._preserve_formatting(original, translation)
        # 段落数量相同，应该保持原样
        assert preserved == translation

    def test_preserve_formatting_add_paragraphs(self, translation_service):
        """测试格式保留（添加段落）"""
        original = "Hello world.\n\nHow are you?\n\nNice to meet you."
        translation = "你好世界。你好吗？很高兴见到你。"

        preserved = translation_service._preserve_formatting(original, translation)
        # 应该尝试分割成段落
        assert "你好世界" in preserved
        assert "你好吗" in preserved
        assert "很高兴见到你" in preserved

    def test_detect_language_chinese(self, translation_service):
        """测试中文语言检测"""
        result = translation_service.detect_language("这是中文文本，包含很多汉字。")
        assert result == "中文"

    def test_detect_language_japanese(self, translation_service):
        """测试日语语言检测"""
        result = translation_service.detect_language("これは日本語のテキストです。ひらがなと漢字が含まれています。")
        assert result == "日本語"

    def test_detect_language_korean(self, translation_service):
        """测试韩语语言检测"""
        result = translation_service.detect_language("이것은 한국어 텍스트입니다.")
        assert result == "한국어"

    def test_detect_language_arabic(self, translation_service):
        """测试阿拉伯语语言检测"""
        result = translation_service.detect_language("هذا نص باللغة العربية.")
        assert result == "العربية"

    def test_detect_language_russian(self, translation_service):
        """测试俄语语言检测"""
        result = translation_service.detect_language("Это русский текст.")
        assert result == "Русский"

    def test_detect_language_english_default(self, translation_service):
        """测试英语语言检测（默认）"""
        result = translation_service.detect_language("This is English text.")
        assert result == "English"

    def test_detect_language_short_text(self, translation_service):
        """测试短文本语言检测"""
        result = translation_service.detect_language("Hi")
        assert result == "Unknown"

    @pytest.mark.asyncio
    async def test_translate_single_text_success(self, translation_service, mock_client):
        """测试单个文本翻译成功"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [{"message": {"content": "你好世界"}}]
        mock_client.chat_completion.return_value = mock_response

        request = TranslationRequest(
            text="Hello world",
            source_language="English",
            target_language="中文"
        )

        result = await translation_service._translate_single_text(request, "test_req_123")

        assert result == "你好世界"

        # 验证API调用
        mock_client.chat_completion.assert_called_once()
        call_args = mock_client.chat_completion.call_args
        api_request = call_args[0][0]
        assert api_request.model == "test-model"
        assert len(api_request.messages) == 2  # system + user
        assert api_request.temperature == 0.7  # 默认服务温度

    @pytest.mark.asyncio
    async def test_translate_single_text_with_custom_temperature(self, translation_service, mock_client):
        """测试自定义温度的文本翻译"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [{"message": {"content": "你好"}}]
        mock_client.chat_completion.return_value = mock_response

        request = TranslationRequest(
            text="Hello",
            source_language="English",
            target_language="中文"
        )

        await translation_service._translate_single_text(request, "test_req_123", temperature=0.9)

        # 验证温度设置
        call_args = mock_client.chat_completion.call_args
        assert call_args[0][0].temperature == 0.9

    @pytest.mark.asyncio
    async def test_translate_long_text_success(self, translation_service, mock_client):
        """测试长文本翻译成功"""
        # 创建长文本
        long_text = "This is a very long text. " * 200

        # 模拟分块翻译响应
        def mock_chat_completion(api_request, request_id):
            mock_response = Mock(spec=ChatCompletionResponse)
            if "segment_0" in request_id:
                mock_response.choices = [{"message": {"content": "这是第一部分的翻译"}}]
            elif "segment_1" in request_id:
                mock_response.choices = [{"message": {"content": "这是第二部分的翻译"}}]
            return mock_response

        mock_client.chat_completion.side_effect = mock_chat_completion

        request = TranslationRequest(
            text=long_text,
            source_language="English",
            target_language="中文"
        )

        result = await translation_service._translate_long_text(request, "test_req_123")

        # 验证结果包含两部分翻译
        assert "第一部分" in result or "第二部分" in result

        # 验证多次API调用
        assert mock_client.chat_completion.call_count >= 2

    @pytest.mark.asyncio
    async def test_translate_success(self, translation_service, mock_client):
        """测试翻译成功"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [{"message": {"content": "你好世界"}}]
        mock_client.chat_completion.return_value = mock_response

        result = await translation_service.translate(
            text="Hello world",
            source_language="English",
            target_language="中文",
            style=TranslationStyle.FORMAL,
            preserve_formatting=True,
            context="Greeting"
        )

        assert result == "你好世界"

        # 验证API调用参数
        call_args = mock_client.chat_completion.call_args
        api_request = call_args[0][0]
        assert api_request.temperature == 0.7  # 默认温度

    @pytest.mark.asyncio
    async def test_translate_with_custom_temperature(self, translation_service, mock_client):
        """测试自定义温度的翻译"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [{"message": {"content": "你好"}}]
        mock_client.chat_completion.return_value = mock_response

        result = await translation_service.translate(
            text="Hello",
            source_language="English",
            target_language="中文",
            temperature=0.4
        )

        assert result == "你好"

        # 验证温度设置
        call_args = mock_client.chat_completion.call_args
        assert call_args[0][0].temperature == 0.4

    @pytest.mark.asyncio
    async def test_translate_long_text_split(self, translation_service, mock_client):
        """测试长文本分割翻译"""
        long_text = "This is a long text that should be split. " * 100

        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [{"message": {"content": "Translation"}}]
        mock_client.chat_completion.return_value = mock_response

        result = await translation_service.translate(
            text=long_text,
            source_language="English",
            target_language="中文"
        )

        assert result == "Translation"
        # 长文本应该触发分割逻辑
        assert mock_client.chat_completion.call_count >= 1

    @pytest.mark.asyncio
    async def test_translate_api_error(self, translation_service, mock_client):
        """测试翻译API错误"""
        from ai_assistant.core.exceptions import APIError

        mock_client.chat_completion.side_effect = APIError("API Error")

        with pytest.raises(ServiceError) as exc_info:
            await translation_service.translate(
                text="Hello",
                source_language="English",
                target_language="中文"
            )

        assert "文本翻译失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_translate_success(self, translation_service, mock_client):
        """测试批量翻译成功"""
        texts = [
            "Hello world",
            "How are you",
            "Nice to meet you"
        ]

        # 模拟批量响应
        def mock_chat_completion(api_request, request_id):
            mock_response = Mock(spec=ChatCompletionResponse)
            if "batch_0" in request_id:
                mock_response.choices = [{"message": {"content": "你好世界"}}]
            elif "batch_1" in request_id:
                mock_response.choices = [{"message": {"content": "你好吗"}}]
            elif "batch_2" in request_id:
                mock_response.choices = [{"message": {"content": "很高兴见到你"}}]
            return mock_response

        mock_client.chat_completion.side_effect = mock_chat_completion

        results = await translation_service.batch_translate(
            texts=texts,
            source_language="English",
            target_language="中文",
            concurrent_limit=2
        )

        assert len(results) == 3
        assert results[0] == "你好世界"
        assert results[1] == "你好吗"
        assert results[2] == "很高兴见到你"

    @pytest.mark.asyncio
    async def test_batch_translate_with_errors(self, translation_service, mock_client):
        """测试批量翻译中的错误处理"""
        texts = ["Text 1", "Text 2"]

        # 模拟一个成功，一个失败
        def mock_chat_completion(api_request, request_id):
            mock_response = Mock(spec=ChatCompletionResponse)
            if "batch_0" in request_id:
                mock_response.choices = [{"message": {"content": "翻译1"}}]
            else:
                raise APIError("API Error")
            return mock_response

        mock_client.chat_completion.side_effect = mock_chat_completion

        results = await translation_service.batch_translate(
            texts=texts,
            source_language="English",
            target_language="中文"
        )

        assert len(results) == 2
        assert results[0] == "翻译1"
        assert "翻译失败" in results[1]

    @pytest.mark.asyncio
    async def test_batch_translate_empty_list(self, translation_service):
        """测试空文本列表的批量翻译"""
        results = await translation_service.batch_translate(texts=[])
        assert results == []

    @pytest.mark.asyncio
    async def test_translate_context_manager(self, mock_settings):
        """测试翻译服务上下文管理器"""
        with patch('ai_assistant.services.translate_service.DeepSeekClient') as mock_client_class:
            mock_client = Mock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            async with TranslationService(None, mock_settings) as service:
                assert service.client == mock_client
                mock_client.__aenter__.assert_called_once()

            mock_client.__aexit__.assert_called_once()

    def test_get_supported_languages(self, translation_service):
        """测试获取支持的语言列表"""
        languages = translation_service.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "中文" in languages
        assert "English" in languages
        assert "日本語" in languages

    def test_is_language_supported(self, translation_service):
        """测试语言支持检查"""
        assert translation_service.is_language_supported("中文")
        assert translation_service.is_language_supported("English")
        assert not translation_service.is_language_supported("InvalidLang")

    def test_language_codes_mapping(self, translation_service):
        """测试语言代码映射"""
        assert "中文" in translation_service.language_codes
        assert "English" in translation_service.language_codes
        assert translation_service.language_codes["中文"] == "zh"
        assert translation_service.language_codes["English"] == "en"

    def test_style_prompts(self, translation_service):
        """测试翻译风格提示"""
        assert TranslationStyle.FORMAL in translation_service.style_prompts
        assert TranslationStyle.CASUAL in translation_service.style_prompts
        assert TranslationStyle.PROFESSIONAL in translation_service.style_prompts
        assert "正式、礼貌的语言风格" in translation_service.style_prompts[TranslationStyle.FORMAL]
        assert "自然、随意的语言风格" in translation_service.style_prompts[TranslationStyle.CASUAL]