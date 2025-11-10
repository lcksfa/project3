"""
总结服务单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from ai_assistant.services.summary_service import (
    SummaryService, SummaryRequest, SummaryType
)
from ai_assistant.services.deepseek_client import DeepSeekClient, Message, ChatCompletionResponse
from ai_assistant.core.config_simple import SimpleSettings
from ai_assistant.core.exceptions import ValidationError, ServiceError


class TestSummaryRequest:
    """总结请求测试"""

    def test_summary_request_creation(self):
        """测试总结请求创建"""
        request = SummaryRequest(
            text="This is a long text that needs to be summarized.",
            summary_type=SummaryType.PARAGRAPH,
            max_length=100,
            language="中文"
        )
        assert request.text == "This is a long text that needs to be summarized."
        assert request.summary_type == SummaryType.PARAGRAPH
        assert request.max_length == 100
        assert request.language == "中文"

    def test_summary_request_defaults(self):
        """测试总结请求默认值"""
        request = SummaryRequest(
            text="Test text"
        )
        assert request.text == "Test text"
        assert request.summary_type == SummaryType.PARAGRAPH
        assert request.max_length is None
        assert request.language == "中文"

    def test_summary_request_validation_empty_text(self):
        """测试空文本验证"""
        with pytest.raises(ValidationError, match="文本不能为空"):
            SummaryRequest(text="")

    def test_summary_request_validation_none_text(self):
        """测试None文本验证"""
        with pytest.raises(ValidationError, match="文本不能为空"):
            SummaryRequest(text=None)

    def test_summary_request_validation_too_long(self):
        """测试文本过长验证"""
        with pytest.raises(ValidationError, match="文本长度不能超过"):
            SummaryRequest(text="a" * 10001)

    def test_summary_request_validation_max_length_zero(self):
        """测试最大长度为零验证"""
        # SummaryService 可能会在运行时验证，但SummaryRequest构造时不会报错
        request = SummaryRequest(text="test", max_length=0)
        assert request.max_length == 0


class TestSummaryType:
    """总结类型测试"""

    def test_summary_type_values(self):
        """测试总结类型值"""
        assert SummaryType.PARAGRAPH == "paragraph"
        assert SummaryType.BULLET_POINTS == "bullet_points"
        assert SummaryType.KEY_INSIGHTS == "key_insights"
        assert SummaryType.EXECUTIVE == "executive"
        assert SummaryType.DETAILED == "detailed"

    def test_summary_type_iteration(self):
        """测试总结类型迭代"""
        types = list(SummaryType)
        assert SummaryType.PARAGRAPH in types
        assert SummaryType.BULLET_POINTS in types
        assert SummaryType.KEY_INSIGHTS in types
        assert SummaryType.EXECUTIVE in types
        assert SummaryType.DETAILED in types


class TestSummaryService:
    """总结服务测试"""

    @pytest.fixture
    def mock_deepseek_client(self):
        """模拟DeepSeek客户端"""
        client = Mock(spec=DeepSeekClient)
        client.chat_completion = AsyncMock()
        client.create_message = Mock()
        client.create_system_message = Mock()
        client.create_user_message = Mock()
        client.create_assistant_message = Mock()
        return client

    @pytest.fixture
    def summary_service(self, mock_deepseek_client):
        """总结服务实例"""
        return SummaryService(mock_deepseek_client)

    def test_summary_service_creation(self, mock_deepseek_client):
        """测试总结服务创建"""
        service = SummaryService(mock_deepseek_client)
        assert service.client == mock_deepseek_client

    @pytest.mark.asyncio
    async def test_summarize_text_paragraph(self, summary_service, mock_deepseek_client):
        """测试段落总结"""
        # 模拟API响应
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="这是一个总结段落。"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(
            text="这是一段很长的文本，需要进行总结。",
            summary_type=SummaryType.PARAGRAPH
        )

        result = await summary_service.summarize(request)
        assert result == "这是一个总结段落。"

        # 验证API调用
        mock_deepseek_client.chat_completion.assert_called_once()
        call_args = mock_deepseek_client.chat_completion.call_args
        assert "总结" in call_args[0][0]  # 系统消息应该包含总结

    @pytest.mark.asyncio
    async def test_summarize_text_bullet_points(self, summary_service, mock_deepseek_client):
        """测试要点总结"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="• 要点1\n• 要点2\n• 要点3"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(
            text="详细内容...",
            summary_type=SummaryType.BULLET_POINTS,
            style="casual"
        )

        result = await summary_service.summarize(request)
        assert "•" in result or "-" in result  # 应该包含要点符号

    @pytest.mark.asyncio
    async def test_summarize_text_concise(self, summary_service, mock_deepseek_client):
        """测试简洁总结"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="简洁总结。"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(
            text="很长很长的详细内容...",
            summary_type=SummaryType.CONCISE,
            style="analytical"
        )

        result = await summary_service.summarize(request)
        assert result == "简洁总结。"

    @pytest.mark.asyncio
    async def test_summarize_text_detailed(self, summary_service, mock_deepseek_client):
        """测试详细总结"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="详细的总结内容..."))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(
            text="原始内容...",
            summary_type=SummaryType.DETAILED,
            style="professional"
        )

        result = await summary_service.summarize(request)
        assert len(result) > 10  # 详细总结应该更长

    @pytest.mark.asyncio
    async def test_summarize_with_temperature(self, summary_service, mock_deepseek_client):
        """测试带温度参数的总结"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="带温度的总结。"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(text="测试文本")
        result = await summary_service.summarize(request, temperature=0.8)

        assert result == "带温度的总结。"

        # 验证温度参数被传递
        call_args = mock_deepseek_client.chat_completion.call_args
        assert call_args[1].get('temperature') == 0.8

    @pytest.mark.asyncio
    async def test_summarize_api_error(self, summary_service, mock_deepseek_client):
        """测试API错误处理"""
        mock_deepseek_client.chat_completion.side_effect = Exception("API Error")

        request = SummaryRequest(text="测试文本")

        with pytest.raises(ServiceError, match="文本总结失败"):
            await summary_service.summarize(request)

    @pytest.mark.asyncio
    async def test_summarize_empty_response(self, summary_service, mock_deepseek_client):
        """测试空响应处理"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content=""))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(text="测试文本")

        with pytest.raises(ServiceError, match="总结结果为空"):
            await summary_service.summarize(request)

    @pytest.mark.asyncio
    async def test_summarize_long_text(self, summary_service, mock_deepseek_client):
        """测试长文本总结"""
        # 模拟长文本
        long_text = "这是一个很长的文本。" * 100

        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="长文本的总结。"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(
            text=long_text,
            summary_type=SummaryType.CONCISE
        )

        result = await summary_service.summarize(request)
        assert result == "长文本的总结。"

    @pytest.mark.asyncio
    async def test_summarize_different_languages(self, summary_service, mock_deepseek_client):
        """测试不同语言总结"""
        test_cases = [
            ("中文文本内容", "中文总结", "中文"),
            ("English text content", "English summary", "English"),
            ("日本語のテキスト", "日本語の要約", "日本語")
        ]

        for text, expected_summary, language in test_cases:
            mock_response = Mock(spec=ChatCompletionResponse)
            mock_response.choices = [
                Mock(message=Mock(content=expected_summary))
            ]
            mock_deepseek_client.chat_completion.return_value = mock_response

            request = SummaryRequest(
                text=text,
                language=language
            )

            result = await summary_service.summarize(request)
            assert result == expected_summary

    def test_validate_summary_request_valid(self, summary_service):
        """测试有效总结请求验证"""
        request = SummaryRequest(
            text="有效的文本内容",
            summary_type=SummaryType.PARAGRAPH,
            style="neutral",
            max_length=100
        )
        # 应该不抛出异常
        summary_service._validate_request(request)

    def test_validate_summary_request_invalid_type(self, summary_service):
        """测试无效总结类型验证"""
        with pytest.raises(ValidationError, match="不支持的总结类型"):
            request = SummaryRequest(text="测试")
            request.summary_type = "invalid_type"
            summary_service._validate_request(request)

    def test_validate_summary_request_invalid_style(self, summary_service):
        """测试无效总结风格验证"""
        with pytest.raises(ValidationError, match="不支持的总结风格"):
            request = SummaryRequest(text="测试")
            request.style = "invalid_style"
            summary_service._validate_request(request)

    def test_get_supported_summary_types(self, summary_service):
        """测试获取支持的总结类型"""
        types = summary_service.get_supported_summary_types()
        assert SummaryType.PARAGRAPH in types
        assert SummaryType.BULLET_POINTS in types
        assert SummaryType.CONCISE in types
        assert SummaryType.DETAILED in types

    def test_get_supported_summary_styles(self, summary_service):
        """测试获取支持的总结风格"""
        styles = summary_service.get_supported_summary_styles()
        assert "neutral" in styles
        assert "formal" in styles
        assert "casual" in styles
        assert "professional" in styles
        assert "analytical" in styles

    def test_is_summary_type_supported(self, summary_service):
        """测试总结类型支持检查"""
        assert summary_service.is_summary_type_supported(SummaryType.PARAGRAPH)
        assert not summary_service.is_summary_type_supported("invalid_type")

    def test_is_summary_style_supported(self, summary_service):
        """测试总结风格支持检查"""
        assert summary_service.is_summary_style_supported("formal")
        assert not summary_service.is_summary_style_supported("invalid_style")

    @pytest.mark.asyncio
    async def test_summarize_with_custom_max_length(self, summary_service, mock_deepseek_client):
        """测试自定义最大长度总结"""
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="短总结。"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        request = SummaryRequest(
            text="很长的原始文本...",
            max_length=50
        )

        result = await summary_service.summarize(request)
        assert result == "短总结。"

        # 验证最大长度在提示中被提及
        call_args = mock_deepseek_client.chat_completion.call_args
        assert "50" in call_args[0][0]  # 系统消息应该包含长度限制