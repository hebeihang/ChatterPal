"""
Integration tests for service layer functionality.
Tests chat, evaluation, and correction services.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import numpy as np

from chatterpal.services.chat import ChatService
from chatterpal.services.evaluation import EvaluationService
from chatterpal.services.correction import CorrectionService, CorrectionReport
from chatterpal.core.asr.base import ASRBase
from chatterpal.core.tts.base import TTSBase
from chatterpal.core.llm.base import LLMBase
from chatterpal.core.assessment.base import AssessmentBase, AssessmentResult, ProsodyFeatures, AssessmentError


class MockASR(ASRBase):
    """Mock ASR for testing services."""
    
    def recognize(self, audio_data, **kwargs):
        return "Hello, how are you today"
    
    def recognize_file(self, audio_path, **kwargs):
        return "Hello, how are you today"


class MockTTS(TTSBase):
    """Mock TTS for testing services."""
    
    def synthesize(self, text, **kwargs):
        return b"fake audio data for: " + text.encode()
    
    def synthesize_to_file(self, text, output_path, **kwargs):
        with open(output_path, 'wb') as f:
            f.write(b"fake audio data for: " + text.encode())
        return True


class MockLLM(LLMBase):
    """Mock LLM for testing services."""
    
    def chat(self, messages, **kwargs):
        if isinstance(messages, str):
            return f"Response to: {messages}"
        elif isinstance(messages, list) and messages:
            last_message = messages[-1].get("content", "")
            return f"Response to: {last_message}"
        return "Default response"


class MockAssessment(AssessmentBase):
    """Mock Assessment for testing services."""
    
    def assess(self, audio_data, target_text="", **kwargs):
        return AssessmentResult(
            overall_score=0.85,
            fluency_score=0.8,
            pronunciation_score=0.9,
            prosody_score=0.8,
            accuracy_score=0.85,
            prosody_features=ProsodyFeatures(),
            recognized_text="Hello, how are you today",
            target_text=target_text,
            feedback="Good pronunciation overall",
            suggestions=["Practice vowel sounds", "Work on intonation"]
        )


class TestChatService:
    """Test the ChatService functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_asr = MockASR()
        self.mock_tts = MockTTS()
        self.mock_llm = MockLLM()
        
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
    
    def test_initialization(self):
        """Test ChatService initialization."""
        assert self.chat_service.asr is self.mock_asr
        assert self.chat_service.tts is self.mock_tts
        assert self.chat_service.llm is self.mock_llm
        assert len(self.chat_service.sessions) == 0
    
    def test_process_audio_input_bytes(self):
        """测试处理字节格式的音频输入"""
        audio_data = b"fake audio bytes"
        
        result = self.chat_service.chat_with_audio(audio_data)
        
        # chat_with_audio返回元组: (response_text, response_audio, session_id)
        assert len(result) == 3
        response_text, response_audio, session_id = result
        assert response_text.startswith("Response to:")
        assert response_audio is not None
        assert session_id is not None
    
    def test_process_audio_input_file(self):
        """测试处理文件路径格式的音频输入"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            result = self.chat_service.chat_with_audio(temp_path)
            
            # chat_with_audio返回元组: (response_text, response_audio, session_id)
            assert len(result) == 3
            response_text, response_audio, session_id = result
            assert response_text.startswith("Response to:")
        finally:
            os.unlink(temp_path)
    
    def test_process_audio_input_gradio_tuple(self):
        """测试处理Gradio音频元组格式"""
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        result = self.chat_service.chat_with_audio(audio_data)
        
        # chat_with_audio返回元组: (response_text, response_audio, session_id)
        assert len(result) == 3
        response_text, response_audio, session_id = result
        assert response_text.startswith("Response to:")
    
    def test_process_text_input(self):
        """测试处理文本输入"""
        text_input = "Hello, how are you"
        
        result = self.chat_service.chat_with_text(text_input)
        
        # chat_with_text返回元组: (response_text, session_id)
        assert len(result) == 2
        response_text, session_id = result
        assert response_text == f"Response to: {text_input}"
        assert session_id is not None
    
    def test_get_conversation_history(self):
        """Test getting conversation history."""
        # Create a session first
        session_id = self.chat_service.create_session()
        
        # Add some conversation
        self.chat_service.chat_with_text("Hello", session_id)
        self.chat_service.chat_with_text("How are you", session_id)
        
        history = self.chat_service.get_conversation_history(session_id)
        
        assert len(history) >= 2  # At least user messages
        assert any(msg["role"] == "user" for msg in history)
    
    def test_clear_conversation(self):
        """Test clearing conversation history."""
        # Create a session first
        session_id = self.chat_service.create_session()
        
        # Add some conversation
        self.chat_service.chat_with_text("Hello", session_id)
        
        self.chat_service.clear_conversation_history(session_id)
        
        history = self.chat_service.get_conversation_history(session_id)
        # Should only have system message if any
        assert len(history) <= 1
    
    def test_set_system_prompt(self):
        """Test setting system prompt."""
        system_prompt = "You are a helpful English teacher."
        
        # Create a session first
        session_id = self.chat_service.create_session()
        
        self.chat_service.set_system_prompt(session_id, system_prompt)
        
        history = self.chat_service.get_conversation_history(session_id)
        assert len(history) >= 1
        assert history[0]["role"] == "system"
        assert history[0]["content"] == system_prompt
    
    def test_generate_topic_suggestions(self):
        """Test generating topic suggestions."""
        # Create a session first
        session_id = self.chat_service.create_session()
        
        topics = self.chat_service.get_conversation_topics(session_id)
        
        assert isinstance(topics, list)
        # Topics might be empty for new session, so just check type
    
    def test_error_handling_asr_failure(self):
        """测试ASR失败时的错误处理"""
        # 模拟ASR抛出异常
        self.mock_asr.recognize = Mock(side_effect=Exception("ASR failed"))
        
        with pytest.raises(RuntimeError, match="语音对话失败"):
            self.chat_service.chat_with_audio(b"audio data")
    
    def test_error_handling_tts_failure(self):
        """测试TTS失败时的错误处理"""
        # 模拟TTS抛出异常
        self.mock_tts.synthesize = Mock(side_effect=Exception("TTS failed"))
        
        result = self.chat_service.chat_with_audio(b"audio data")
        
        # 应该仍然成功但没有音
        assert len(result) == 3
        response_text, response_audio, session_id = result
        assert response_text.startswith("Response to:")
        assert response_audio is None  # TTS失败时音频为None

    def test_process_chat_text_input(self):
        """测试 process_chat 方法的文本输入模式"""
        text_input = "Hello, how are you"
        
        result = self.chat_service.process_chat(
            text_input=text_input,
            use_text_input=True
        )
        
        # process_chat 返回 ((sample_rate, audio_data), formatted_history)
        assert len(result) == 2
        audio_output, formatted_history = result
        
        # 检查音频输出格
        assert len(audio_output) == 2
        sample_rate, audio_data = audio_output
        assert sample_rate == 16000
        assert audio_data is not None  # 应该有TTS生成的音
        
        # 检查格式化的历史记
        assert isinstance(formatted_history, list)
        assert len(formatted_history) >= 1
        # 最后一条记录应该包含用户输入和AI回复
        last_entry = formatted_history[-1]
        assert len(last_entry) == 2
        assert last_entry[0] == text_input  # 用户输入
        assert last_entry[1] is not None   # AI回复

    def test_process_chat_audio_input(self):
        """测试 process_chat 方法的语音输入模式"""
        audio_data = b"fake audio bytes"
        
        result = self.chat_service.process_chat(
            audio=audio_data,
            use_text_input=False
        )
        
        # process_chat 返回 ((sample_rate, audio_data), formatted_history)
        assert len(result) == 2
        audio_output, formatted_history = result
        
        # 检查音频输出格
        assert len(audio_output) == 2
        sample_rate, audio_data_out = audio_output
        assert sample_rate == 16000
        assert audio_data_out is not None
        
        # 检查格式化的历史记
        assert isinstance(formatted_history, list)
        assert len(formatted_history) >= 1

    def test_process_chat_with_session_id(self):
        """测试 process_chat 方法使用指定会话ID"""
        # 先创建一个会
        session_id = self.chat_service.create_session()
        
        result = self.chat_service.process_chat(
            text_input="Hello",
            use_text_input=True,
            session_id=session_id
        )
        
        assert len(result) == 2
        # 验证会话中确实有对话记录
        history = self.chat_service.get_conversation_history(session_id)
        assert len(history) >= 2  # 至少有用户消息和AI回复

    def test_process_chat_error_handling(self):
        """测试 process_chat 方法的错误处理"""
        # 测试空文本输
        result = self.chat_service.process_chat(
            text_input="",
            use_text_input=True
        )
        
        assert len(result) == 2
        audio_output, formatted_history = result
        
        # 错误情况下应该返回错误消
        assert len(formatted_history) >= 1
        error_entry = formatted_history[-1]
        assert "处理失败" in error_entry[1]

    def test_generate_topic_success(self):
        """测试 generate_topic 方法成功生成主题"""
        topic = self.chat_service.generate_topic()
        
        assert isinstance(topic, str)
        assert len(topic) > 0
        # MockLLM 会返"Mock response",但我们的方法会处理
        # 如果LLM返回的内容不合适,会使用默认主
        assert len(topic) >= 10  # 主题应该有一定长

    def test_generate_topic_llm_failure(self):
        """测试 generate_topic 方法在LLM失败时使用默认主题"""
        # 模拟LLM失败
        self.mock_llm.chat = Mock(side_effect=Exception("LLM failed"))
        
        topic = self.chat_service.generate_topic()
        
        assert isinstance(topic, str)
        assert len(topic) > 0
        # 应该返回TopicGenerator的默认主题之一或备用主
        # 新的实现会使用TopicGenerator的预定义主题
        assert len(topic) >= 10  # 主题应该有合理的长度
        # 验证主题格式(应该是问题或指令)
        assert topic.endswith('') or any(word in topic.lower() for word in ['tell me', 'describe', 'what', 'how'])

    def test_generate_topic_no_llm(self):
        """测试没有LLMgenerate_topic 方法使用默认主题"""
        # 创建没有LLM的ChatService
        chat_service_no_llm = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=None
        )
        
        topic = chat_service_no_llm.generate_topic()
        
        assert isinstance(topic, str)
        assert len(topic) > 0
        # 应该返回TopicGenerator的默认主题之一
        # 新的实现会使用TopicGenerator的预定义主题
        assert len(topic) >= 10  # 主题应该有合理的长度
        # 验证主题格式(应该是问题或指令)
        assert topic.endswith('') or any(word in topic.lower() for word in ['tell me', 'describe', 'what', 'how'])

    def test_clear_context_specific_session(self):
        """测试 clear_context 方法清除指定会话"""
        # 创建会话并添加对
        session_id = self.chat_service.create_session()
        self.chat_service.chat_with_text("Hello", session_id)
        
        # 验证有对话记
        history_before = self.chat_service.get_conversation_history(session_id)
        assert len(history_before) >= 2
        
        # 清除上下
        result = self.chat_service.clear_context(session_id)
        
        assert result is True
        
        # 验证对话记录被清
        history_after = self.chat_service.get_conversation_history(session_id)
        assert len(history_after) <= 1  # 只剩系统消息(如果有

    def test_clear_context_all_sessions(self):
        """测试 clear_context 方法清除所有会话"""
        # 创建多个会话
        session1 = self.chat_service.create_session()
        session2 = self.chat_service.create_session()
        
        # 添加对话
        self.chat_service.chat_with_text("Hello", session1)
        self.chat_service.chat_with_text("Hi", session2)
        
        # 验证有会
        assert len(self.chat_service.sessions) == 2
        
        # 清除所有上下文
        result = self.chat_service.clear_context()
        
        assert result is True
        assert len(self.chat_service.sessions) == 0

    def test_clear_context_nonexistent_session(self):
        """测试 clear_context 方法处理不存在的会话"""
        result = self.chat_service.clear_context("nonexistent_session_id")
        
        assert result is False


class TestEvaluationService:
    """Test the EvaluationService functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_asr = MockASR()
        self.mock_llm = MockLLM()
        
        self.evaluation_service = EvaluationService(
            asr=self.mock_asr,
            llm=self.mock_llm
        )
    
    def test_initialization(self):
        """Test EvaluationService initialization."""
        assert self.evaluation_service.asr is self.mock_asr
        assert self.evaluation_service.llm is self.mock_llm
    
    def test_evaluate_pronunciation_with_target(self):
        """测试带目标文本的发音评估"""
        audio_data = b"fake audio data"
        target_text = "Hello, how are you today"
        
        result = self.evaluation_service.evaluate_pronunciation(
            audio_data, target_text
        )
        
        # evaluate_pronunciation返回AssessmentResult对象
        assert isinstance(result, AssessmentResult)
        assert result.overall_score >= 0
        assert result.recognized_text == "Hello, how are you today"
        assert result.target_text == target_text
    
    def test_evaluate_pronunciation_without_target(self):
        """测试不带目标文本的发音评估"""
        audio_data = b"fake audio data"
        
        result = self.evaluation_service.evaluate_pronunciation(audio_data)
        
        # evaluate_pronunciation返回AssessmentResult对象
        assert isinstance(result, AssessmentResult)
        assert result.overall_score >= 0
        assert result.target_text == ""
    
    def test_evaluate_pronunciation_gradio_audio(self):
        """测试Gradio音频格式的发音评估"""
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        target_text = "Test sentence"
        
        result = self.evaluation_service.evaluate_pronunciation(
            audio_data, target_text
        )
        
        # evaluate_pronunciation返回AssessmentResult对象
        assert isinstance(result, AssessmentResult)
        assert result.target_text == target_text
    
    def test_generate_default_feedback(self):
        """测试生成默认反馈"""
        scores = {
            "overall": 0.85,
            "fluency": 0.8,
            "pronunciation": 0.9,
            "accuracy": 0.85
        }
        similarity = 0.9
        
        feedback = self.evaluation_service._generate_default_feedback(
            scores, similarity
        )
        
        assert isinstance(feedback, str)
        assert len(feedback) > 0
    
    def test_calculate_text_similarity(self):
        """测试文本相似度计算"""
        recognized_text = "Hello world"
        target_text = "Hello world"
        
        score = self.evaluation_service._calculate_similarity(
            recognized_text, target_text
        )
        
        assert score == 1.0
        
        # 测试不同文本
        score = self.evaluation_service._calculate_similarity(
            "Hello there", "Hello world"
        )
        
        assert 0 <= score <= 1
    
    def test_error_handling_asr_failure(self):
        """测试ASR失败时的错误处理"""
        self.mock_asr.recognize = Mock(side_effect=Exception("ASR failed"))
        
        with pytest.raises(AssessmentError):
            self.evaluation_service.evaluate_pronunciation(b"audio data")
    
    def test_error_handling_invalid_audio(self):
        """测试无效音频数据的错误处理"""
        with pytest.raises(AssessmentError):
            self.evaluation_service.evaluate_pronunciation(None)


class TestCorrectionService:
    """Test the CorrectionService functionality."""
    
    def setup_method(self):
        """设置测试夹具"""
        self.mock_asr = MockASR()
        
        self.correction_service = CorrectionService(
            asr=self.mock_asr
        )
    
    def test_initialization(self):
        """测试CorrectionService初始化"""
        assert self.correction_service.asr is self.mock_asr
        assert self.correction_service.corrector is not None
        assert self.correction_service.phoneme_analyzer is not None
        assert self.correction_service.prosody_analyzer is not None
    
    def test_comprehensive_correction(self):
        """测试综合纠错分析"""
        audio_data = b"fake audio data"
        target_text = "Hello, how are you today"
        
        result = self.correction_service.comprehensive_correction(
            audio_data, target_text
        )
        
        # comprehensive_correction返回CorrectionReport对象
        assert isinstance(result, CorrectionReport)
        assert result.overall_score >= 0
        assert isinstance(result.pronunciation_errors, list)
        assert isinstance(result.improvement_suggestions, list)
    
    def test_comprehensive_correction_gradio_audio(self):
        """测试Gradio音频格式的综合纠错"""
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        target_text = "Test sentence"
        
        result = self.correction_service.comprehensive_correction(
            audio_data, target_text
        )
        
        assert isinstance(result, CorrectionReport)
    
    def test_quick_correction(self):
        """测试快速纠错错功能"""
        # 先进行音频分
        result = self.correction_service.quick_correction(
            b"audio data", "Hello world"
        )
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "main_issues" in result
        assert "key_suggestions" in result
    
    def test_get_service_status(self):
        """测试获取服务状态"""
        status = self.correction_service.get_service_status()
        
        assert isinstance(status, dict)
        assert "asr_available" in status
        assert "corrector_available" in status
        assert "phoneme_analyzer_available" in status
        assert "prosody_analyzer_available" in status
    

    
    def test_error_handling_correction_failure(self):
        """测试纠错失败时的错误处理"""
        self.mock_asr.recognize = Mock(side_effect=Exception("ASR failed"))
        
        with pytest.raises(AssessmentError):
            self.correction_service.comprehensive_correction(b"audio data")
    
    def test_error_handling_invalid_audio(self):
        """测试无效音频数据的错误处理"""
        with pytest.raises(AssessmentError):
            self.correction_service.comprehensive_correction(None)


class TestServiceIntegration:
    """Test integration between different services."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_asr = MockASR()
        self.mock_tts = MockTTS()
        self.mock_llm = MockLLM()
        self.mock_assessment = MockAssessment()
        
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        self.evaluation_service = EvaluationService(
            asr=self.mock_asr,
            llm=self.mock_llm
        )
        
        self.correction_service = CorrectionService(
            asr=self.mock_asr
        )
    
    def test_chat_to_evaluation_workflow(self):
        """测试从对话到评估的工作流程"""
        # 开始对
        chat_result = self.chat_service.chat_with_text("Hello, how are you")
        assert len(chat_result) == 2
        response_text, session_id = chat_result
        
        # 模拟用户录音进行评估
        user_audio = b"user recorded audio"
        eval_result = self.evaluation_service.evaluate_pronunciation(
            user_audio, "Hello, how are you"
        )
        assert isinstance(eval_result, AssessmentResult)
    
    def test_evaluation_to_correction_workflow(self):
        """测试从评估到纠错的工作流程"""
        # 开始评
        audio_data = b"fake audio data"
        target_text = "Hello world"
        
        eval_result = self.evaluation_service.evaluate_pronunciation(
            audio_data, target_text
        )
        assert isinstance(eval_result, AssessmentResult)
        
        # 使用评估结果进行详细纠错
        correction_result = self.correction_service.comprehensive_correction(
            audio_data, target_text
        )
        assert isinstance(correction_result, CorrectionReport)
    
    def test_full_workflow_integration(self):
        """测试完整工作流程集成"""
        # 1. 对话交互
        chat_result = self.chat_service.chat_with_text("Practice sentence")
        assert len(chat_result) == 2
        
        # 2. 用户录音(模拟)
        user_audio = b"user recorded audio"
        
        # 3. 评估发音
        eval_result = self.evaluation_service.evaluate_pronunciation(
            user_audio, "Practice sentence"
        )
        assert isinstance(eval_result, AssessmentResult)
        
        # 4. 获取详细纠错
        correction_result = self.correction_service.comprehensive_correction(
            user_audio, "Practice sentence"
        )
        assert isinstance(correction_result, CorrectionReport)
        
        # 5. 为对话生成反
        feedback_text = f"Your pronunciation score: {eval_result.overall_score:.2f}"
        feedback_result = self.chat_service.chat_with_text(feedback_text)
        assert len(feedback_result) == 2


if __name__ == "__main__":
    pytest.main([__file__])








