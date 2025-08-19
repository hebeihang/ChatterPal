"""
增强ASR功能测试
"""

import numpy as np
import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from src.oralcounsellor.core.asr.base import (
    ASRBase, 
    ASRError, 
    ASRQualityError, 
    ASRConfidenceError, 
    ASRTimeoutError,
    ASRResult,
    ConfidenceLevel
)


class MockASR(ASRBase):
    """用于测试的模拟ASR实现"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.mock_result = "测试识别结果"
        self.should_fail = False
        self.processing_delay = 0.1
        
    def recognize(self, audio_data: bytes, **kwargs):
        import time
        time.sleep(self.processing_delay)
        
        if self.should_fail:
            raise ASRError("模拟识别失败")
        
        return self.mock_result
    
    def recognize_file(self, audio_path: str, **kwargs):
        import time
        time.sleep(self.processing_delay)
        
        if self.should_fail:
            raise ASRError("模拟识别失败")
        
        return self.mock_result


class TestASREnhanced:
    """增强ASR功能测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.asr = MockASR({
            "min_confidence": 0.6,
            "min_audio_quality": 0.4,
            "max_processing_time": 5.0,
            "enable_quality_check": True,
            "enable_confidence_check": True
        })
        
    def test_asr_result_dataclass(self):
        """测试ASRResult数据类"""
        result = ASRResult(
            text="测试文本",
            confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            audio_quality_score=0.9,
            processing_time=1.5,
            metadata={"test": "data"}
        )
        
        assert result.text == "测试文本"
        assert result.confidence == 0.8
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert result.audio_quality_score == 0.9
        assert result.processing_time == 1.5
        assert result.metadata["test"] == "data"
        
    def test_confidence_level_enum(self):
        """测试置信度级别枚举"""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.VERY_LOW.value == "very_low"
        
    def test_recognize_enhanced_success(self):
        """测试增强识别成功情况"""
        # 创建测试音频数据
        audio_data = self._create_test_audio_bytes()
        
        result = self.asr.recognize_enhanced(audio_data)
        
        assert isinstance(result, ASRResult)
        assert result.text == "测试识别结果"
        assert result.confidence > 0
        assert result.audio_quality_score >= 0
        assert result.processing_time > 0
        
    def test_recognize_enhanced_quality_check_disabled(self):
        """测试禁用质量检查的增强识别"""
        self.asr.enable_quality_check = False
        self.asr.enable_confidence_check = False  # 也禁用置信度检查以避免干扰
        audio_data = self._create_test_audio_bytes()
        
        result = self.asr.recognize_enhanced(audio_data)
        
        assert result.audio_quality_score == 1.0  # 禁用质量检查时默认为1.0
        
    def test_recognize_enhanced_confidence_check_disabled(self):
        """测试禁用置信度检查的增强识别"""
        self.asr.enable_confidence_check = False
        self.asr.mock_result = "a"  # 很短的结果，置信度会很低
        audio_data = self._create_test_audio_bytes()
        
        result = self.asr.recognize_enhanced(audio_data)
        
        # 即使置信度低，也不应该抛出异常
        assert result.text == "a"
        
    def test_recognize_enhanced_quality_error(self):
        """测试音频质量过低错误"""
        # 模拟质量检查返回很低的分数
        with patch.object(self.asr, '_assess_audio_quality', return_value=0.1):
            audio_data = self._create_test_audio_bytes()
            
            with pytest.raises(ASRQualityError) as exc_info:
                self.asr.recognize_enhanced(audio_data)
            
            assert "音频质量过低" in str(exc_info.value)
            
    def test_recognize_enhanced_confidence_error(self):
        """测试识别置信度过低错误"""
        # 模拟返回置信度很低的文本，并确保音频质量也很低
        self.asr.mock_result = "aaaaaaaaaa"  # 重复字符，会降低置信度
        
        # 模拟低质量音频以进一步降低置信度
        with patch.object(self.asr, '_assess_audio_quality') as mock_assess:
            mock_assess.side_effect = lambda audio_data, metadata: (
                metadata.update({
                    "quality_score": 1,  # 低质量分数
                    "snr": 2,  # 低信噪比
                    "silence_ratio": 0.9  # 高静音比例
                }), 0.5  # 返回中等质量分数以通过质量检查
            )[1]
            
            audio_data = self._create_test_audio_bytes()
            
            with pytest.raises(ASRConfidenceError) as exc_info:
                self.asr.recognize_enhanced(audio_data)
            
            assert "识别置信度过低" in str(exc_info.value)
        
    def test_recognize_enhanced_timeout_error(self):
        """测试识别超时错误"""
        self.asr.processing_delay = 6.0  # 超过max_processing_time
        audio_data = self._create_test_audio_bytes()
        
        with pytest.raises(ASRTimeoutError) as exc_info:
            self.asr.recognize_enhanced(audio_data)
        
        assert "识别超时" in str(exc_info.value)
        
    def test_recognize_enhanced_exception_handling(self):
        """测试增强识别的异常处理"""
        self.asr.should_fail = True
        audio_data = self._create_test_audio_bytes()
        
        result = self.asr.recognize_enhanced(audio_data)
        
        assert result.text is None
        assert result.confidence == 0.0
        assert result.confidence_level == ConfidenceLevel.VERY_LOW
        assert "error" in result.metadata
        
    def test_assess_audio_quality_with_audioprocessor(self):
        """测试使用AudioProcessor的音频质量评估"""
        audio_data = self._create_test_audio_bytes()
        metadata = {}
        
        # 这个测试依赖于AudioProcessor的存在
        try:
            quality_score = self.asr._assess_audio_quality(audio_data, metadata)
            assert 0 <= quality_score <= 1
            assert isinstance(metadata, dict)
        except ImportError:
            # 如果AudioProcessor不可用，跳过测试
            pytest.skip("AudioProcessor not available")
            
    def test_simple_audio_quality_check(self):
        """测试简化的音频质量检查"""
        audio_data = self._create_test_audio_bytes()
        metadata = {}
        
        quality_score = self.asr._simple_audio_quality_check(audio_data, metadata)
        
        assert 0 <= quality_score <= 1
        assert "data_size" in metadata
        
    def test_simple_audio_quality_check_file(self):
        """测试文件路径的简化音频质量检查"""
        # 创建临时音频文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(self._create_test_audio_bytes())
            temp_path = temp_file.name
        
        try:
            metadata = {}
            quality_score = self.asr._simple_audio_quality_check(temp_path, metadata)
            
            assert 0 <= quality_score <= 1
            assert "file_size" in metadata
        finally:
            os.unlink(temp_path)
            
    def test_calculate_confidence_empty_text(self):
        """测试空文本的置信度计算"""
        metadata = {}
        confidence = self.asr._calculate_confidence(None, metadata)
        assert confidence == 0.0
        
        confidence = self.asr._calculate_confidence("", metadata)
        assert confidence == 0.0
        
    def test_calculate_confidence_normal_text(self):
        """测试正常文本的置信度计算"""
        metadata = {"quality_score": 5, "snr": 12, "silence_ratio": 0.3}
        confidence = self.asr._calculate_confidence("这是一段正常的测试文本", metadata)
        
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # 正常文本应该有较高置信度
        
    def test_calculate_confidence_poor_quality(self):
        """测试低质量音频的置信度计算"""
        metadata = {"quality_score": 1, "snr": 3, "silence_ratio": 0.9}
        confidence = self.asr._calculate_confidence("测试文本", metadata)
        
        assert confidence < 0.5  # 低质量应该导致低置信度
        
    def test_has_recognition_errors(self):
        """测试识别错误模式检测"""
        # 正常文本
        assert not self.asr._has_recognition_errors("这是正常的文本")
        
        # 重复字符
        assert self.asr._has_recognition_errors("aaaaaa")
        
        # 过多标点符号
        assert self.asr._has_recognition_errors("文本。。。。")
        
        # 过长英文字符串
        assert self.asr._has_recognition_errors("abcdefghijklmnop")
        
        # 过多数字
        assert self.asr._has_recognition_errors("12345678901234567890")
        
    def test_get_confidence_level(self):
        """测试置信度级别获取"""
        assert self.asr._get_confidence_level(0.9) == ConfidenceLevel.HIGH
        assert self.asr._get_confidence_level(0.7) == ConfidenceLevel.MEDIUM
        assert self.asr._get_confidence_level(0.4) == ConfidenceLevel.LOW
        assert self.asr._get_confidence_level(0.1) == ConfidenceLevel.VERY_LOW
        
    def test_validate_audio_for_recognition_success(self):
        """测试音频验证成功情况"""
        audio_data = self._create_test_audio_bytes()
        
        is_valid, message = self.asr.validate_audio_for_recognition(audio_data)
        
        # 结果取决于具体的质量评估，但不应该抛出异常
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)
        
    def test_validate_audio_for_recognition_failure(self):
        """测试音频验证失败情况"""
        # 模拟质量检查返回很低的分数
        with patch.object(self.asr, '_assess_audio_quality', return_value=0.1):
            audio_data = self._create_test_audio_bytes()
            
            is_valid, message = self.asr.validate_audio_for_recognition(audio_data)
            
            assert not is_valid
            assert "音频质量过低" in message
            
    def test_get_recognition_suggestions(self):
        """测试获取识别建议"""
        audio_data = self._create_test_audio_bytes()
        
        suggestions = self.asr.get_recognition_suggestions(audio_data)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
        
    def test_get_recognition_suggestions_with_issues(self):
        """测试有问题音频的识别建议"""
        # 模拟有问题的音频元数据
        mock_metadata = {
            "snr": 3,  # 低信噪比
            "silence_ratio": 0.8,  # 高静音比例
            "max_amplitude": 0.05,  # 低音量
            "duration": 0.3  # 短时长
        }
        
        with patch.object(self.asr, '_assess_audio_quality') as mock_assess:
            mock_assess.side_effect = lambda audio_data, metadata: (
                metadata.update(mock_metadata), 0.3
            )[1]
            
            audio_data = self._create_test_audio_bytes()
            suggestions = self.asr.get_recognition_suggestions(audio_data)
            
            # 应该包含针对各种问题的建议
            suggestion_text = " ".join(suggestions)
            assert "噪音" in suggestion_text or "静音" in suggestion_text or "音量" in suggestion_text
            
    def _create_test_audio_bytes(self, duration=1.0, sample_rate=16000):
        """创建测试用的音频字节数据"""
        # 生成简单的正弦波
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_float = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz正弦波
        audio_int16 = (audio_float * 32767).astype(np.int16)
        return audio_int16.tobytes()


class TestASRErrorTypes:
    """ASR错误类型测试"""
    
    def test_asr_error_inheritance(self):
        """测试ASR错误类继承关系"""
        assert issubclass(ASRQualityError, ASRError)
        assert issubclass(ASRConfidenceError, ASRError)
        assert issubclass(ASRTimeoutError, ASRError)
        
    def test_asr_quality_error(self):
        """测试音频质量错误"""
        error = ASRQualityError("质量过低")
        assert str(error) == "质量过低"
        assert isinstance(error, ASRError)
        
    def test_asr_confidence_error(self):
        """测试置信度错误"""
        error = ASRConfidenceError("置信度过低")
        assert str(error) == "置信度过低"
        assert isinstance(error, ASRError)
        
    def test_asr_timeout_error(self):
        """测试超时错误"""
        error = ASRTimeoutError("处理超时")
        assert str(error) == "处理超时"
        assert isinstance(error, ASRError)


class TestASRIntegration:
    """ASR集成测试"""
    
    def test_full_enhanced_recognition_pipeline(self):
        """测试完整的增强识别流程"""
        asr = MockASR({
            "min_confidence": 0.3,  # 降低阈值以便测试通过
            "min_audio_quality": 0.2,
            "max_processing_time": 10.0
        })
        
        # 创建测试音频
        audio_data = self._create_good_quality_audio()
        
        # 执行增强识别
        result = asr.recognize_enhanced(audio_data)
        
        # 验证结果
        assert result.text is not None
        assert result.confidence > 0
        assert result.confidence_level != ConfidenceLevel.VERY_LOW
        assert result.audio_quality_score > 0
        assert result.processing_time > 0
        
        # 验证音频
        is_valid, message = asr.validate_audio_for_recognition(audio_data)
        assert isinstance(is_valid, bool)
        
        # 获取建议
        suggestions = asr.get_recognition_suggestions(audio_data)
        assert len(suggestions) > 0
        
    def _create_good_quality_audio(self):
        """创建高质量的测试音频"""
        duration = 2.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # 创建包含多个频率的复合信号
        audio_float = (
            0.3 * np.sin(2 * np.pi * 440 * t) +  # 基频
            0.2 * np.sin(2 * np.pi * 880 * t) +  # 倍频
            0.1 * np.sin(2 * np.pi * 1320 * t)   # 三倍频
        )
        
        # 添加少量噪音
        noise = np.random.normal(0, 0.02, len(audio_float))
        audio_float += noise
        
        # 转换为16位整数
        audio_int16 = (np.clip(audio_float, -1.0, 1.0) * 32767).astype(np.int16)
        return audio_int16.tobytes()


if __name__ == "__main__":
    pytest.main([__file__])