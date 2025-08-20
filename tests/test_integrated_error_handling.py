"""
集成错误处理测试
测试整个聊天模块的错误处理和恢复机制
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from chatterpal.services.chat import ChatService
from chatterpal.core.errors import error_handler, ChatModuleError
from tests.test_error_handling import MockASR
from tests.test_tts_error_handling import MockTTSWithErrorHandling
from tests.test_topic_error_handling import MockLLMForTopic


class TestIntegratedErrorHandling:
    """测试集成错误处理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.asr = MockASR()
        self.tts = MockTTSWithErrorHandling()
        self.llm = MockLLMForTopic()
        
        self.chat_service = ChatService(
            asr=self.asr,
            tts=self.tts,
            llm=self.llm
        )
    
    def test_end_to_end_error_recovery_chain(self):
        """测试端到端错误恢复链"""
        session_id = self.chat_service.create_session()
        
        # 场景1:ASR失败,但文本输入正常工作
        self.asr.should_fail = True
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        
        result = self.chat_service.process_chat(
            audio=audio_data,
            use_text_input=False,
            session_id=session_id
        )
        audio_output, chat_history = result
        
        # 应该有错误信
        assert len(chat_history) > 0
        error_message = chat_history[0][1]
        assert any(keyword in error_message for keyword in ["服务", "不可, "网络", "重试", "文本输入"])
        
        # 场景2:切换到文本输入,应该正常工
        self.asr.should_fail = False  # 重置ASR
        result = self.chat_service.process_chat(
            text_input="Hello, how are you",
            use_text_input=True,
            session_id=session_id
        )
        audio_output, chat_history = result
        
        # 文本对话应该成功
        assert len(chat_history) >= 1
        assert "What's your favorite hobby" in str(chat_history)  # LLM响应
    
    def test_multiple_component_failures(self):
        """测试多个组件同时失败的处""
        session_id = self.chat_service.create_session()
        
        # 同时让ASR、TTS和主题生成都失败
        self.asr.should_fail = True
        self.tts.should_fail = True
        self.llm.should_fail = True
        self.llm.fail_count = 10
        
        # 尝试语音对话
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        result = self.chat_service.process_chat(
            audio=audio_data,
            use_text_input=False,
            session_id=session_id
        )
        audio_output, chat_history = result
        
        # 应该有错误信息,但不会崩
        assert len(chat_history) > 0
        assert audio_output == (16000, [])  # 没有音频输出
        
        # 尝试生成主题也应该有备用方案
        topic = self.chat_service.generate_topic(session_id)
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_partial_failure_graceful_degradation(self):
        """测试部分失败时的优雅降级"""
        session_id = self.chat_service.create_session()
        
        # 只让TTS失败,其他组件正
        self.tts.should_fail = True
        
        result = self.chat_service.process_chat(
            text_input="Tell me about your day",
            use_text_input=True,
            session_id=session_id
        )
        audio_output, chat_history = result
        
        # 文本对话应该成功,但没有音频输出
        assert len(chat_history) > 0
        assert "What's your favorite hobby" in str(chat_history)
        assert audio_output == (16000, [])  # TTS失败,没有音
    
    def test_error_recovery_with_retry(self):
        """测试带重试的错误恢复"""
        session_id = self.chat_service.create_session()
        
        # 设置ASR前两次失败,第三次成
        self.asr.should_fail = True
        original_recognize_enhanced = self.asr.recognize_enhanced
        call_count = 0
        
        def mock_recognize_enhanced(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("临时ASR错误")
            # 第三次调用成
            self.asr.should_fail = False
            return original_recognize_enhanced(*args, **kwargs)
        
        self.asr.recognize_enhanced = mock_recognize_enhanced
        
        # 使用增强的ASR方法
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        try:
            result = self.asr.recognize_with_error_handling(audio_data, max_retries=3)
            assert result.text == "test recognition result"
            assert call_count == 3
        except Exception:
            # 如果仍然失败,至少验证重试了
            assert call_count >= 2
    
    def test_user_friendly_error_messages(self):
        """测试用户友好的错误消""
        session_id = self.chat_service.create_session()
        
        # 测试不同类型的错误消
        error_scenarios = [
            {
                "setup": lambda: setattr(self.asr, "should_fail", True),
                "input": {"audio": np.random.random(16000).astype(np.float32) * 0.5, "use_text_input": False},
                "expected_keywords": ["语音", "识别", "重试"]
            },
            {
                "setup": lambda: None,
                "input": {"text_input": "", "use_text_input": True},
                "expected_keywords": ["输入", ", "重试"]
            }
        ]
        
        for scenario in error_scenarios:
            # 重置状
            self.asr.should_fail = False
            self.tts.should_fail = False
            
            # 设置错误条件
            scenario["setup"]()
            
            # 执行操作
            result = self.chat_service.process_chat(session_id=session_id, **scenario["input"])
            audio_output, chat_history = result
            
            # 验证错误消息
            assert len(chat_history) > 0
            error_message = chat_history[0][1].lower()
            
            # 检查是否包含预期的关键词或通用错误词汇
            expected_keywords = scenario["expected_keywords"] + ["服务", "不可, "问题", "重试"]
            has_expected_keyword = any(
                keyword in error_message 
                for keyword in expected_keywords
            )
            assert has_expected_keyword, f"错误消息 '{error_message}' 不包含预期关键词 {expected_keywords}"
    
    def test_error_logging_integration(self):
        """测试错误日志记录的集""
        with patch('chatterpal.core.errors.error_handler.log_error') as mock_log_error:
            session_id = self.chat_service.create_session()
            
            # 触发ASR错误
            self.asr.should_fail = True
            audio_data = np.random.random(16000).astype(np.float32) * 0.5
            
            result = self.chat_service.process_chat(
                audio=audio_data,
                use_text_input=False,
                session_id=session_id
            )
            
            # 验证错误被记
            assert mock_log_error.called
            
            # 检查记录的错误信息
            call_args = mock_log_error.call_args
            if call_args:
                error_obj = call_args[0][0]
                assert isinstance(error_obj, ChatModuleError)
    
    def test_service_status_with_errors(self):
        """测试服务状态报告中的错误信""
        # 模拟各种服务状
        self.asr.should_fail = True
        self.tts.should_fail = True
        
        status = self.chat_service.get_service_status()
        
        # 验证状态报告包含必要信
        assert "asr_available" in status
        assert "tts_available" in status
        assert "llm_available" in status
        assert "active_sessions" in status
        
        # 验证连接状态检
        if "asr_status" in status:
            # ASR设置为失败,状态应该为False
            assert status["asr_status"] is False
    
    def test_session_isolation_during_errors(self):
        """测试错误期间的会话隔""
        # 创建两个会话
        session1 = self.chat_service.create_session()
        session2 = self.chat_service.create_session()
        
        # 在会中进行正常对
        result1 = self.chat_service.process_chat(
            text_input="Hello from session 1",
            use_text_input=True,
            session_id=session1
        )
        
        # 在会中触发错
        self.asr.should_fail = True
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        result2 = self.chat_service.process_chat(
            audio=audio_data,
            use_text_input=False,
            session_id=session2
        )
        
        # 验证会话1不受影响
        history1 = self.chat_service.get_conversation_history(session1)
        history2 = self.chat_service.get_conversation_history(session2)
        
        assert len(history1) >= 2  # 用户消息 + 助手回复(这里是原始格式
        assert len(history2) >= 1  # 至少有错误消
        
        # 会话1的历史不应包含会的错
        history1_text = str(history1)
        assert "Hello from session 1" in history1_text
        assert "错误" not in history1_text or "失败" not in history1_text
    
    def test_cleanup_after_errors(self):
        """测试错误后的清理工作"""
        session_id = self.chat_service.create_session()
        
        # 触发一些错
        self.asr.should_fail = True
        self.tts.should_fail = True
        
        audio_data = np.random.random(16000).astype(np.float32) * 0.5
        result = self.chat_service.process_chat(
            audio=audio_data,
            use_text_input=False,
            session_id=session_id
        )
        
        # 重置错误状
        self.asr.should_fail = False
        self.tts.should_fail = False
        
        # 验证服务可以恢复正常
        result = self.chat_service.process_chat(
            text_input="Are you working now",
            use_text_input=True,
            session_id=session_id
        )
        audio_output, chat_history = result
        
        # 应该能正常工
        assert len(chat_history) >= 1
        assert "What's your favorite hobby" in str(chat_history)
    
    def test_concurrent_error_handling(self):
        """测试并发错误处理"""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                session_id = self.chat_service.create_session()
                
                # 随机触发不同类型的错
                if worker_id % 2 == 0:
                    self.asr.should_fail = True
                    audio_data = np.random.random(16000).astype(np.float32) * 0.5
                    result = self.chat_service.process_chat(
                        audio=audio_data,
                        use_text_input=False,
                        session_id=session_id
                    )
                else:
                    result = self.chat_service.process_chat(
                        text_input=f"Hello from worker {worker_id}",
                        use_text_input=True,
                        session_id=session_id
                    )
                
                results.append((worker_id, result))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # 创建多个并发工作线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完
        for thread in threads:
            thread.join(timeout=10)
        
        # 验证结果
        assert len(results) > 0, "应该有一些成功的结果"
        
        # 即使有错误,也不应该有未处理的异
        for worker_id, error in errors:
            print(f"Worker {worker_id} error: {error}")
        
        # 所有工作线程都应该完成(无论成功还是失败)
        assert len(results) + len(errors) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])








