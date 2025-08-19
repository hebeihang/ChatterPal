"""
性能和用户体验测试
测试语音识别和合成的响应时间、不同音频质量下的识别准确率
测试并发用户场景下的系统稳定性、验证用户界面的响应性和流畅性
"""

import pytest
import numpy as np
import tempfile
import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
from typing import List, Tuple, Any, Dict
import statistics

from src.oralcounsellor.services.chat import ChatService
from src.oralcounsellor.web.components.chat_tab import ChatTab
from src.oralcounsellor.utils.preferences import UserPreferences


class TestResponseTimePerformance:
    """响应时间性能测试"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建带有可控延迟的模拟组件
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 设置基准响应时间
        self.asr_delay = 0.5  # 500ms
        self.tts_delay = 0.8  # 800ms
        self.llm_delay = 1.0  # 1000ms
        
        # 创建带延迟的模拟方法
        def asr_with_delay(*args, **kwargs):
            time.sleep(self.asr_delay)
            return "Hello, this is a test recognition result"
        
        def tts_with_delay(*args, **kwargs):
            time.sleep(self.tts_delay)
            return b"fake synthesized audio data with realistic timing"
        
        def llm_with_delay(*args, **kwargs):
            time.sleep(self.llm_delay)
            return "This is a test response from the language model"
        
        self.mock_asr.recognize.side_effect = asr_with_delay
        self.mock_asr.recognize_file.side_effect = asr_with_delay
        self.mock_asr.recognize_gradio_audio.side_effect = asr_with_delay
        
        self.mock_tts.synthesize.side_effect = tts_with_delay
        
        self.mock_llm.chat.side_effect = llm_with_delay
        
        # 创建增强的错误处理方法
        from dataclasses import dataclass
        
        @dataclass
        class ASRResult:
            text: str
            confidence: float = 0.9
            processing_time: float = 0.5
            
        def asr_enhanced_with_delay(*args, **kwargs):
            time.sleep(self.asr_delay)
            return ASRResult(
                text="Hello, this is a test recognition result",
                processing_time=self.asr_delay
            )
        
        @dataclass
        class TTSResult:
            audio_data: bytes
            synthesis_time: float = 0.8
            cached: bool = False
            
        def tts_enhanced_with_delay(*args, **kwargs):
            time.sleep(self.tts_delay)
            return TTSResult(
                audio_data=b"fake synthesized audio data",
                synthesis_time=self.tts_delay
            )
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_with_delay
        self.mock_tts.synthesize_with_error_handling = tts_enhanced_with_delay
        
        # 创建ChatService
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        # 创建ChatTab
        self.temp_dir = tempfile.mkdtemp()
        with patch('src.oralcounsellor.utils.preferences.get_preferences_manager') as mock_get_prefs:
            self.preferences = UserPreferences(config_dir=self.temp_dir)
            mock_get_prefs.return_value = self.preferences
            self.chat_tab = ChatTab(self.chat_service)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_sample_audio(self, duration: float = 2.0, quality: str = "high") -> Tuple[int, np.ndarray]:
        """创建不同质量的示例音频"""
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        if quality == "high":
            # 高质量：清晰的正弦波
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.8
        elif quality == "medium":
            # 中等质量：添加轻微噪音
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.6
            noise = np.random.normal(0, 0.05, len(t)).astype(np.float32)
            audio = audio + noise
        elif quality == "low":
            # 低质量：添加较多噪音和失真
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.4
            noise = np.random.normal(0, 0.15, len(t)).astype(np.float32)
            distortion = np.sin(2 * np.pi * 1000 * t).astype(np.float32) * 0.1
            audio = audio + noise + distortion
        else:
            # 默认高质量
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.8
        
        # 限制幅度范围
        audio = np.clip(audio, -1.0, 1.0)
        return sample_rate, audio
    
    def test_asr_response_time_performance(self):
        """
        测试ASR响应时间性能
        需求: 所有需求的性能方面
        """
        # 测试单次ASR响应时间
        sample_rate, audio_array = self._create_sample_audio(duration=2.0)
        gradio_audio = (sample_rate, audio_array)
        
        start_time = time.time()
        response_text, response_audio, session_id = self.chat_service.chat_with_audio(
            audio_data=gradio_audio,
            return_audio=False  # 只测试ASR，不包括TTS
        )
        end_time = time.time()
        
        asr_response_time = end_time - start_time
        
        # ASR响应时间应该在合理范围内（包括LLM处理时间）
        expected_max_time = self.asr_delay + self.llm_delay + 0.5  # 额外0.5秒缓冲
        assert asr_response_time <= expected_max_time, f"ASR响应时间过长: {asr_response_time:.2f}s > {expected_max_time:.2f}s"
        
        # 验证响应质量
        assert response_text == "This is a test response from the language model"
        assert session_id is not None
    
    def test_tts_response_time_performance(self):
        """
        测试TTS响应时间性能
        需求: 所有需求的性能方面
        """
        # 测试不同长度文本的TTS响应时间
        test_texts = [
            "Hello",  # 短文本
            "Hello, how are you today? I hope you're doing well.",  # 中等文本
            "This is a longer text that should take more time to synthesize. It contains multiple sentences and should test the TTS performance under more realistic conditions."  # 长文本
        ]
        
        response_times = []
        
        for text in test_texts:
            start_time = time.time()
            audio_data = self.chat_service._synthesize_with_error_handling(text)
            end_time = time.time()
            
            synthesis_time = end_time - start_time
            response_times.append(synthesis_time)
            
            # 验证音频生成成功
            assert audio_data is not None
            assert isinstance(audio_data, bytes)
            assert len(audio_data) > 0
        
        # 验证响应时间合理性
        for i, response_time in enumerate(response_times):
            expected_max_time = self.tts_delay + 0.3  # 额外300ms缓冲
            assert response_time <= expected_max_time, f"TTS响应时间过长 (文本{i+1}): {response_time:.2f}s > {expected_max_time:.2f}s"
        
        # 验证响应时间与文本长度的关系（可选）
        # 注意：在模拟环境中，所有文本的处理时间相同
        assert all(rt > 0 for rt in response_times), "所有TTS响应时间应该大于0"
    
    def test_end_to_end_response_time(self):
        """
        测试端到端响应时间
        需求: 所有需求的性能方面
        """
        # 测试完整的语音到语音对话流程
        sample_rate, audio_array = self._create_sample_audio(duration=3.0)
        gradio_audio = (sample_rate, audio_array)
        
        start_time = time.time()
        response_text, response_audio, session_id = self.chat_service.chat_with_audio(
            audio_data=gradio_audio,
            return_audio=True
        )
        end_time = time.time()
        
        total_response_time = end_time - start_time
        
        # 端到端响应时间应该是各组件时间之和加上合理缓冲
        expected_max_time = self.asr_delay + self.llm_delay + self.tts_delay + 1.0  # 1秒缓冲
        assert total_response_time <= expected_max_time, f"端到端响应时间过长: {total_response_time:.2f}s > {expected_max_time:.2f}s"
        
        # 验证响应完整性
        assert response_text == "This is a test response from the language model"
        assert response_audio is not None
        assert isinstance(response_audio, bytes)
        assert session_id is not None
        
        print(f"端到端响应时间: {total_response_time:.2f}s")
    
    def test_batch_processing_performance(self):
        """
        测试批量处理性能
        需求: 所有需求的性能方面
        """
        session_id = self.chat_service.create_session()
        
        # 测试连续多次文本对话的性能
        num_requests = 5
        response_times = []
        
        for i in range(num_requests):
            start_time = time.time()
            response, _ = self.chat_service.chat_with_text(
                f"Test message {i+1}",
                session_id=session_id
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # 验证响应正确
            assert response == "This is a test response from the language model"
        
        # 分析性能指标
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # 验证性能指标
        expected_max_single = self.llm_delay + 0.5  # 单次请求最大时间
        assert max_response_time <= expected_max_single, f"单次最大响应时间过长: {max_response_time:.2f}s"
        assert avg_response_time <= expected_max_single, f"平均响应时间过长: {avg_response_time:.2f}s"
        
        print(f"批量处理性能 - 平均: {avg_response_time:.2f}s, 最大: {max_response_time:.2f}s, 最小: {min_response_time:.2f}s")
    
    def test_memory_usage_stability(self):
        """
        测试内存使用稳定性
        需求: 所有需求的性能方面
        """
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        session_id = self.chat_service.create_session()
        
        # 进行多轮对话
        for i in range(10):
            # 文本对话
            self.chat_service.chat_with_text(f"Memory test message {i}", session_id)
            
            # 语音对话
            sample_rate, audio_array = self._create_sample_audio(duration=1.0)
            gradio_audio = (sample_rate, audio_array)
            self.chat_service.chat_with_audio(gradio_audio, session_id)
        
        # 检查内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（考虑到对话历史）
        max_acceptable_increase = 50  # MB
        assert memory_increase <= max_acceptable_increase, f"内存增长过多: {memory_increase:.2f}MB > {max_acceptable_increase}MB"
        
        print(f"内存使用 - 初始: {initial_memory:.2f}MB, 最终: {final_memory:.2f}MB, 增长: {memory_increase:.2f}MB")


class TestAudioQualityAccuracy:
    """音频质量与识别准确率测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 根据音频质量返回不同的识别结果
        def quality_based_recognition(*args, **kwargs):
            # 模拟不同质量下的识别准确率
            audio_data = args[0] if args else None
            
            if isinstance(audio_data, tuple):
                sample_rate, audio_array = audio_data
                # 基于音频信号质量判断
                signal_power = np.mean(np.abs(audio_array))
                noise_level = np.std(audio_array) - np.std(np.sin(2 * np.pi * 440 * np.linspace(0, 2, len(audio_array))))
                
                if signal_power > 0.6 and noise_level < 0.1:
                    # 高质量音频
                    return "Perfect recognition result with high accuracy"
                elif signal_power > 0.4 and noise_level < 0.2:
                    # 中等质量音频
                    return "Good recognition result with some minor errors"
                else:
                    # 低质量音频
                    return "Poor recognition result with multiple errors"
            
            return "Default recognition result"
        
        self.mock_asr.recognize.side_effect = quality_based_recognition
        self.mock_asr.recognize_gradio_audio.side_effect = quality_based_recognition
        
        # 创建增强的ASR方法
        from dataclasses import dataclass
        
        @dataclass
        class ASRResult:
            text: str
            confidence: float
            processing_time: float = 0.5
            
        def asr_enhanced_quality_based(*args, **kwargs):
            result_text = quality_based_recognition(*args, **kwargs)
            
            # 根据识别结果设置置信度
            if "Perfect" in result_text:
                confidence = 0.95
            elif "Good" in result_text:
                confidence = 0.80
            elif "Poor" in result_text:
                confidence = 0.60
            else:
                confidence = 0.75
            
            return ASRResult(text=result_text, confidence=confidence)
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_quality_based
        
        self.mock_tts.synthesize.return_value = b"fake audio data"
        self.mock_llm.chat.return_value = "Quality test response"
        
        # 创建ChatService
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
    
    def _create_sample_audio(self, duration: float = 2.0, quality: str = "high") -> Tuple[int, np.ndarray]:
        """创建不同质量的示例音频"""
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        if quality == "high":
            # 高质量：清晰的正弦波
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.8
        elif quality == "medium":
            # 中等质量：添加轻微噪音
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.6
            noise = np.random.normal(0, 0.05, len(t)).astype(np.float32)
            audio = audio + noise
        elif quality == "low":
            # 低质量：添加较多噪音和失真
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.4
            noise = np.random.normal(0, 0.15, len(t)).astype(np.float32)
            distortion = np.sin(2 * np.pi * 1000 * t).astype(np.float32) * 0.1
            audio = audio + noise + distortion
        else:
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.8
        
        # 限制幅度范围
        audio = np.clip(audio, -1.0, 1.0)
        return sample_rate, audio
    
    def test_high_quality_audio_recognition(self):
        """
        测试高质量音频的识别准确率
        需求: 所有需求的性能方面
        """
        # 创建高质量音频
        sample_rate, audio_array = self._create_sample_audio(quality="high")
        gradio_audio = (sample_rate, audio_array)
        
        # 进行语音识别
        response_text, response_audio, session_id = self.chat_service.chat_with_audio(
            audio_data=gradio_audio,
            return_audio=False
        )
        
        # 验证高质量音频的识别结果
        recognition_result = self.mock_asr.recognize_with_error_handling.return_value
        assert recognition_result.confidence >= 0.9, f"高质量音频置信度应该 >= 0.9，实际: {recognition_result.confidence}"
        assert "Perfect" in recognition_result.text, "高质量音频应该有完美的识别结果"
    
    def test_medium_quality_audio_recognition(self):
        """
        测试中等质量音频的识别准确率
        需求: 所有需求的性能方面
        """
        # 创建中等质量音频
        sample_rate, audio_array = self._create_sample_audio(quality="medium")
        gradio_audio = (sample_rate, audio_array)
        
        # 进行语音识别
        response_text, response_audio, session_id = self.chat_service.chat_with_audio(
            audio_data=gradio_audio,
            return_audio=False
        )
        
        # 验证中等质量音频的识别结果
        recognition_result = self.mock_asr.recognize_with_error_handling.return_value
        assert 0.7 <= recognition_result.confidence < 0.9, f"中等质量音频置信度应该在0.7-0.9之间，实际: {recognition_result.confidence}"
        assert "Good" in recognition_result.text, "中等质量音频应该有良好的识别结果"
    
    def test_low_quality_audio_recognition(self):
        """
        测试低质量音频的识别准确率
        需求: 所有需求的性能方面
        """
        # 创建低质量音频
        sample_rate, audio_array = self._create_sample_audio(quality="low")
        gradio_audio = (sample_rate, audio_array)
        
        # 进行语音识别
        response_text, response_audio, session_id = self.chat_service.chat_with_audio(
            audio_data=gradio_audio,
            return_audio=False
        )
        
        # 验证低质量音频的识别结果
        recognition_result = self.mock_asr.recognize_with_error_handling.return_value
        assert recognition_result.confidence < 0.7, f"低质量音频置信度应该 < 0.7，实际: {recognition_result.confidence}"
        assert "Poor" in recognition_result.text, "低质量音频应该有较差的识别结果"
    
    def test_audio_quality_degradation_handling(self):
        """
        测试音频质量降级处理
        需求: 4.1, 4.2, 4.3, 4.4
        """
        qualities = ["high", "medium", "low"]
        results = []
        
        for quality in qualities:
            sample_rate, audio_array = self._create_sample_audio(quality=quality)
            gradio_audio = (sample_rate, audio_array)
            
            # 进行语音识别
            response_text, response_audio, session_id = self.chat_service.chat_with_audio(
                audio_data=gradio_audio,
                return_audio=False
            )
            
            recognition_result = self.mock_asr.recognize_with_error_handling.return_value
            results.append({
                "quality": quality,
                "confidence": recognition_result.confidence,
                "text": recognition_result.text
            })
        
        # 验证质量降级趋势
        high_confidence = results[0]["confidence"]
        medium_confidence = results[1]["confidence"]
        low_confidence = results[2]["confidence"]
        
        assert high_confidence > medium_confidence > low_confidence, "置信度应该随音频质量降低而下降"
        
        # 验证系统对低质量音频的处理
        low_quality_result = results[2]
        if low_quality_result["confidence"] < 0.5:
            # 低置信度时，系统应该有相应的处理机制
            assert "Poor" in low_quality_result["text"], "低质量音频应该被正确识别为质量较差"
    
    def test_different_audio_durations(self):
        """
        测试不同音频时长的处理性能
        需求: 4.1, 4.2
        """
        durations = [0.5, 1.0, 2.0, 5.0]  # 不同时长（秒）
        processing_times = []
        
        for duration in durations:
            sample_rate, audio_array = self._create_sample_audio(duration=duration, quality="high")
            gradio_audio = (sample_rate, audio_array)
            
            start_time = time.time()
            response_text, response_audio, session_id = self.chat_service.chat_with_audio(
                audio_data=gradio_audio,
                return_audio=False
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            # 验证处理成功
            assert response_text == "Quality test response"
        
        # 验证处理时间合理性
        for i, (duration, proc_time) in enumerate(zip(durations, processing_times)):
            # 处理时间不应该与音频时长成正比增长太快
            max_expected_time = 3.0  # 最大3秒处理时间
            assert proc_time <= max_expected_time, f"音频时长{duration}s的处理时间过长: {proc_time:.2f}s"
        
        print(f"不同时长音频处理时间: {list(zip(durations, [f'{t:.2f}s' for t in processing_times]))}")


class TestConcurrentUserScenarios:
    """并发用户场景测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 添加轻微延迟以模拟真实场景
        def asr_with_delay(*args, **kwargs):
            time.sleep(0.1)
            return "Concurrent user recognition result"
        
        def tts_with_delay(*args, **kwargs):
            time.sleep(0.2)
            return b"concurrent audio data"
        
        def llm_with_delay(*args, **kwargs):
            time.sleep(0.3)
            return f"Response for concurrent user at {time.time()}"
        
        self.mock_asr.recognize.side_effect = asr_with_delay
        self.mock_asr.recognize_gradio_audio.side_effect = asr_with_delay
        self.mock_tts.synthesize.side_effect = tts_with_delay
        self.mock_llm.chat.side_effect = llm_with_delay
        
        # 创建增强方法
        from dataclasses import dataclass
        
        @dataclass
        class ASRResult:
            text: str
            confidence: float = 0.9
            
        @dataclass
        class TTSResult:
            audio_data: bytes
            synthesis_time: float = 0.2
            
        def asr_enhanced_concurrent(*args, **kwargs):
            time.sleep(0.1)
            return ASRResult(text="Concurrent user recognition result")
        
        def tts_enhanced_concurrent(*args, **kwargs):
            time.sleep(0.2)
            return TTSResult(audio_data=b"concurrent audio data")
        
        self.mock_asr.recognize_with_error_handling = asr_enhanced_concurrent
        self.mock_tts.synthesize_with_error_handling = tts_enhanced_concurrent
        
        # 创建ChatService
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
    
    def test_concurrent_text_conversations(self):
        """
        测试并发文本对话
        需求: 所有需求的性能方面
        """
        num_concurrent_users = 5
        messages_per_user = 3
        
        results = []
        errors = []
        
        def user_conversation(user_id):
            try:
                session_id = self.chat_service.create_session()
                user_results = []
                
                for i in range(messages_per_user):
                    start_time = time.time()
                    response, _ = self.chat_service.chat_with_text(
                        f"User {user_id} message {i+1}",
                        session_id=session_id
                    )
                    end_time = time.time()
                    
                    user_results.append({
                        "user_id": user_id,
                        "message_id": i+1,
                        "response_time": end_time - start_time,
                        "response": response
                    })
                
                results.extend(user_results)
                
            except Exception as e:
                errors.append((user_id, str(e)))
        
        # 启动并发用户
        threads = []
        for user_id in range(num_concurrent_users):
            thread = threading.Thread(target=user_conversation, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)
        
        # 验证结果
        expected_total_messages = num_concurrent_users * messages_per_user
        assert len(results) == expected_total_messages, f"应该有{expected_total_messages}条消息，实际: {len(results)}"
        assert len(errors) == 0, f"不应该有错误，实际错误: {errors}"
        
        # 分析性能
        response_times = [r["response_time"] for r in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # 并发情况下响应时间应该仍然合理
        assert max_response_time <= 2.0, f"并发情况下最大响应时间过长: {max_response_time:.2f}s"
        assert avg_response_time <= 1.0, f"并发情况下平均响应时间过长: {avg_response_time:.2f}s"
        
        print(f"并发文本对话性能 - 用户数: {num_concurrent_users}, 平均响应时间: {avg_response_time:.2f}s, 最大响应时间: {max_response_time:.2f}s")
    
    def test_concurrent_voice_conversations(self):
        """
        测试并发语音对话
        需求: 所有需求的性能方面
        """
        num_concurrent_users = 3  # 语音处理更耗资源，减少并发数
        
        results = []
        errors = []
        
        def user_voice_conversation(user_id):
            try:
                session_id = self.chat_service.create_session()
                
                # 创建音频数据
                sample_rate = 16000
                duration = 1.0
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_array = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5
                gradio_audio = (sample_rate, audio_array)
                
                start_time = time.time()
                response_text, response_audio, _ = self.chat_service.chat_with_audio(
                    audio_data=gradio_audio,
                    session_id=session_id,
                    return_audio=True
                )
                end_time = time.time()
                
                results.append({
                    "user_id": user_id,
                    "response_time": end_time - start_time,
                    "response_text": response_text,
                    "has_audio": response_audio is not None
                })
                
            except Exception as e:
                errors.append((user_id, str(e)))
        
        # 启动并发语音用户
        threads = []
        for user_id in range(num_concurrent_users):
            thread = threading.Thread(target=user_voice_conversation, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=60)  # 语音处理需要更多时间
        
        # 验证结果
        assert len(results) == num_concurrent_users, f"应该有{num_concurrent_users}个结果，实际: {len(results)}"
        assert len(errors) == 0, f"不应该有错误，实际错误: {errors}"
        
        # 验证所有用户都得到了完整响应
        for result in results:
            assert result["response_text"] is not None, f"用户{result['user_id']}没有得到文本响应"
            assert result["has_audio"], f"用户{result['user_id']}没有得到音频响应"
        
        # 分析性能
        response_times = [r["response_time"] for r in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # 并发语音处理的响应时间限制
        assert max_response_time <= 5.0, f"并发语音处理最大响应时间过长: {max_response_time:.2f}s"
        assert avg_response_time <= 3.0, f"并发语音处理平均响应时间过长: {avg_response_time:.2f}s"
        
        print(f"并发语音对话性能 - 用户数: {num_concurrent_users}, 平均响应时间: {avg_response_time:.2f}s, 最大响应时间: {max_response_time:.2f}s")
    
    def test_mixed_concurrent_operations(self):
        """
        测试混合并发操作（文本+语音）
        需求: 所有需求的性能方面
        """
        num_text_users = 3
        num_voice_users = 2
        
        results = []
        errors = []
        
        def text_user(user_id):
            try:
                session_id = self.chat_service.create_session()
                start_time = time.time()
                response, _ = self.chat_service.chat_with_text(
                    f"Text user {user_id} message",
                    session_id=session_id
                )
                end_time = time.time()
                
                results.append({
                    "type": "text",
                    "user_id": user_id,
                    "response_time": end_time - start_time,
                    "success": True
                })
                
            except Exception as e:
                errors.append(("text", user_id, str(e)))
        
        def voice_user(user_id):
            try:
                session_id = self.chat_service.create_session()
                
                # 创建音频数据
                sample_rate = 16000
                duration = 1.0
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_array = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5
                gradio_audio = (sample_rate, audio_array)
                
                start_time = time.time()
                response_text, response_audio, _ = self.chat_service.chat_with_audio(
                    audio_data=gradio_audio,
                    session_id=session_id
                )
                end_time = time.time()
                
                results.append({
                    "type": "voice",
                    "user_id": user_id,
                    "response_time": end_time - start_time,
                    "success": True
                })
                
            except Exception as e:
                errors.append(("voice", user_id, str(e)))
        
        # 启动混合并发操作
        threads = []
        
        # 启动文本用户
        for user_id in range(num_text_users):
            thread = threading.Thread(target=text_user, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # 启动语音用户
        for user_id in range(num_voice_users):
            thread = threading.Thread(target=voice_user, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=60)
        
        # 验证结果
        expected_total = num_text_users + num_voice_users
        assert len(results) == expected_total, f"应该有{expected_total}个结果，实际: {len(results)}"
        assert len(errors) == 0, f"不应该有错误，实际错误: {errors}"
        
        # 分析不同类型操作的性能
        text_results = [r for r in results if r["type"] == "text"]
        voice_results = [r for r in results if r["type"] == "voice"]
        
        text_avg_time = statistics.mean([r["response_time"] for r in text_results])
        voice_avg_time = statistics.mean([r["response_time"] for r in voice_results])
        
        # 验证性能合理性
        assert text_avg_time <= 1.0, f"混合并发下文本操作平均时间过长: {text_avg_time:.2f}s"
        assert voice_avg_time <= 3.0, f"混合并发下语音操作平均时间过长: {voice_avg_time:.2f}s"
        
        print(f"混合并发性能 - 文本平均: {text_avg_time:.2f}s, 语音平均: {voice_avg_time:.2f}s")
    
    def test_session_isolation_under_load(self):
        """
        测试高负载下的会话隔离
        需求: 所有需求的性能方面
        """
        num_users = 5
        messages_per_user = 3
        
        session_data = {}
        errors = []
        
        def isolated_user_conversation(user_id):
            try:
                session_id = self.chat_service.create_session()
                session_data[user_id] = {"session_id": session_id, "messages": []}
                
                for i in range(messages_per_user):
                    message = f"User {user_id} unique message {i+1}"
                    response, _ = self.chat_service.chat_with_text(message, session_id)
                    
                    session_data[user_id]["messages"].append({
                        "user_message": message,
                        "assistant_response": response
                    })
                
            except Exception as e:
                errors.append((user_id, str(e)))
        
        # 启动并发用户
        threads = []
        for user_id in range(num_users):
            thread = threading.Thread(target=isolated_user_conversation, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)
        
        # 验证会话隔离
        assert len(errors) == 0, f"不应该有错误，实际错误: {errors}"
        assert len(session_data) == num_users, f"应该有{num_users}个会话，实际: {len(session_data)}"
        
        # 验证每个会话都有独立的数据
        session_ids = set()
        for user_id, data in session_data.items():
            session_id = data["session_id"]
            assert session_id not in session_ids, f"会话ID重复: {session_id}"
            session_ids.add(session_id)
            
            # 验证消息数量
            assert len(data["messages"]) == messages_per_user, f"用户{user_id}消息数量不正确"
            
            # 验证消息内容包含用户ID（确保没有串话）
            for msg in data["messages"]:
                assert f"User {user_id}" in msg["user_message"], f"用户{user_id}的消息内容错误"
        
        print(f"会话隔离测试通过 - {num_users}个并发用户，{len(session_ids)}个独立会话")


class TestUIResponsivenessAndFluidity:
    """用户界面响应性和流畅性测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_asr = Mock()
        self.mock_tts = Mock()
        self.mock_llm = Mock()
        
        # 设置快速响应以测试UI
        self.mock_asr.recognize.return_value = "UI test recognition"
        self.mock_asr.recognize_gradio_audio.return_value = "UI test recognition"
        self.mock_tts.synthesize.return_value = b"UI test audio"
        self.mock_llm.chat.return_value = "UI test response"
        
        # 创建增强方法
        from dataclasses import dataclass
        
        @dataclass
        class ASRResult:
            text: str
            confidence: float = 0.9
            
        @dataclass
        class TTSResult:
            audio_data: bytes
            synthesis_time: float = 0.1
            
        self.mock_asr.recognize_with_error_handling = lambda *args, **kwargs: ASRResult(text="UI test recognition")
        self.mock_tts.synthesize_with_error_handling = lambda *args, **kwargs: TTSResult(audio_data=b"UI test audio")
        
        # 创建ChatService和ChatTab
        self.chat_service = ChatService(
            asr=self.mock_asr,
            tts=self.mock_tts,
            llm=self.mock_llm
        )
        
        self.temp_dir = tempfile.mkdtemp()
        with patch('src.oralcounsellor.utils.preferences.get_preferences_manager') as mock_get_prefs:
            self.preferences = UserPreferences(config_dir=self.temp_dir)
            mock_get_prefs.return_value = self.preferences
            self.chat_tab = ChatTab(self.chat_service)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_input_mode_switching_responsiveness(self):
        """
        测试输入模式切换的响应性
        需求: 3.1, 3.2, 3.3
        """
        # 测试多次快速切换
        switch_times = []
        
        current_mode = True  # 开始为文本模式
        
        for i in range(10):
            start_time = time.time()
            result = self.chat_tab._toggle_input_mode(current_mode)
            end_time = time.time()
            
            switch_time = end_time - start_time
            switch_times.append(switch_time)
            
            # 验证切换结果
            new_use_text, audio_update, text_update, status_update, button_update = result
            assert new_use_text != current_mode, "输入模式应该被切换"
            
            current_mode = new_use_text
        
        # 验证切换响应时间
        avg_switch_time = statistics.mean(switch_times)
        max_switch_time = max(switch_times)
        
        assert max_switch_time <= 0.1, f"输入模式切换时间过长: {max_switch_time:.3f}s"
        assert avg_switch_time <= 0.05, f"平均切换时间过长: {avg_switch_time:.3f}s"
        
        print(f"输入模式切换性能 - 平均: {avg_switch_time:.3f}s, 最大: {max_switch_time:.3f}s")
    
    def test_chat_interaction_responsiveness(self):
        """
        测试聊天交互的响应性
        需求: 1.1, 1.2, 2.1, 2.2
        """
        # 测试文本输入响应时间
        text_response_times = []
        
        for i in range(5):
            start_time = time.time()
            result = self.chat_tab._handle_chat(
                audio=None,
                text_input=f"Test message {i+1}",
                chat_history=[],
                use_text=True
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            text_response_times.append(response_time)
            
            # 验证响应格式
            audio_output, chat_history = result
            assert isinstance(audio_output, tuple), "音频输出应该是元组格式"
            assert isinstance(chat_history, list), "聊天历史应该是列表格式"
        
        # 测试语音输入响应时间
        voice_response_times = []
        
        for i in range(3):  # 语音处理较慢，测试次数少一些
            sample_rate = 16000
            duration = 1.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_array = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5
            gradio_audio = (sample_rate, audio_array)
            
            start_time = time.time()
            result = self.chat_tab._handle_chat(
                audio=gradio_audio,
                text_input="",
                chat_history=[],
                use_text=False
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            voice_response_times.append(response_time)
            
            # 验证响应格式
            audio_output, chat_history = result
            assert isinstance(audio_output, tuple), "音频输出应该是元组格式"
            assert isinstance(chat_history, list), "聊天历史应该是列表格式"
        
        # 分析响应时间
        avg_text_time = statistics.mean(text_response_times)
        avg_voice_time = statistics.mean(voice_response_times)
        
        # UI响应时间要求
        assert avg_text_time <= 1.0, f"文本交互平均响应时间过长: {avg_text_time:.2f}s"
        assert avg_voice_time <= 2.0, f"语音交互平均响应时间过长: {avg_voice_time:.2f}s"
        
        print(f"聊天交互响应性 - 文本平均: {avg_text_time:.2f}s, 语音平均: {avg_voice_time:.2f}s")
    
    def test_preference_persistence_performance(self):
        """
        测试偏好设置持久化性能
        需求: 3.3, 5.4
        """
        # 测试偏好设置保存时间
        save_times = []
        
        preferences_to_test = [
            ("input_mode", ["text", "voice"]),
            ("show_history", [True, False]),
            ("auto_play_response", [True, False])
        ]
        
        for pref_name, values in preferences_to_test:
            for value in values:
                start_time = time.time()
                
                if pref_name == "input_mode":
                    self.preferences.set_input_mode(value)
                elif pref_name == "show_history":
                    self.preferences.set_show_history(value)
                elif pref_name == "auto_play_response":
                    self.preferences.set_auto_play_response(value)
                
                end_time = time.time()
                save_time = end_time - start_time
                save_times.append(save_time)
        
        # 验证保存性能
        avg_save_time = statistics.mean(save_times)
        max_save_time = max(save_times)
        
        assert max_save_time <= 0.1, f"偏好设置保存时间过长: {max_save_time:.3f}s"
        assert avg_save_time <= 0.05, f"平均保存时间过长: {avg_save_time:.3f}s"
        
        # 测试读取性能
        load_times = []
        
        for _ in range(10):
            start_time = time.time()
            
            # 读取所有偏好设置
            input_mode = self.preferences.get_input_mode()
            show_history = self.preferences.get_show_history()
            auto_play = self.preferences.get_auto_play_response()
            
            end_time = time.time()
            load_time = end_time - start_time
            load_times.append(load_time)
        
        avg_load_time = statistics.mean(load_times)
        max_load_time = max(load_times)
        
        assert max_load_time <= 0.05, f"偏好设置读取时间过长: {max_load_time:.3f}s"
        assert avg_load_time <= 0.02, f"平均读取时间过长: {avg_load_time:.3f}s"
        
        print(f"偏好设置性能 - 保存平均: {avg_save_time:.3f}s, 读取平均: {avg_load_time:.3f}s")
    
    def test_error_handling_ui_responsiveness(self):
        """
        测试错误处理的UI响应性
        需求: 1.3, 2.3, 4.1, 4.2, 4.3, 4.4
        """
        # 模拟各种错误场景
        error_scenarios = [
            ("ASR错误", lambda: setattr(self.mock_asr, 'recognize_gradio_audio', Mock(side_effect=Exception("ASR失败")))),
            ("TTS错误", lambda: setattr(self.mock_tts, 'synthesize_with_error_handling', Mock(side_effect=Exception("TTS失败")))),
            ("LLM错误", lambda: setattr(self.mock_llm, 'chat', Mock(side_effect=Exception("LLM失败"))))
        ]
        
        error_response_times = []
        
        for error_name, setup_error in error_scenarios:
            # 设置错误条件
            setup_error()
            
            start_time = time.time()
            
            if "ASR" in error_name:
                # 测试语音输入错误
                sample_rate = 16000
                audio_array = np.random.random(sample_rate).astype(np.float32) * 0.5
                gradio_audio = (sample_rate, audio_array)
                
                result = self.chat_tab._handle_chat(
                    audio=gradio_audio,
                    text_input="",
                    chat_history=[],
                    use_text=False
                )
            else:
                # 测试文本输入错误
                result = self.chat_tab._handle_chat(
                    audio=None,
                    text_input="Test error handling",
                    chat_history=[],
                    use_text=True
                )
            
            end_time = time.time()
            error_response_time = end_time - start_time
            error_response_times.append((error_name, error_response_time))
            
            # 验证错误处理结果
            audio_output, chat_history = result
            assert isinstance(audio_output, tuple), "错误情况下仍应返回正确格式"
            assert isinstance(chat_history, list), "错误情况下仍应返回聊天历史"
            
            # 重置模拟组件
            self.mock_asr.recognize_gradio_audio = Mock(return_value="UI test recognition")
            self.mock_tts.synthesize_with_error_handling = lambda *args, **kwargs: Mock(audio_data=b"UI test audio")
            self.mock_llm.chat = Mock(return_value="UI test response")
        
        # 验证错误处理响应时间
        for error_name, response_time in error_response_times:
            assert response_time <= 2.0, f"{error_name}处理时间过长: {response_time:.2f}s"
        
        avg_error_time = statistics.mean([t for _, t in error_response_times])
        assert avg_error_time <= 1.0, f"平均错误处理时间过长: {avg_error_time:.2f}s"
        
        print(f"错误处理响应性: {[(name, f'{time:.2f}s') for name, time in error_response_times]}")
    
    def test_ui_state_consistency_under_load(self):
        """
        测试高负载下的UI状态一致性
        需求: 所有需求的性能方面
        """
        # 模拟快速连续的UI操作
        operations = []
        
        def rapid_operations():
            for i in range(20):
                # 快速切换输入模式
                current_mode = i % 2 == 0
                self.chat_tab._toggle_input_mode(current_mode)
                
                # 快速切换历史显示
                show_history = i % 3 == 0
                self.chat_tab._toggle_history_display(show_history)
                
                # 快速进行聊天
                if i % 2 == 0:
                    result = self.chat_tab._handle_chat(
                        audio=None,
                        text_input=f"Rapid message {i}",
                        chat_history=[],
                        use_text=True
                    )
                
                operations.append(i)
        
        # 执行快速操作
        start_time = time.time()
        rapid_operations()
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # 验证操作完成
        assert len(operations) == 20, "所有操作应该完成"
        
        # 验证最终状态一致性
        final_input_mode = self.preferences.get_input_mode()
        final_show_history = self.preferences.get_show_history()
        
        assert final_input_mode in ["text", "voice"], "最终输入模式应该有效"
        assert isinstance(final_show_history, bool), "最终历史显示设置应该是布尔值"
        
        # 验证总体性能
        avg_operation_time = total_time / len(operations)
        assert avg_operation_time <= 0.1, f"平均操作时间过长: {avg_operation_time:.3f}s"
        
        print(f"UI状态一致性测试 - 总时间: {total_time:.2f}s, 平均操作时间: {avg_operation_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])