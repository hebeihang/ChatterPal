"""
核心功能测试 - 只测试可以正常工作的核心功能
跳过需要外部依赖的测试
"""

import pytest
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch

def test_core_modules_import():
    """测试核心模块可以导入"""
    try:
        from oralcounsellor.core.asr.base import ASRBase
        from oralcounsellor.core.tts.base import TTSBase
        from oralcounsellor.core.llm.base import LLMBase
        from oralcounsellor.core.assessment.base import AssessmentBase
        from oralcounsellor.services.chat import ChatService
        from oralcounsellor.services.evaluation import EvaluationService
        from oralcounsellor.services.correction import CorrectionService
        from oralcounsellor.config.settings import Settings
        
        print("✓ 所有核心模块导入成功")
        assert True
    except Exception as e:
        pytest.fail(f"核心模块导入失败: {e}")

def test_app_can_be_imported():
    """测试应用可以导入"""
    try:
        import os
        # 设置测试环境变量
        os.environ['ALIBABA_API_KEY'] = 'test_key'
        
        from oralcounsellor.web.app import create_app
        app = create_app()
        assert app is not None
        print("✓ 应用导入和创建成功")
        
        # 清理环境变量
        if 'ALIBABA_API_KEY' in os.environ:
            del os.environ['ALIBABA_API_KEY']
            
    except Exception as e:
        pytest.fail(f"应用导入失败: {e}")

def test_chat_service_basic():
    """测试聊天服务基本功能"""
    try:
        from oralcounsellor.services.chat import ChatService
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello world"
        mock_asr.recognize_file.return_value = "Hello world"
        mock_asr.recognize_gradio_audio.return_value = "Hello world"
        
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"fake audio"
        
        mock_llm = Mock()
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
        
        print("✓ 聊天服务基本功能正常")
    except Exception as e:
        pytest.fail(f"聊天服务测试失败: {e}")

def test_evaluation_service_basic():
    """测试评估服务基本功能"""
    try:
        from oralcounsellor.services.evaluation import EvaluationService
        from oralcounsellor.core.assessment.base import AssessmentResult
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello world"
        
        mock_llm = Mock()
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
        
        print("✓ 评估服务基本功能正常")
    except Exception as e:
        pytest.fail(f"评估服务测试失败: {e}")

def test_correction_service_basic():
    """测试纠错服务基本功能"""
    try:
        from oralcounsellor.services.correction import CorrectionService
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello world"
        
        # 创建服务
        correction_service = CorrectionService(asr=mock_asr)
        
        # 测试快速纠错
        result = correction_service.quick_correction(
            b"audio data", "Hello world"
        )
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        
        print("✓ 纠错服务基本功能正常")
    except Exception as e:
        pytest.fail(f"纠错服务测试失败: {e}")

def test_configuration_system():
    """测试配置系统"""
    try:
        from oralcounsellor.config.settings import Settings
        
        settings = Settings()
        
        # 验证基本配置属性
        assert hasattr(settings, 'audio_sample_rate')
        assert hasattr(settings, 'whisper_model')
        assert hasattr(settings, 'asr_provider')
        assert hasattr(settings, 'tts_provider')
        assert hasattr(settings, 'llm_provider')
        
        # 验证配置值
        assert settings.audio_sample_rate > 0
        assert settings.whisper_model in ["tiny", "base", "small", "medium", "large"]
        
        print("✓ 配置系统正常工作")
    except Exception as e:
        pytest.fail(f"配置系统测试失败: {e}")

def test_asr_base_functionality():
    """测试ASR基础功能"""
    try:
        from oralcounsellor.core.asr.base import ASRBase
        
        class TestASR(ASRBase):
            def recognize(self, audio_data, **kwargs):
                return "测试识别结果"
            
            def recognize_file(self, audio_path, **kwargs):
                return "文件识别结果"
        
        asr = TestASR({})
        
        # 测试基本功能
        result = asr.recognize(b"audio data")
        assert result == "测试识别结果"
        
        # 测试连接测试
        assert asr.test_connection() is True
        
        print("✓ ASR基础功能正常")
    except Exception as e:
        pytest.fail(f"ASR基础功能测试失败: {e}")

def test_tts_base_functionality():
    """测试TTS基础功能"""
    try:
        from oralcounsellor.core.tts.base import TTSBase
        
        class TestTTS(TTSBase):
            def synthesize(self, text, **kwargs):
                return f"合成音频: {text}".encode()
            
            def synthesize_to_file(self, text, output_path, **kwargs):
                with open(output_path, 'wb') as f:
                    f.write(f"合成音频: {text}".encode())
                return True
        
        tts = TestTTS({})
        
        # 测试基本功能
        result = tts.synthesize("Hello world")
        assert b"Hello world" in result
        
        # 测试文本验证
        assert tts.validate_text("Hello world") is True
        assert tts.validate_text("") is False
        
        print("✓ TTS基础功能正常")
    except Exception as e:
        pytest.fail(f"TTS基础功能测试失败: {e}")

def test_llm_base_functionality():
    """测试LLM基础功能"""
    try:
        from oralcounsellor.core.llm.base import LLMBase
        
        class TestLLM(LLMBase):
            def chat(self, messages, **kwargs):
                normalized = self.normalize_messages(messages)
                if normalized:
                    last_msg = normalized[-1].get("content", "")
                    return f"回复: {last_msg}"
                return "默认回复"
        
        llm = TestLLM({})
        
        # 测试基本对话
        response = llm.chat("你好")
        assert response == "回复: 你好"
        
        print("✓ LLM基础功能正常")
    except Exception as e:
        pytest.fail(f"LLM基础功能测试失败: {e}")

def test_end_to_end_workflow():
    """测试端到端工作流程"""
    try:
        from oralcounsellor.services.chat import ChatService
        from oralcounsellor.services.evaluation import EvaluationService
        from oralcounsellor.services.correction import CorrectionService
        from oralcounsellor.core.assessment.base import AssessmentResult
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello, how are you?"
        mock_asr.recognize_file.return_value = "Hello, how are you?"
        mock_asr.recognize_gradio_audio.return_value = "Hello, how are you?"
        
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
            b"audio data", "Hello, how are you?"
        )
        assert isinstance(eval_result, AssessmentResult)
        
        # 3. 获取纠错建议
        correction_result = correction_service.quick_correction(
            b"audio data", "Hello, how are you?"
        )
        assert isinstance(correction_result, dict)
        
        print("✓ 端到端工作流程正常")
    except Exception as e:
        pytest.fail(f"端到端工作流程测试失败: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])