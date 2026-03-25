"""
错误处理功能测试
测试语音输入、语音输出和主题生成的错误处理机
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from chatterpal.core.errors import (
    ErrorHandler, ChatModuleError, AudioInputError, SpeechRecognitionError,
    SpeechSynthesisError, TopicGenerationError, ErrorSeverity, ErrorCategory
)
from chatterpal.core.asr.base import ASRBase, ASRResult, ConfidenceLevel
from chatterpal.services.chat import ChatService
from chatterpal.services.topic_generator import TopicGenerator
from chatterpal.utils.audio import AudioProcessor, AudioValidationResult, AudioQualityLevel


class TestErrorHandler:
    """测试错误处理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.error_handler = ErrorHandler()
    
    def test_get_error_info(self):
        """测试获取错误信息"""
        # 测试已知错误
        error_info = self.error_handler.get_error_info("AUDIO_TOO_SHORT")
        assert error_info is not None
        assert error_info.code == "AUDIO_TOO_SHORT"
        assert error_info.category == ErrorCategory.AUDIO_INPUT
        assert error_info.severity == ErrorSeverity.MEDIUM
        
        # 测试未知错误
        unknown_error = self.error_handler.get_error_info("UNKNOWN_ERROR_CODE")
        assert unknown_error is None
    
    def test_create_error(self):
        """测试创建错误对象"""
        # 测试创建已知错误
        error = self.error_handler.create_error("AUDIO_TOO_SHORT", duration=0.5)
        assert isinstance(error, AudioInputError)
        assert error.error_info.code == "AUDIO_TOO_SHORT"
        assert error.error_info.metadata["duration"] == 0.5
        
        # 测试创建未知错误
        unknown_error = self.error_handler.create_error("UNKNOWN_CODE")
        assert isinstance(unknown_error, ChatModuleError)
        assert unknown_error.error_info.code == "UNKNOWN_ERROR"
    
    def test_handle_audio_validation_error(self):
        """测试音频验证错误处理"""
        # 测试有效音频
        valid_result = AudioValidationResult(
            is_valid=True,
            duration=5.0,
            quality_level=AudioQualityLevel.GOOD,
            issues=[],
            metadata={}
        )
        error = self.error_handler.handle_audio_validation_error(valid_result)
        assert error is None
        
        # 测试音频过短
        short_result = AudioValidationResult(
            is_valid=False,
            duration=0.5,
            quality_level=AudioQualityLevel.POOR,
            issues=["音频时长过短"],
            metadata={}
        )
        error = self.error_handler.handle_audio_validation_error(short_result)
        assert isinstance(error, AudioInputError)
        assert error.error_info.code == "AUDIO_TOO_SHORT"
        
        # 测试音频过长
        long_result = AudioValidationResult(
            is_valid=False,
            duration=65.0,
            quality_level=AudioQualityLevel.FAIR,
            issues=["音频时长过长"],
            metadata={}
        )
        error = self.error_handler.handle_audio_validation_error(long_result)
        assert isinstance(error, AudioInputError)
        assert error.error_info.code == "AUDIO_TOO_LONG"
        
        # 测试音量过低
        low_volume_result = AudioValidationResult(
            is_valid=False,
            duration=3.0,
            quality_level=AudioQualityLevel.POOR,
            issues=["音频音量过低"],
            metadata={"max_amplitude": 0.001, "rms_amplitude": 0.0005}
        )
        error = self.error_handler.handle_audio_validation_error(low_volume_result)
        assert isinstance(error, AudioInputError)
        assert error.error_info.code == "AUDIO_LOW_VOLUME"
        
        # 测试静音过多
        silence_result = AudioValidationResult(
            is_valid=False,
            duration=3.0,
            quality_level=AudioQualityLevel.POOR,
            issues=["静音比例过高"],
            metadata={"silence_ratio": 0.9}
        )
        error = self.error_handler.handle_audio_validation_error(silence_result)
        assert isinstance(error, AudioInputError)
        assert error.error_info.code == "AUDIO_MOSTLY_SILENCE"
    
    def test_handle_asr_error(self):
        """测试ASR错误处理"""
        # 测试无语音识别结
        no_speech_result = ASRResult(
            text=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.VERY_LOW,
            audio_quality_score=0.5,
            processing_time=2.0,
            metadata={}
        )
        error = self.error_handler.handle_asr_error(no_speech_result)
        assert isinstance(error, SpeechRecognitionError)
        assert error.error_info.code == "ASR_NO_SPEECH"
        
        # 测试置信度过
        low_confidence_result = ASRResult(
            text="hello",
            confidence=0.2,
            confidence_level=ConfidenceLevel.VERY_LOW,
            audio_quality_score=0.5,
            processing_time=2.0,
            metadata={}
        )
        error = self.error_handler.handle_asr_error(low_confidence_result)
        assert isinstance(error, SpeechRecognitionError)
        assert error.error_info.code == "ASR_LOW_CONFIDENCE"
        
        # 测试处理超时
        timeout_result = ASRResult(
            text="hello",
            confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            audio_quality_score=0.8,
            processing_time=35.0,
            metadata={}
        )
        error = self.error_handler.handle_asr_error(timeout_result)
        assert isinstance(error, SpeechRecognitionError)
        assert error.error_info.code == "ASR_TIMEOUT"
        
        # 测试正常结果
        good_result = ASRResult(
            text="hello world",
            confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            audio_quality_score=0.8,
            processing_time=2.0,
            metadata={}
        )
        error = self.error_handler.handle_asr_error(good_result)
        assert error is None
    
    def test_format_user_error_message(self):
        """测试格式化用户错误消息"""
        error = self.error_handler.create_error("AUDIO_TOO_SHORT", duration=0.5)
        formatted = self.error_handler.format_user_error_message(error)
        
        assert formatted["error_code"] == "AUDIO_TOO_SHORT"
        assert "录音时间太短" in formatted["message"]
        assert len(formatted["suggestions"]) > 0
        assert formatted["severity"] == "medium"
        assert formatted["category"] == "audio_input"
        assert formatted["can_retry"] is True


class MockASR(ASRBase):
    """模拟ASR类用于测试"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.should_fail = False
        self.fail_with_timeout = False
        self.return_low_confidence = False
        self.return_empty = False
    
    def recognize(self, audio_data: bytes, **kwargs):
        if self.should_fail:
            raise Exception("ASR服务错误")
        if self.return_empty:
            return None
        return "test recognition result"
    
    def recognize_file(self, audio_path: str, **kwargs):
        if self.should_fail:
            raise Exception("ASR服务错误")
        if self.return_empty:
            return None
        return "test recognition result"
    
    def recognize_enhanced(self, audio_data, **kwargs):
        if self.should_fail:
            raise Exception("ASR服务错误")
        
        confidence = 0.2 if self.return_low_confidence else 0.9
        processing_time = 35.0 if self.fail_with_timeout else 2.0
        text = None if self.return_empty else "test recognition result"
        
        return ASRResult(
            text=text,
            confidence=confidence,
            confidence_level=ConfidenceLevel.LOW if self.return_low_confidence else ConfidenceLevel.HIGH,
            audio_quality_score=0.8,
            processing_time=processing_time,
            metadata={}
        )


class MockTTS:
    """模拟TTS类用于测试"""
    
    def __init__(self):
        self.should_fail = False
        self.fail_with_timeout = False
    
    def synthesize(self, text: str):
        if self.should_fail:
            raise Exception("TTS服务错误")
        if self.fail_with_timeout:
            import time
            time.sleep(31)  # 模拟超时
        return b"fake audio data"


class MockLLM:
    """模拟LLM类用于测试"""
    
    def __init__(self):
        self.should_fail = False
    
    def chat(self, messages, **kwargs):
        if self.should_fail:
            raise Exception("LLM服务错误")
        return "Test response"


class TestASRErrorHandling:
    """测试ASR错误处理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.asr = MockASR()
    
    def test_recognize_with_error_handling_success(self):
        """测试成功的语音识别"""
        audio_data = np.random.random(16000).astype(np.float32) * 0.5  # 1秒的音频
        result = self.asr.recognize_with_error_handling(audio_data)
        
        assert result.text == "test recognition result"
        assert result.confidence > 0.5
    
    def test_recognize_with_error_handling_retry(self):
        """测试重试机制"""
        # 设置前两次失败,第三次成
        call_count = 0
        original_recognize_enhanced = self.asr.recognize_enhanced
        
        def mock_recognize_enhanced(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("临时错误")
            return original_recognize_enhanced(*args, **kwargs)
        
        self.asr.recognize_enhanced = mock_recognize_enhanced
        
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        result = self.asr.recognize_with_error_handling(audio_data, max_retries=3)
        
        assert result.text == "test recognition result"
        assert call_count == 3
    
    def test_recognize_with_error_handling_audio_too_short(self):
        """测试音频过短错误"""
        # 创建过短的音频数
        short_audio = np.random.random(100).astype(np.float32) * 0.5  # 很短的音
        
        with pytest.raises(AudioInputError) as exc_info:
            self.asr.recognize_with_error_handling(short_audio)
        
        assert exc_info.value.error_info.code == "AUDIO_TOO_SHORT"
    
    def test_recognize_with_error_handling_low_confidence(self):
        """测试低置信度错误"""
        self.asr.return_low_confidence = True
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        
        with pytest.raises(SpeechRecognitionError) as exc_info:
            self.asr.recognize_with_error_handling(audio_data, max_retries=1)
        
        assert exc_info.value.error_info.code == "ASR_LOW_CONFIDENCE"
    
    def test_recognize_with_error_handling_no_speech(self):
        """测试无语音错误"""
        self.asr.return_empty = True
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        
        with pytest.raises(SpeechRecognitionError) as exc_info:
            self.asr.recognize_with_error_handling(audio_data)
        
        assert exc_info.value.error_info.code == "ASR_NO_SPEECH"


class TestChatServiceErrorHandling:
    """测试ChatService错误处理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.asr = MockASR()
        self.tts = MockTTS()
        self.llm = MockLLM()
        self.chat_service = ChatService(
            asr=self.asr,
            tts=self.tts,
            llm=self.llm
        )
    
    def test_chat_with_audio_success(self):
        """测试成功的语音对话"""
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        
        response_text, response_audio, session_id = self.chat_service.chat_with_audio(audio_data)
        
        assert response_text == "Test response"
        assert response_audio == b"fake audio data"
        assert session_id is not None
    
    def test_chat_with_audio_asr_failure(self):
        """测试ASR失败的处理"""
        self.asr.should_fail = True
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        
        with pytest.raises(SpeechRecognitionError):
            self.chat_service.chat_with_audio(audio_data, max_retries=1)
    
    def test_chat_with_audio_tts_failure(self):
        """测试TTS失败的处理"""
        self.tts.should_fail = True
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        
        # TTS失败不应该阻止对
        response_text, response_audio, session_id = self.chat_service.chat_with_audio(audio_data)
        
        assert response_text == "Test response"
        assert response_audio is None  # TTS失败,音频为None
        assert session_id is not None
    
    def test_process_chat_error_handling(self):
        """测试process_chat的错误处理"""
        # 测试空文本输
        result = self.chat_service.process_chat(text_input="", use_text_input=True)
        audio_output, chat_history = result
        
        # 应该返回错误信息
        assert len(chat_history) > 0
        error_message = chat_history[0][1]
        assert any(keyword in error_message for keyword in ["错误", "失败", "不支持", "损坏", "重新"])
    
    def test_process_chat_audio_error_handling(self):
        """测试process_chat的音频错误处理"""
        # 测试音频输入错误
        self.asr.should_fail = True
        short_audio = np.random.random(100).astype(np.float32) * 0.5
        
        result = self.chat_service.process_chat(audio=short_audio, use_text_input=False)
        audio_output, chat_history = result
        
        # 应该返回用户友好的错误信
        assert len(chat_history) > 0
        error_message = chat_history[0][1]
        assert any(keyword in error_message for keyword in ["录音", "音频", "语音", "重试"])


class TestTopicGeneratorErrorHandling:
    """测试主题生成器错误处理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.llm = MockLLM()
        self.topic_generator = TopicGenerator(llm=self.llm)
    
    def test_generate_random_topic_success(self):
        """测试成功生成随机主题"""
        topic = self.topic_generator.generate_random_topic("intermediate")
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_random_topic_with_fallback(self):
        """测试带备用方案的主题生成"""
        # 即使出现错误,也应该返回备用主题
        topic = self.topic_generator.generate_random_topic_with_fallback("invalid_difficulty")
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_contextual_topic_llm_failure(self):
        """测试LLM失败时的上下文主题生成"""
        self.llm.should_fail = True
        
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        # 即使LLM失败,也应该回退到随机主
        topic = self.topic_generator.generate_contextual_topic(chat_history)
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_contextual_topic_empty_history(self):
        """测试空对话历史的处理"""
        topic = self.topic_generator.generate_contextual_topic([])
        assert isinstance(topic, str)
        assert len(topic) > 0


class TestIntegratedErrorHandling:
    """测试集成错误处理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.asr = MockASR()
        self.tts = MockTTS()
        self.llm = MockLLM()
        self.chat_service = ChatService(
            asr=self.asr,
            tts=self.tts,
            llm=self.llm
        )
    
    def test_end_to_end_error_recovery(self):
        """测试端到端错误恢复"""
        # 创建会话
        session_id = self.chat_service.create_session()
        
        # 第一次对话成
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        result1 = self.chat_service.process_chat(
            audio=audio_data, 
            use_text_input=False, 
            session_id=session_id
        )
        audio_output1, chat_history1 = result1
        assert len(chat_history1) > 0
        
        # 第二次对话ASR失败,但系统应该优雅处理
        self.asr.should_fail = True
        result2 = self.chat_service.process_chat(
            audio=audio_data, 
            use_text_input=False, 
            session_id=session_id
        )
        audio_output2, chat_history2 = result2
        
        # 应该有错误信息,但不会崩
        assert len(chat_history2) >= len(chat_history1)
        
        # 第三次切换到文本输入,应该正常工
        self.asr.should_fail = False  # 重置ASR
        result3 = self.chat_service.process_chat(
            text_input="Hello again", 
            use_text_input=True, 
            session_id=session_id
        )
        audio_output3, chat_history3 = result3
        
        # 文本对话应该成功
        assert len(chat_history3) > len(chat_history2)
        assert "Test response" in str(chat_history3)
    
    def test_topic_generation_error_recovery(self):
        """测试主题生成错误恢复"""
        # 创建会话
        session_id = self.chat_service.create_session()
        
        # 正常生成主题
        topic1 = self.chat_service.generate_topic(session_id)
        assert isinstance(topic1, str)
        assert len(topic1) > 0
        
        # 模拟LLM失败
        self.llm.should_fail = True
        topic2 = self.chat_service.generate_topic(session_id)
        
        # 即使LLM失败,也应该返回备用主题
        assert isinstance(topic2, str)
        assert len(topic2) > 0
    
    @patch('chatterpal.core.errors.error_handler.log_error')
    def test_error_logging(self, mock_log_error):
        """测试错误日志记录"""
        # 触发一个错
        self.asr.should_fail = True
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        
        try:
            self.chat_service.chat_with_audio(audio_data, max_retries=1)
        except:
            pass
        
        # 验证错误被记
        assert mock_log_error.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])








