"""
错误场景集成测试
测试网络中断和恢复、音频设备故障、服务超时处理场
验证错误提示的用户友好
"""

import pytest
import numpy as np
import tempfile
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import List, Tuple, Any

from chatterpal.services.chat import ChatService
from chatterpal.web.components.chat_tab import ChatTab
from chatterpal.utils.preferences import UserPreferences
from chatterpal.core.errors import (
    error_handler, ChatModuleError, AudioInputError, 
    SpeechRecognitionError, SpeechSynthesisError
)


class TestNetworkInterruptionScenarios:
    """网络中断和恢复场景测试"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建可控制的模拟组件
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 网络状态控
        self.network_available = True
        
        # 设置网络相关的模拟行
        def asr_with_network_check(*args, **kwargs):
            if not self.network_available:
                raise Exception("网络连接超时")
            return "Hello, how are you"
        
        def tts_with_network_check(*args, **kwargs):
            if not self.network_available:
                raise Exception("网络连接超时")
            return b"fake audio data"
        
        def llm_with_network_check(*args, **kwargs):
            if not self.network_available:
                raise Exception("网络连接超时")
            return "I'm fine, thank you!"
        
        self.mock_asr.recognize.side_effect = asr_with_network_check
        self.mock_asr.recognize_file.side_effect = asr_with_network_check
        self.mock_asr.recognize_gradio_audio.side_effect = asr_with_network_check
        
        self.mock_tts.synthesize.side_effect = tts_with_network_check
        
        self.mock_llm.chat.side_effect = llm_with_network_check
        
        # 创建增强的错误处理方
        from dataclasses import dataclass
        
        @dataclass
        class ASRResult:
            text: str
            confidence: float = 0.9
            
        def asr_enhanced_with_network(*args, **kwargs):
            if not self.network_available:
                raise error_handler.create_error("NETWORK_ERROR", message="网络连接不可用")
            return ASRResult(text="Hello, how are you")
        
        @dataclass
        class TTSResult:
            audio_data: bytes
            synthesis_time: float = 1.0
            cached: bool = False
            
        def tts_enhanced_with_network(*args, **kwargs):
            if not self.network_available:
                raise error_handler.create_error("NETWORK_ERROR", message="网络连接不可用")
            return TTSResult(audio_data=b"fake audio data")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_with_network
        self.mock_tts.synthesize_with_error_handling = tts_enhanced_with_network
        
        # 创建ChatService
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        # 创建ChatTab
        self.temp_dir = tempfile.mkdtemp()
        with patch('chatterpal.utils.preferences.get_preferences_manager') as mock_get_prefs:
            self.preferences = UserPreferences(config_dir=self.temp_dir)
            mock_get_prefs.return_value = self.preferences
            self.chat_tab = ChatTab(self.chat_service)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_network_interruption_during_voice_chat(self):
        """
        测试语音对话过程中的网络中断
        需 1.3, 4.1, 4.2, 4.3, 4.4
        """
        # 1. 正常建立会话
        session_id = self.chat_service.create_session()
        
        # 2. 正常进行一轮对
        response1, _ = self.chat_service.chat_with_text("Hello", session_id)
        assert response1 == "I'm fine, thank you!"
        
        # 3. 模拟网络中断
        self.network_available = False
        
        # 4. 尝试语音对话,应该失败但有友好错误提
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 验证错误处理
        assert len(chat_history) > 0
        error_message = str(chat_history).lower()
        assert any(keyword in error_message for keyword in [
            "网络", "连接", "不可用", "重试", "稍后"
        ])
        
        # 5. 模拟网络恢复
        self.network_available = True
        
        # 6. 再次尝试对话,应该成
        result = self.chat_tab._handle_chat(
            text_input="Network is back",
            audio=None,
            chat_history=[],
            use_text=True
        )
        
        audio_output, chat_history = result
        
        # 验证恢复后正常工
        assert len(chat_history) > 0
        success_message = str(chat_history)
        assert "I'm fine, thank you!" in success_message
    
    def test_network_timeout_handling(self):
        """
        测试网络超时处理
        需 1.3, 2.3, 4.4
        """
        # 模拟超时错误
        def timeout_error(*args, **kwargs):
            import socket
            raise socket.timeout("连接超时")
        
        self.mock_llm.chat.side_effect = timeout_error
        
        # 尝试文本对话
        with pytest.raises(Exception) as exc_info:
            self.chat_service.chat_with_text("Hello")
        
        # 验证超时错误被正确处
        assert "超时" in str(exc_info.value) or "timeout" in str(exc_info.value).lower()
    
    def test_network_recovery_with_retry_mechanism(self):
        """
        测试网络恢复的重试机
        需 4.1, 4.2, 4.3
        """
        # 设置重试计数
        retry_count = 0
        max_retries = 3
        
        def failing_then_success(*args, **kwargs):
            nonlocal retry_count
            retry_count += 1
            if retry_count < max_retries:
                raise Exception("网络暂时不可")
            return "重试成功后的回复"
        
        self.mock_llm.chat.side_effect = failing_then_success
        
        # 使用ChatService的重试机
        session_id = self.chat_service.create_session()
        
        # 多次尝试直到成功
        success = False
        for attempt in range(max_retries + 1):
            try:
                response, _ = self.chat_service.chat_with_text("Test retry", session_id)
                success = True
                break
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(0.1)  # 短暂等待后重
                    continue
                else:
                    raise
        
        assert success
        assert retry_count == max_retries
    
    def test_partial_network_failure(self):
        """
        测试部分网络服务失败的处
        需 1.3, 2.3
        """
        # 只让TTS服务失败,其他服务正
        def tts_network_fail(*args, **kwargs):
            raise Exception("TTS服务网络错误")
        
        self.mock_tts.synthesize.side_effect = tts_network_fail
        self.mock_tts.synthesize_with_error_handling.side_effect = tts_network_fail
        
        # 进行文本对话
        result = self.chat_tab._handle_chat(
            text_input="Hello world",
            audio=None,
            chat_history=[],
            use_text=True
        )
        
        audio_output, chat_history = result
        
        # 文本对话应该成功,但没有音频输出
        assert len(chat_history) > 0
        assert "I'm fine, thank you!" in str(chat_history)
        assert audio_output == (16000, [])  # 没有音频输出


class TestAudioDeviceFailureScenarios:
    """音频设备故障场景测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 音频设备状态控
        self.microphone_available = True
        self.speaker_available = True
        
        # 设置音频设备相关的模拟行
        def asr_with_device_check(*args, **kwargs):
            if not self.microphone_available:
                raise Exception("麦克风设备不可用")
            return "Hello from microphone"
        
        def tts_with_device_check(*args, **kwargs):
            if not self.speaker_available:
                raise Exception("音频输出设备不可")
            return b"fake audio output"
        
        self.mock_asr.recognize.side_effect = asr_with_device_check
        self.mock_asr.recognize_file.side_effect = asr_with_device_check
        self.mock_asr.recognize_gradio_audio.side_effect = asr_with_device_check
        
        self.mock_tts.synthesize.side_effect = tts_with_device_check
        
        self.mock_llm.chat.return_value = "Device test response"
        
        # 创建增强的错误处理方
        from dataclasses import dataclass
        
        @dataclass
        class ASRResult:
            text: str
            confidence: float = 0.9
            
        def asr_enhanced_with_device(*args, **kwargs):
            if not self.microphone_available:
                raise error_handler.create_error("AUDIO_DEVICE_ERROR", message="麦克风设备不可用")
            return ASRResult(text="Hello from microphone")
        
        @dataclass
        class TTSResult:
            audio_data: bytes
            synthesis_time: float = 1.0
            cached: bool = False
            
        def tts_enhanced_with_device(*args, **kwargs):
            if not self.speaker_available:
                raise error_handler.create_error("AUDIO_DEVICE_ERROR", message="音频输出设备不可用")
            return TTSResult(audio_data=b"fake audio output")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_with_device
        self.mock_tts.synthesize_with_error_handling = tts_enhanced_with_device
        
        # 创建服务
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        # 创建ChatTab
        self.temp_dir = tempfile.mkdtemp()
        with patch('chatterpal.utils.preferences.get_preferences_manager') as mock_get_prefs:
            self.preferences = UserPreferences(config_dir=self.temp_dir)
            mock_get_prefs.return_value = self.preferences
            self.chat_tab = ChatTab(self.chat_service)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_microphone_device_failure(self):
        """
        测试麦克风设备故
        需 4.1, 4.2, 4.3
        """
        # 1. 模拟麦克风不可用
        self.microphone_available = False
        
        # 2. 尝试语音输入
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 3. 验证错误处理和用户友好提
        assert len(chat_history) > 0
        error_message = str(chat_history).lower()
        assert any(keyword in error_message for keyword in [
            "麦克风", "设备", "不可用", "权限", "文本输入"
        ])
        
        # 4. 验证建议切换到文本输
        # 错误消息应该建议用户使用文本输入
        assert any(keyword in error_message for keyword in [
            "文本", "输入", "切换", "替代"
        ])
    
    def test_speaker_device_failure(self):
        """
        测试扬声器设备故
        需 2.3, 5.3
        """
        # 1. 模拟扬声器不可用
        self.speaker_available = False
        
        # 2. 进行文本对话(应该成功,但没有音频输出)
        result = self.chat_tab._handle_chat(
            text_input="Hello, test speaker failure",
            audio=None,
            chat_history=[],
            use_text=True
        )
        
        audio_output, chat_history = result
        
        # 3. 验证文本对话成功
        assert len(chat_history) > 0
        assert "Device test response" in str(chat_history)
        
        # 4. 验证没有音频输出(优雅降级)
        assert audio_output == (16000, [])
    
    def test_audio_permission_denied(self):
        """
        测试音频权限被拒绝的场景
        需 4.1, 4.2
        """
        # 模拟权限错误
        def permission_denied(*args, **kwargs):
            raise PermissionError("麦克风权限被拒绝")
        
        self.mock_asr.recognize.side_effect = permission_denied
        self.mock_asr.recognize_file.side_effect = permission_denied
        self.mock_asr.recognize_gradio_audio.side_effect = permission_denied
        
        def asr_enhanced_permission_denied(*args, **kwargs):
            raise error_handler.create_error("AUDIO_PERMISSION_ERROR", message="麦克风权限被拒绝")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_permission_denied
        
        # 尝试语音输入
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 验证权限错误的友好提
        assert len(chat_history) > 0
        error_message = str(chat_history).lower()
        assert any(keyword in error_message for keyword in [
            "权限", "麦克风", "允许", "设置", "浏览器"
        ])
    
    def test_audio_format_not_supported(self):
        """
        测试不支持的音频格式
        需 4.1, 4.3
        """
        # 模拟格式不支持错
        def format_error(*args, **kwargs):
            raise ValueError("不支持的音频格式")
        
        self.mock_asr.recognize.side_effect = format_error
        self.mock_asr.recognize_gradio_audio.side_effect = format_error
        
        def asr_enhanced_format_error(*args, **kwargs):
            raise error_handler.create_error("AUDIO_FORMAT_ERROR", message="不支持的音频格式")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_format_error
        
        # 尝试语音输入
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 验证格式错误的友好提
        assert len(chat_history) > 0
        error_message = str(chat_history).lower()
        assert any(keyword in error_message for keyword in [
            "格式", "支持", "音频", "重新录制"
        ])


class TestServiceTimeoutScenarios:
    """服务超时处理场景测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 创建ChatService
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        # 创建ChatTab
        self.temp_dir = tempfile.mkdtemp()
        with patch('chatterpal.utils.preferences.get_preferences_manager') as mock_get_prefs:
            self.preferences = UserPreferences(config_dir=self.temp_dir)
            mock_get_prefs.return_value = self.preferences
            self.chat_tab = ChatTab(self.chat_service)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_asr_service_timeout(self):
        """
        测试ASR服务超时
        需 1.3, 4.4
        """
        # 模拟ASR超时
        def asr_timeout(*args, **kwargs):
            time.sleep(0.1)  # 模拟处理时间
            raise TimeoutError("ASR服务响应超时")
        
        self.mock_asr.recognize.side_effect = asr_timeout
        self.mock_asr.recognize_gradio_audio.side_effect = asr_timeout
        
        def asr_enhanced_timeout(*args, **kwargs):
            raise error_handler.create_error("ASR_TIMEOUT", message="语音识别服务响应超时")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_timeout
        
        # 尝试语音输入
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 验证超时错误的友好提
        assert len(chat_history) > 0
        error_message = str(chat_history).lower()
        assert any(keyword in error_message for keyword in [
            "超时", "响应", "重试", "稍后"
        ])
    
    def test_tts_service_timeout(self):
        """
        测试TTS服务超时
        需 2.3, 5.3
        """
        # 模拟TTS超时
        def tts_timeout(*args, **kwargs):
            time.sleep(0.1)  # 模拟处理时间
            raise TimeoutError("TTS服务响应超时")
        
        self.mock_tts.synthesize.side_effect = tts_timeout
        
        def tts_enhanced_timeout(*args, **kwargs):
            raise error_handler.create_error("TTS_TIMEOUT", message="语音合成服务响应超时")
        
        self.mock_tts.synthesize_with_error_handling = tts_enhanced_timeout
        
        # 设置LLM正常工作
        self.mock_llm.chat.return_value = "TTS timeout test response"
        
        # 进行文本对话
        result = self.chat_tab._handle_chat(
            text_input="Test TTS timeout",
            audio=None,
            chat_history=[],
            use_text=True
        )
        
        audio_output, chat_history = result
        
        # 验证文本对话成功,但没有音频输出
        assert len(chat_history) > 0
        assert "TTS timeout test response" in str(chat_history)
        assert audio_output == (16000, [])  # TTS超时,没有音频输
    
    def test_llm_service_timeout(self):
        """
        测试LLM服务超时
        需 1.3
        """
        # 模拟LLM超时
        def llm_timeout(*args, **kwargs):
            time.sleep(0.1)  # 模拟处理时间
            raise TimeoutError("LLM服务响应超时")
        
        self.mock_llm.chat.side_effect = llm_timeout
        
        # 尝试文本对话
        with pytest.raises(Exception) as exc_info:
            self.chat_service.chat_with_text("Test LLM timeout")
        
        # 验证超时错误被正确处
        error_str = str(exc_info.value).lower()
        assert "超时" in error_str or "timeout" in error_str
    
    def test_multiple_service_timeouts(self):
        """
        测试多个服务同时超时
        需 1.3, 2.3, 4.4
        """
        # 模拟所有服务都超时
        def universal_timeout(*args, **kwargs):
            raise TimeoutError("服务响应超时")
        
        self.mock_asr.recognize.side_effect = universal_timeout
        self.mock_asr.recognize_gradio_audio.side_effect = universal_timeout
        self.mock_tts.synthesize.side_effect = universal_timeout
        self.mock_llm.chat.side_effect = universal_timeout
        
        def asr_enhanced_timeout(*args, **kwargs):
            raise error_handler.create_error("ASR_TIMEOUT", message="语音识别服务超时")
        
        def tts_enhanced_timeout(*args, **kwargs):
            raise error_handler.create_error("TTS_TIMEOUT", message="语音合成服务超时")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_timeout
        self.mock_tts.synthesize_with_error_handling = tts_enhanced_timeout
        
        # 尝试语音对话
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 验证系统不会崩溃,有友好的错误提
        assert len(chat_history) > 0
        error_message = str(chat_history).lower()
        assert any(keyword in error_message for keyword in [
            "超时", "服务", "不可用", "重试", "稍后"
        ])
    
    def test_timeout_with_retry_mechanism(self):
        """
        测试超时后的重试机制
        需 4.4
        """
        # 设置重试计数
        retry_count = 0
        
        def timeout_then_success(*args, **kwargs):
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise TimeoutError("服务暂时超时")
            return "重试成功的回复"
        
        self.mock_llm.chat.side_effect = timeout_then_success
        
        # 手动实现重试逻辑
        session_id = self.chat_service.create_session()
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                response, _ = self.chat_service.chat_with_text("Test timeout retry", session_id)
                success = True
                break
            except TimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # 短暂等待后重
                    continue
                else:
                    break
        
        assert success
        assert retry_count == 3


class TestUserFriendlyErrorMessages:
    """用户友好错误消息测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 创建ChatService
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        # 创建ChatTab
        self.temp_dir = tempfile.mkdtemp()
        with patch('chatterpal.utils.preferences.get_preferences_manager') as mock_get_prefs:
            self.preferences = UserPreferences(config_dir=self.temp_dir)
            mock_get_prefs.return_value = self.preferences
            self.chat_tab = ChatTab(self.chat_service)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_error_message_localization(self):
        """
        测试错误消息的本地化
        需 1.3, 2.3, 4.1, 4.2, 4.3, 4.4
        """
        # 测试不同类型的错误消
        error_scenarios = [
            {
                "error": Exception("Network connection failed"),
                "expected_keywords": ["网络", "连接", "重试"]
            },
            {
                "error": PermissionError("Microphone access denied"),
                "expected_keywords": ["权限", "麦克风", "允许"]
            },
            {
                "error": TimeoutError("Service timeout"),
                "expected_keywords": ["超时", "服务", "稍后"]
            },
            {
                "error": ValueError("Invalid audio format"),
                "expected_keywords": ["格式", "音频", "支持"]
            }
        ]
        
        for scenario in error_scenarios:
            # 设置错误
            self.mock_asr.recognize_gradio_audio.side_effect = scenario["error"]
            
            def asr_enhanced_error(*args, **kwargs):
                raise scenario["error"]
            
            self.mock_asr.recognize_with_error_handling = asr_enhanced_error
            
            # 触发错误
            sample_rate = 16000
            audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
            gradio_audio = (sample_rate, audio_array)
            
            result = self.chat_tab._handle_chat(
                audio=gradio_audio,
                text_input="",
                chat_history=[],
                use_text=False
            )
            
            audio_output, chat_history = result
            
            # 验证错误消息包含预期关键
            assert len(chat_history) > 0
            error_message = str(chat_history).lower()
            
            # 检查是否包含预期关键词或通用友好词汇
            expected_keywords = scenario["expected_keywords"] + ["问题", "重试", "稍后"]
            has_expected_keyword = any(
                keyword in error_message 
                for keyword in expected_keywords
            )
            assert has_expected_keyword, f"错误消息 '{error_message}' 不包含预期关键词 {expected_keywords}"
    
    def test_error_message_actionable_suggestions(self):
        """
        测试错误消息包含可操作的建议
        需 1.3, 4.1, 4.2, 4.3
        """
        # 模拟麦克风权限错
        def permission_error(*args, **kwargs):
            raise PermissionError("麦克风权限被拒绝")
        
        self.mock_asr.recognize_gradio_audio.side_effect = permission_error
        
        def asr_enhanced_permission_error(*args, **kwargs):
            raise error_handler.create_error("AUDIO_PERMISSION_ERROR", message="麦克风权限被拒绝")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_permission_error
        
        # 触发错误
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 验证错误消息包含可操作的建议
        assert len(chat_history) > 0
        error_message = str(chat_history).lower()
        
        # 应该包含具体的解决建
        actionable_keywords = [
            "设置", "允许", "权限", "浏览器", "文本输入", "切换"
        ]
        has_actionable_suggestion = any(
            keyword in error_message 
            for keyword in actionable_keywords
        )
        assert has_actionable_suggestion, f"错误消息应包含可操作建议: {error_message}"
    
    def test_error_message_severity_levels(self):
        """
        测试不同严重程度的错误消
        需 1.3, 2.3, 4.4
        """
        # 轻微错误:TTS失败(不影响核心功能
        def tts_minor_error(*args, **kwargs):
            raise Exception("语音合成暂时不可")
        
        self.mock_tts.synthesize_with_error_handling = tts_minor_error
        self.mock_llm.chat.return_value = "Text response works fine"
        
        result = self.chat_tab._handle_chat(
            text_input="Test minor error",
            audio=None,
            chat_history=[],
            use_text=True
        )
        
        audio_output, chat_history = result
        
        # 轻微错误:文本对话应该成功,只是没有音频
        assert len(chat_history) > 0
        assert "Text response works fine" in str(chat_history)
        assert audio_output == (16000, [])
        
        # 严重错误:LLM失败(影响核心功能)
        def llm_critical_error(*args, **kwargs):
            raise Exception("语言模型服务完全不可用")
        
        self.mock_llm.chat.side_effect = llm_critical_error
        
        with pytest.raises(Exception):
            self.chat_service.chat_with_text("Test critical error")
    
    def test_progressive_error_disclosure(self):
        """
        测试渐进式错误信息披
        需 4.1, 4.2, 4.3, 4.4
        """
        # 模拟连续失败的场
        failure_count = 0
        
        def progressive_failure(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count == 1:
                raise Exception("临时网络问题")
            elif failure_count == 2:
                raise Exception("服务响应超时")
            else:
                raise Exception("服务长时间不可用,请稍后重试")
        
        self.mock_asr.recognize_gradio_audio.side_effect = progressive_failure
        
        def asr_enhanced_progressive(*args, **kwargs):
            return progressive_failure(*args, **kwargs)
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_progressive
        
        # 多次尝试,观察错误消息的变化
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        error_messages = []
        
        for attempt in range(3):
            result = self.chat_tab._handle_chat(
                audio=gradio_audio,
                text_input="",
                chat_history=[],
                use_text=False
            )
            
            audio_output, chat_history = result
            if len(chat_history) > 0:
                error_messages.append(str(chat_history).lower())
        
        # 验证错误消息随着失败次数增加而提供更多信
        assert len(error_messages) == 3
        
        # 第一次:简单的重试建议
        assert any(keyword in error_messages[0] for keyword in ["网络", "重试"])
        
        # 第二次:更具体的问题描述
        assert any(keyword in error_messages[1] for keyword in ["超时", "服务"])
        
        # 第三次:更详细的解决方案
        assert any(keyword in error_messages[2] for keyword in ["稍后", "长时间"])


class TestErrorRecoveryIntegration:
    """错误恢复集成测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 创建ChatService
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        # 创建ChatTab
        self.temp_dir = tempfile.mkdtemp()
        with patch('chatterpal.utils.preferences.get_preferences_manager') as mock_get_prefs:
            self.preferences = UserPreferences(config_dir=self.temp_dir)
            mock_get_prefs.return_value = self.preferences
            self.chat_tab = ChatTab(self.chat_service)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_graceful_degradation_chain(self):
        """
        测试优雅降级
        需 1.3, 2.3, 3.1, 3.2
        """
        session_id = self.chat_service.create_session()
        
        # 场景1:语音输入失-> 建议文本输入
        def asr_fail(*args, **kwargs):
            raise Exception("语音识别不可用")
        
        self.mock_asr.recognize_gradio_audio.side_effect = asr_fail
        self.mock_asr.recognize_with_error_handling.side_effect = asr_fail
        
        sample_rate = 16000
        audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
        gradio_audio = (sample_rate, audio_array)
        
        result = self.chat_tab._handle_chat(
            audio=gradio_audio,
            text_input="",
            chat_history=[],
            use_text=False
        )
        
        audio_output, chat_history = result
        
        # 应该建议切换到文本输
        error_message = str(chat_history).lower()
        assert any(keyword in error_message for keyword in ["文本", "输入", "切换"])
        
        # 场景2:切换到文本输入,LLM正常工作
        self.mock_llm.chat.return_value = "文本输入工作正常"
        
        result = self.chat_tab._handle_chat(
            text_input="Hello via text",
            audio=None,
            chat_history=[],
            use_text=True
        )
        
        audio_output, chat_history = result
        
        # 文本对话应该成功
        assert "文本输入工作正常" in str(chat_history)
        
        # 场景3:TTS失败,但文本回复仍然显示
        def tts_fail(*args, **kwargs):
            raise Exception("语音合成不可用")
        
        self.mock_tts.synthesize_with_error_handling = tts_fail
        
        result = self.chat_tab._handle_chat(
            text_input="Another text message",
            audio=None,
            chat_history=chat_history,
            use_text=True
        )
        
        audio_output, chat_history = result
        
        # 文本对话仍然成功,只是没有音
        assert "文本输入工作正常" in str(chat_history)
        assert audio_output == (16000, [])
    
    def test_error_state_cleanup(self):
        """
        测试错误状态清
        需 1.3, 2.3, 4.4
        """
        session_id = self.chat_service.create_session()
        
        # 1. 触发错误状
        def temporary_error(*args, **kwargs):
            raise Exception("临时错误")
        
        self.mock_llm.chat.side_effect = temporary_error
        
        # 尝试对话,应该失
        with pytest.raises(Exception):
            self.chat_service.chat_with_text("Test error", session_id)
        
        # 2. 清除错误状
        self.mock_llm.chat.side_effect = None
        self.mock_llm.chat.return_value = "错误已恢复"
        
        # 3. 再次尝试,应该成
        response, _ = self.chat_service.chat_with_text("Test recovery", session_id)
        assert response == "错误已恢复"
        
        # 4. 验证会话状态正
        history = self.chat_service.get_conversation_history(session_id)
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assert len(user_messages) >= 1
        assert user_messages[-1]["content"] == "Test recovery"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])









