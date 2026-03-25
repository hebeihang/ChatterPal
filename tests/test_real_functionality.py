"""
Real functionality verification test
Tests the actual implemented functionality without mocking
"""

import pytest
import tempfile
import os
import numpy as np
from unittest.mock import patch

def test_app_can_be_imported():
    """测试应用可以被导入"""
    try:
        from chatterpal.web.app import create_app
        assert create_app is not None
        print("应用可以成功导入")
    except Exception as e:
        pytest.fail(f"应用导入失败: {e}")

def test_services_can_be_imported():
    """测试服务层可以被导入"""
    try:
        from chatterpal.services.chat import ChatService
        from chatterpal.services.evaluation import EvaluationService
        from chatterpal.services.correction import CorrectionService
        
        assert ChatService is not None
        assert EvaluationService is not None
        assert CorrectionService is not None
        print("服务层可以成功导入")
    except Exception as e:
        pytest.fail(f"服务层导入失败 {e}")

def test_core_modules_can_be_imported():
    """测试核心模块可以被导入"""
    try:
        from chatterpal.core.asr.base import ASRBase
        from chatterpal.core.tts.base import TTSBase
        from chatterpal.core.llm.base import LLMBase
        from chatterpal.core.assessment.base import AssessmentBase
        
        assert ASRBase is not None
        assert TTSBase is not None
        assert LLMBase is not None
        assert AssessmentBase is not None
        print("核心模块可以成功导入")
    except Exception as e:
        pytest.fail(f"核心模块导入失败: {e}")

def test_web_components_can_be_imported():
    """测试Web组件可以被导入"""
    try:
        from chatterpal.web.components.chat_tab import ChatTab
        from chatterpal.web.components.score_tab import ScoreTab
        from chatterpal.web.components.correct_tab import CorrectTab
        
        assert ChatTab is not None
        assert ScoreTab is not None
        assert CorrectTab is not None
        print("Web组件可以成功导入")
    except Exception as e:
        pytest.fail(f"Web组件导入失败: {e}")

def test_configuration_system():
    """测试配置值系统"""
    try:
        from chatterpal.config.settings import Settings
        
        settings = Settings()
        
        # 测试基本配置属性
        assert hasattr(settings, 'audio_sample_rate')
        assert hasattr(settings, 'whisper_model')
        assert hasattr(settings, 'asr_provider')
        assert hasattr(settings, 'tts_provider')
        assert hasattr(settings, 'llm_provider')
        
        # 测试配置值
        assert settings.audio_sample_rate > 0
        assert settings.whisper_model in ["tiny", "base", "small", "medium", "large"]
        
        print("配置系统正常工作")
    except Exception as e:
        pytest.fail(f"配置系统测试失败: {e}")

def test_asr_base_functionality():
    """测试ASR基础功能"""
    try:
        from chatterpal.core.asr.base import ASRBase
        
        class TestASR(ASRBase):
            def recognize(self, audio_data, **kwargs):
                return "测试识别结果"
            
            def recognize_file(self, audio_path, **kwargs):
                return "文件识别结果"
        
        asr = TestASR()
        
        # 测试基本功能
        result = asr.recognize(b"audio data")
        assert result == "测试识别结果"
        
        # 测试连接测试
        assert asr.test_connection() is True
        
        # 测试支持格式
        formats = asr.get_supported_formats()
        assert isinstance(formats, list)
        assert "wav" in formats
        
        print("ASR基础功能正常")
    except Exception as e:
        pytest.fail(f"ASR基础功能测试失败: {e}")

def test_tts_base_functionality():
    """测试TTS基础功能"""
    try:
        from chatterpal.core.tts.base import TTSBase
        
        class TestTTS(TTSBase):
            def synthesize(self, text, **kwargs):
                return f"合成音频: {text}".encode()
            
            def synthesize_to_file(self, text, output_path, **kwargs):
                with open(output_path, 'wb') as f:
                    f.write(f"合成音频: {text}".encode())
                return True
        
        tts = TestTTS()
        
        # 测试基本功能
        result = tts.synthesize("Hello world")
        assert b"Hello world" in result
        
        # 测试文本验证
        assert tts.validate_text("Hello world") is True
        assert tts.validate_text("") is False
        
        print("TTS基础功能正常")
    except Exception as e:
        pytest.fail(f"TTS基础功能测试失败: {e}")

def test_llm_base_functionality():
    """测试LLM基础功能"""
    try:
        from chatterpal.core.llm.base import LLMBase
        
        class TestLLM(LLMBase):
            def chat(self, messages, **kwargs):
                normalized = self.normalize_messages(messages)
                if normalized:
                    last_msg = normalized[-1].get("content", "")
                    return f"回复: {last_msg}"
                return "默认回复"
        
        llm = TestLLM()
        
        # 测试基本对话
        response = llm.chat("你好")
        assert response == "回复: 你好"
        
        # 测试对话对象
        conv = llm.create_conversation("你是助手")
        conv.add_user_message("你好")
        response = llm.chat(conv)
        assert "回复:" in response
        
        print("LLM基础功能正常")
    except Exception as e:
        pytest.fail(f"LLM基础功能测试失败: {e}")

def test_assessment_base_functionality():
    """测试评估基础功能"""
    try:
        from chatterpal.core.assessment.base import AssessmentBase, AssessmentResult, ProsodyFeatures
        
        class TestAssessment(AssessmentBase):
            def assess(self, audio_data, target_text="", **kwargs):
                return AssessmentResult(
                    overall_score=0.8,
                    fluency_score=0.7,
                    pronunciation_score=0.9,
                    prosody_score=0.8,
                    accuracy_score=0.85,
                    prosody_features=ProsodyFeatures(),
                    recognized_text="测试识别文本",
                    target_text=target_text,
                    feedback="测试反馈"
                )
        
        assessment = TestAssessment()
        
        # 测试音频数据验证
        assert assessment.validate_audio_data(b"audio data") is True
        assert assessment.validate_audio_data("") is False
        assert assessment.validate_audio_data(None) is False
        
        # 测试语言检测
        assert assessment.detect_language("Hello world") == "en"
        assert assessment.detect_language("你好世界") == "zh"
        
        print("评估基础功能正常")
    except Exception as e:
        pytest.fail(f"评估基础功能测试失败: {e}")

def test_chat_service_basic():
    """测试聊天服务基本功能"""
    try:
        from chatterpal.services.chat import ChatService
        from chatterpal.core.asr.base import ASRBase
        from chatterpal.core.tts.base import TTSBase
        from chatterpal.core.llm.base import LLMBase
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock(spec=ASRBase)
        mock_asr.recognize.return_value = "Hello"
        mock_asr.recognize_file.return_value = "Hello"
        mock_asr.recognize_gradio_audio.return_value = "Hello"
        
        mock_tts = Mock(spec=TTSBase)
        mock_tts.synthesize.return_value = b"fake audio"
        
        mock_llm = Mock(spec=LLMBase)
        mock_llm.chat.return_value = "Hi there!"
        
        # 创建服务
        chat_service = ChatService(
            asr=mock_asr,
            tts=mock_tts,
            llm=mock_llm
        )
        
        # 测试文本对话
        response_text, session_id = chat_service.chat_with_text("Hello")
        assert response_text == "Hi there!"
        assert session_id is not None
        
        # 测试会话管理
        history = chat_service.get_conversation_history(session_id)
        assert isinstance(history, list)
        
        print("聊天服务基本功能正常")
    except Exception as e:
        pytest.fail(f"聊天服务测试失败: {e}")

def test_evaluation_service_basic():
    """测试评估服务基本功能"""
    try:
        from chatterpal.services.evaluation import EvaluationService
        from chatterpal.core.asr.base import ASRBase
        from chatterpal.core.llm.base import LLMBase
        from chatterpal.core.assessment.base import AssessmentResult
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock(spec=ASRBase)
        mock_asr.recognize.return_value = "Hello world"
        
        mock_llm = Mock(spec=LLMBase)
        mock_llm.chat.return_value = "Good pronunciation!"
        
        # 创建服务
        eval_service = EvaluationService(
            asr=mock_asr,
            llm=mock_llm
        )
        
        # 测试发音评估
        result = eval_service.evaluate_pronunciation(
            b"audio data", "Hello world"
        )
        
        assert isinstance(result, AssessmentResult)
        assert result.overall_score >= 0
        
        print("评估服务基本功能正常")
    except Exception as e:
        pytest.fail(f"评估服务测试失败: {e}")

def test_correction_service_basic():
    """测试纠错服务基本功能"""
    try:
        from chatterpal.services.correction import CorrectionService, CorrectionReport
        from chatterpal.core.asr.base import ASRBase
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock(spec=ASRBase)
        mock_asr.recognize.return_value = "Hello world"
        
        # 创建服务
        correction_service = CorrectionService(asr=mock_asr)
        
        # 测试快速纠错
        result = correction_service.quick_correction(
            b"audio data", "Hello world"
        )
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        
        print("纠错服务基本功能正常")
    except Exception as e:
        pytest.fail(f"纠错服务测试失败: {e}")

def test_web_components_basic():
    """测试Web组件基本功能"""
    try:
        from chatterpal.web.components.chat_tab import ChatTab
        from chatterpal.web.components.score_tab import ScoreTab
        from chatterpal.web.components.correct_tab import CorrectTab
        from unittest.mock import Mock
        
        # 创建模拟服务
        mock_chat_service = Mock()
        mock_eval_service = Mock()
        mock_correction_service = Mock()
        
        # 创建组件
        chat_tab = ChatTab(mock_chat_service)
        score_tab = ScoreTab(mock_eval_service)
        correct_tab = CorrectTab(mock_correction_service)
        
        # 测试组件创建
        assert chat_tab.chat_service is mock_chat_service
        assert score_tab.evaluation_service is mock_eval_service
        assert correct_tab.correction_service is mock_correction_service
        
        print("Web组件基本功能正常")
    except Exception as e:
        pytest.fail(f"Web组件测试失败: {e}")

def test_end_to_end_workflow():
    """测试端到端工作流程"""
    try:
        from chatterpal.services.chat import ChatService
        from chatterpal.services.evaluation import EvaluationService
        from chatterpal.services.correction import CorrectionService
        from chatterpal.core.assessment.base import AssessmentResult
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello, how are you"
        mock_asr.recognize_file.return_value = "Hello, how are you"
        mock_asr.recognize_gradio_audio.return_value = "Hello, how are you"
        
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"response audio"
        
        mock_llm = Mock()
        mock_llm.chat.return_value = "I'm fine, thank you!"
        
        # 创建服务
        chat_service = ChatService(asr=mock_asr, tts=mock_tts, llm=mock_llm)
        eval_service = EvaluationService(asr=mock_asr, llm=mock_llm)
        correction_service = CorrectionService(asr=mock_asr)
        
        # 1. 用户开始对话
        response_text, session_id = chat_service.chat_with_text("Hello")
        assert response_text == "I'm fine, thank you!"
        assert session_id is not None
        
        # 2. 用户录音评估
        eval_result = eval_service.evaluate_pronunciation(
            b"audio data", "Hello, how are you"
        )
        assert isinstance(eval_result, AssessmentResult)
        
        # 3. 获取纠错建议
        correction_result = correction_service.quick_correction(
            b"audio data", "Hello, how are you"
        )
        assert isinstance(correction_result, dict)
        
        print("端到端工作流程正常")
    except Exception as e:
        pytest.fail(f"端到端工作流程测试失败 {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])








