"""
Final functionality verification test
Tests all core functionality without complex app startup
"""

import pytest
import os
from unittest.mock import Mock, patch

def test_all_modules_import_successfully():
    """测试所有模块可以成功导入"""
    try:
        # 核心模块
        from chatterpal.core.asr.base import ASRBase
        from chatterpal.core.tts.base import TTSBase
        from chatterpal.core.llm.base import LLMBase
        from chatterpal.core.assessment.base import AssessmentBase
        
        # 服务
        from chatterpal.services.chat import ChatService
        from chatterpal.services.evaluation import EvaluationService
        from chatterpal.services.correction import CorrectionService
        
        # Web组件
        from chatterpal.web.components.chat_tab import ChatTab
        from chatterpal.web.components.score_tab import ScoreTab
        from chatterpal.web.components.correct_tab import CorrectTab
        
        # 配置系统
        from chatterpal.config.settings import Settings
        
        print("所有模块导入成功")
        return True
        
    except Exception as e:
        pytest.fail(f"模块导入失败: {e}")

def test_chat_functionality():
    """测试聊天功能"""
    try:
        from chatterpal.services.chat import ChatService
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello world"
        mock_asr.recognize_file.return_value = "Hello world"
        mock_asr.recognize_gradio_audio.return_value = "Hello world"
        
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"fake audio"
        
        mock_llm = Mock()
        mock_llm.chat.return_value = "Hi there! How can I help you"
        
        # 创建聊天服务
        chat_service = ChatService(asr=mock_asr, tts=mock_tts, llm=mock_llm)
        
        # 测试文本对话
        response_text, session_id = chat_service.chat_with_text("Hello")
        assert response_text == "Hi there! How can I help you"
        assert session_id is not None
        
        # 测试音频对话
        response_text, response_audio, session_id2 = chat_service.chat_with_audio(b"audio data")
        assert response_text == "Hi there! How can I help you"
        assert response_audio == b"fake audio"
        
        print("聊天功能正常工作")
        return True
        
    except Exception as e:
        pytest.fail(f"聊天功能测试失败: {e}")

def test_evaluation_functionality():
    """测试评分功能"""
    try:
        from chatterpal.services.evaluation import EvaluationService
        from chatterpal.core.assessment.base import AssessmentResult
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello world"
        
        mock_llm = Mock()
        mock_llm.chat.return_value = "Good pronunciation!"
        
        # 创建评估服务
        eval_service = EvaluationService(asr=mock_asr, llm=mock_llm)
        
        # 测试发音评估
        result = eval_service.evaluate_pronunciation(b"audio data", "Hello world")
        assert isinstance(result, AssessmentResult)
        assert result.overall_score >= 0
        assert result.recognized_text == "Hello world"
        
        print("评分功能正常工作")
        return True
        
    except Exception as e:
        pytest.fail(f"评分功能测试失败: {e}")

def test_correction_functionality():
    """测试纠错功能"""
    try:
        from chatterpal.services.correction import CorrectionService
        from unittest.mock import Mock
        
        # 创建模拟组件
        mock_asr = Mock()
        mock_asr.recognize.return_value = "Hello world"
        
        # 创建纠错服务
        correction_service = CorrectionService(asr=mock_asr)
        
        # 测试快速纠错
        result = correction_service.quick_correction(b"audio data", "Hello world")
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "main_issues" in result
        assert "key_suggestions" in result
        
        print("纠错功能正常工作")
        return True
        
    except Exception as e:
        pytest.fail(f"纠错功能测试失败: {e}")

def test_web_components_functionality():
    """测试Web组件功能"""
    try:
        from chatterpal.web.components.chat_tab import ChatTab
        from chatterpal.web.components.score_tab import ScoreTab
        from chatterpal.web.components.correct_tab import CorrectTab
        from unittest.mock import Mock
        
        # 创建模拟服务
        mock_chat_service = Mock()
        mock_eval_service = Mock()
        mock_correction_service = Mock()
        
        # 创建Web组件
        chat_tab = ChatTab(mock_chat_service)
        score_tab = ScoreTab(mock_eval_service)
        correct_tab = CorrectTab(mock_correction_service)
        
        # 验证组件创建成功
        assert chat_tab.chat_service is mock_chat_service
        assert score_tab.evaluation_service is mock_eval_service
        assert correct_tab.correction_service is mock_correction_service
        
        print("Web组件功能正常工作")
        return True
        
    except Exception as e:
        pytest.fail(f"Web组件功能测试失败: {e}")

def test_configuration_system():
    """测试配置值系统"""
    try:
        from chatterpal.config.settings import Settings
        
        # 创建配置实例
        settings = Settings()
        
        # 验证基本配置属
        assert hasattr(settings, 'audio_sample_rate')
        assert hasattr(settings, 'whisper_model')
        assert hasattr(settings, 'asr_provider')
        assert hasattr(settings, 'tts_provider')
        assert hasattr(settings, 'llm_provider')
        
        # 验证配置
        assert settings.audio_sample_rate > 0
        assert settings.whisper_model in ["tiny", "base", "small", "medium", "large"]
        assert settings.asr_provider in ["whisper", "aliyun"]
        assert settings.tts_provider in ["edge"]
        assert settings.llm_provider in ["alibaba", "openai"]
        
        print("配置系统正常工作")
        return True
        
    except Exception as e:
        pytest.fail(f"配置系统测试失败: {e}")

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
        assert eval_result.recognized_text == "Hello, how are you"
        
        # 3. 获取纠错建议
        correction_result = correction_service.quick_correction(
            b"audio data", "Hello, how are you"
        )
        assert isinstance(correction_result, dict)
        assert "overall_score" in correction_result
        
        # 4. 继续对话
        feedback_text = f"My score is {eval_result.overall_score:.2f}"
        final_response, _ = chat_service.chat_with_text(feedback_text, session_id)
        assert final_response == "I'm fine, thank you!"
        
        print("端到端工作流程正常")
        return True
        
    except Exception as e:
        pytest.fail(f"端到端工作流程测试失败 {e}")

def test_project_structure():
    """测试项目结构"""
    try:
        import os
        
        # 检查关键目录和文件
        required_paths = [
            "src/chatterpal",
            "src/chatterpal/core",
            "src/chatterpal/services",
            "src/chatterpal/web",
            "src/chatterpal/config",
            "src/chatterpal/utils",
            "tests",
            "docs",
            "scripts",
            "pyproject.toml",
            "README.md"
        ]
        
        for path in required_paths:
            assert os.path.exists(path), f"缺少必要的路径 {path}"
        
        print("项目结构完整")
        return True
        
    except Exception as e:
        pytest.fail(f"项目结构测试失败: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])








