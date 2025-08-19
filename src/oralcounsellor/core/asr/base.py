# -*- coding: utf-8 -*-
"""
ASR基类定义
定义统一的语音识别接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import time

from ...utils.encoding_fix import safe_str

logger = logging.getLogger(__name__)


class ASRError(Exception):
    """语音识别错误基类"""
    pass


class ASRQualityError(ASRError):
    """音频质量错误"""
    pass


class ASRConfidenceError(ASRError):
    """识别置信度错误"""
    pass


class ASRTimeoutError(ASRError):
    """识别超时错误"""
    pass


class ConfidenceLevel(Enum):
    """置信度级别"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class ASRResult:
    """ASR识别结果"""
    text: Optional[str]
    confidence: float
    confidence_level: ConfidenceLevel
    audio_quality_score: float
    processing_time: float
    metadata: Dict[str, Any]


class ASRBase(ABC):
    """
    语音识别基类
    定义统一的ASR接口，所有ASR实现都应继承此类
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化ASR实例

        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 质量和置信度阈值配置
        self.min_confidence = self.config.get("min_confidence", 0.6)
        self.min_audio_quality = self.config.get("min_audio_quality", 0.4)
        self.max_processing_time = self.config.get("max_processing_time", 30.0)
        self.enable_quality_check = self.config.get("enable_quality_check", True)
        self.enable_confidence_check = self.config.get("enable_confidence_check", True)

    @abstractmethod
    def recognize(self, audio_data: bytes, **kwargs) -> Optional[str]:
        """
        识别音频数据并返回文本

        Args:
            audio_data: 音频字节数据
            **kwargs: 其他参数

        Returns:
            识别结果文本，失败返回None

        Raises:
            ASRError: 识别过程中的错误
        """
        pass

    @abstractmethod
    def recognize_file(self, audio_path: str, **kwargs) -> Optional[str]:
        """
        识别音频文件并返回文本

        Args:
            audio_path: 音频文件路径
            **kwargs: 其他参数

        Returns:
            识别结果文本，失败返回None

        Raises:
            ASRError: 识别过程中的错误
        """
        pass

    def recognize_gradio_audio(
        self, audio_data: Union[str, Tuple[int, Any]], **kwargs
    ) -> Optional[str]:
        """
        识别Gradio传递的音频数据

        Args:
            audio_data: Gradio音频数据，可能是文件路径字符串或(sample_rate, numpy_array)元组
            **kwargs: 其他参数

        Returns:
            识别结果文本，失败返回None

        Raises:
            ASRError: 识别过程中的错误
        """
        try:
            if audio_data is None:
                self.logger.error("音频数据为空")
                return None

            # 如果是字符串，当作文件路径处理
            if isinstance(audio_data, str):
                return self.recognize_file(audio_data, **kwargs)

            # 如果是元组，说明是Gradio的(sample_rate, audio_array)格式
            if isinstance(audio_data, tuple) and len(audio_data) == 2:
                return self._handle_gradio_tuple(audio_data, **kwargs)

            self.logger.error(f"不支持的音频数据格式: {type(audio_data)}")
            return None

        except Exception as e:
            self.logger.error(f"Gradio音频识别异常: {e}")
            raise ASRError(f"Gradio音频识别失败: {e}")

    def _handle_gradio_tuple(
        self, audio_data: Tuple[int, Any], **kwargs
    ) -> Optional[str]:
        """
        处理Gradio元组格式的音频数据

        Args:
            audio_data: (sample_rate, audio_array)格式的音频数据
            **kwargs: 其他参数

        Returns:
            识别结果文本，失败返回None
        """
        import tempfile
        import os

        try:
            sample_rate, audio_array = audio_data

            # 创建临时文件保存音频数据
            import soundfile as sf

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            # 将numpy数组保存为wav文件
            sf.write(temp_path, audio_array, sample_rate)

            # 识别临时文件
            result = self.recognize_file(temp_path, **kwargs)

            # 清理临时文件
            try:
                os.unlink(temp_path)
            except:
                pass

            return result

        except ImportError:
            self.logger.error("soundfile库未安装，无法处理Gradio音频数据")
            raise ASRError("soundfile库未安装")
        except Exception as e:
            self.logger.error(f"处理Gradio音频数据失败: {e}")
            raise ASRError(f"处理Gradio音频数据失败: {e}")

    def test_connection(self) -> bool:
        """
        测试ASR服务连接

        Returns:
            连接是否正常
        """
        try:
            # 子类可以重写此方法进行具体的连接测试
            return True
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False

    def get_supported_formats(self) -> list:
        """
        获取支持的音频格式列表

        Returns:
            支持的音频格式列表
        """
        # 默认支持的格式，子类可以重写
        return ["wav", "mp3", "flac", "m4a"]

    def validate_audio_file(self, audio_path: str) -> bool:
        """
        验证音频文件是否有效

        Args:
            audio_path: 音频文件路径

        Returns:
            文件是否有效
        """
        import os

        if not os.path.exists(audio_path):
            self.logger.error(f"音频文件不存在: {audio_path}")
            return False

        if os.path.getsize(audio_path) == 0:
            self.logger.error(f"音频文件为空: {audio_path}")
            return False

        # 检查文件扩展名
        file_ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
        if file_ext not in self.get_supported_formats():
            self.logger.warning(f"音频格式可能不受支持: {file_ext}")

        return True

    def recognize_with_error_handling(
        self, 
        audio_data: Union[bytes, str, Tuple[int, Any]], 
        max_retries: int = 3,
        **kwargs
    ) -> ASRResult:
        """
        带错误处理和重试机制的语音识别
        
        Args:
            audio_data: 音频数据
            max_retries: 最大重试次数
            **kwargs: 其他参数
            
        Returns:
            ASRResult: 识别结果
        """
        from ..errors import error_handler, SpeechRecognitionError, AudioInputError
        
        # 首先进行音频验证
        try:
            # 如果是Gradio格式，先转换
            if isinstance(audio_data, tuple) and len(audio_data) == 2:
                # 处理Gradio格式
                processed_audio = self._handle_gradio_tuple(audio_data, **kwargs)
                if processed_audio is None:
                    raise AudioInputError(error_handler.create_error("AUDIO_FORMAT_ERROR").error_info)
                audio_data = processed_audio
            
            # 验证音频数据
            if isinstance(audio_data, str):
                # 文件路径验证
                if not self.validate_audio_file(audio_data):
                    raise AudioInputError(error_handler.create_error("AUDIO_FORMAT_ERROR").error_info)
            else:
                # 字节数据验证
                try:
                    from ...utils.audio import AudioProcessor
                    processor = AudioProcessor()
                    validation_result = processor.validate_audio_input(audio_data)
                    
                    # 检查验证结果
                    validation_error = error_handler.handle_audio_validation_error(validation_result)
                    if validation_error:
                        raise validation_error
                        
                except ImportError:
                    # 如果AudioProcessor不可用，进行基本验证
                    if isinstance(audio_data, bytes) and len(audio_data) < 1000:
                        raise AudioInputError(error_handler.create_error("AUDIO_TOO_SHORT").error_info)
            
            # 执行识别（带重试）
            last_error = None
            for attempt in range(max_retries):
                try:
                    result = self.recognize_enhanced(audio_data, **kwargs)
                    
                    # 检查识别结果
                    asr_error = error_handler.handle_asr_error(result)
                    if asr_error and attempt < max_retries - 1:
                        # 如果不是最后一次尝试，记录警告并重试
                        self.logger.warning(f"ASR识别质量不佳，重试 {attempt + 1}/{max_retries}: {asr_error.error_info.message}")
                        last_error = asr_error
                        time.sleep(0.5 * (attempt + 1))  # 递增延迟
                        continue
                    elif asr_error:
                        # 最后一次尝试仍然有问题，抛出错误
                        raise asr_error
                    
                    # 识别成功
                    if attempt > 0:
                        self.logger.info(f"ASR识别在第 {attempt + 1} 次尝试后成功")
                    
                    return result
                    
                except (AudioInputError, SpeechRecognitionError):
                    # 重新抛出已知错误
                    raise
                except Exception as e:
                    last_error = error_handler.create_error("ASR_SERVICE_ERROR", 
                                                          attempt=attempt + 1, 
                                                          error_message=safe_str(e))
                    if attempt < max_retries - 1:
                        self.logger.warning(f"ASR服务错误，重试 {attempt + 1}/{max_retries}: {e}")
                        time.sleep(1.0 * (attempt + 1))  # 递增延迟
                        continue
                    else:
                        raise last_error
            
            # 如果所有重试都失败了
            if last_error:
                raise last_error
            else:
                raise error_handler.create_error("ASR_SERVICE_ERROR")
                
        except (AudioInputError, SpeechRecognitionError):
            # 重新抛出已知错误
            raise
        except Exception as e:
            # 处理未预期的错误
            self.logger.error(f"语音识别过程中发生未预期错误: {e}")
            raise error_handler.create_error("ASR_SERVICE_ERROR", error_message=safe_str(e))

    def recognize_enhanced(self, audio_data: Union[bytes, str], **kwargs) -> ASRResult:
        """
        增强的语音识别方法，包含质量检测和置信度评估
        
        Args:
            audio_data: 音频数据（字节或文件路径）
            **kwargs: 其他参数
            
        Returns:
            ASRResult: 包含详细信息的识别结果
            
        Raises:
            ASRQualityError: 音频质量不符合要求
            ASRConfidenceError: 识别置信度过低
            ASRTimeoutError: 识别超时
        """
        import time
        
        start_time = time.time()
        metadata = {}
        
        try:
            # 音频质量检测
            if self.enable_quality_check:
                quality_score = self._assess_audio_quality(audio_data, metadata)
                if quality_score < self.min_audio_quality:
                    raise ASRQualityError(
                        f"音频质量过低 (得分: {quality_score:.2f}, 最低要求: {self.min_audio_quality})"
                    )
            else:
                quality_score = 1.0
            
            # 执行识别
            if isinstance(audio_data, bytes):
                text = self.recognize(audio_data, **kwargs)
            else:
                text = self.recognize_file(audio_data, **kwargs)
            
            processing_time = time.time() - start_time
            
            # 检查处理时间
            if processing_time > self.max_processing_time:
                raise ASRTimeoutError(f"识别超时 ({processing_time:.2f}s > {self.max_processing_time}s)")
            
            # 计算置信度
            confidence = self._calculate_confidence(text, metadata)
            confidence_level = self._get_confidence_level(confidence)
            
            # 置信度检查
            if self.enable_confidence_check and confidence < self.min_confidence:
                raise ASRConfidenceError(
                    f"识别置信度过低 (置信度: {confidence:.2f}, 最低要求: {self.min_confidence})"
                )
            
            return ASRResult(
                text=text,
                confidence=confidence,
                confidence_level=confidence_level,
                audio_quality_score=quality_score,
                processing_time=processing_time,
                metadata=metadata
            )
            
        except (ASRQualityError, ASRConfidenceError, ASRTimeoutError):
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"增强识别过程中发生错误: {e}")
            
            return ASRResult(
                text=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                audio_quality_score=0.0,
                processing_time=processing_time,
                metadata={"error": safe_str(e)}
            )

    def _assess_audio_quality(self, audio_data: Union[bytes, str], metadata: Dict[str, Any]) -> float:
        """
        评估音频质量
        
        Args:
            audio_data: 音频数据
            metadata: 元数据字典
            
        Returns:
            float: 质量得分 (0-1)
        """
        try:
            # 尝试导入AudioProcessor，如果失败则使用简化版本
            try:
                from ...utils.audio import AudioProcessor
                
                processor = AudioProcessor()
                
                # 如果是文件路径，读取音频数据
                if isinstance(audio_data, str):
                    audio_array, sample_rate = processor.read_audio_file(audio_data)
                else:
                    # 假设是16位PCM数据
                    import numpy as np
                    audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # 使用AudioProcessor的验证功能
                validation_result = processor.validate_audio_input(audio_array)
                
                # 更新元数据
                metadata.update(validation_result.metadata)
                metadata['validation_issues'] = validation_result.issues
                
                # 根据质量级别计算得分
                quality_scores = {
                    'excellent': 1.0,
                    'good': 0.8,
                    'fair': 0.6,
                    'poor': 0.2
                }
                
                base_score = quality_scores.get(validation_result.quality_level.value, 0.0)
                
                # 如果有问题，降低得分
                if validation_result.issues:
                    penalty = min(0.3, len(validation_result.issues) * 0.1)
                    base_score = max(0.0, base_score - penalty)
                
                return base_score
                
            except ImportError:
                # 如果AudioProcessor不可用，使用简化的质量评估
                return self._simple_audio_quality_check(audio_data, metadata)
            
        except Exception as e:
            self.logger.warning(f"音频质量评估失败: {e}")
            metadata['quality_assessment_error'] = safe_str(e)
            return 0.5  # 默认中等质量

    def _simple_audio_quality_check(self, audio_data: Union[bytes, str], metadata: Dict[str, Any]) -> float:
        """
        简化的音频质量检查（当AudioProcessor不可用时）
        
        Args:
            audio_data: 音频数据
            metadata: 元数据字典
            
        Returns:
            float: 质量得分 (0-1)
        """
        try:
            import os
            
            if isinstance(audio_data, str):
                # 文件路径检查
                if not os.path.exists(audio_data):
                    return 0.0
                
                file_size = os.path.getsize(audio_data)
                metadata['file_size'] = file_size
                
                # 基于文件大小的简单评估
                if file_size < 1000:  # 小于1KB
                    return 0.1
                elif file_size > 10 * 1024 * 1024:  # 大于10MB
                    return 0.7  # 可能是高质量但文件过大
                else:
                    return 0.6  # 中等质量
            else:
                # 字节数据检查
                data_size = len(audio_data)
                metadata['data_size'] = data_size
                
                if data_size < 1000:
                    return 0.1
                elif data_size > 10 * 1024 * 1024:
                    return 0.7
                else:
                    return 0.6
                    
        except Exception as e:
            self.logger.warning(f"简化质量检查失败: {e}")
            return 0.5

    def _calculate_confidence(self, text: Optional[str], metadata: Dict[str, Any]) -> float:
        """
        计算识别置信度
        
        Args:
            text: 识别文本
            metadata: 元数据
            
        Returns:
            float: 置信度 (0-1)
        """
        if not text:
            return 0.0
        
        confidence = 0.5  # 基础置信度
        
        # 基于文本长度的置信度调整
        text_length = len(text.strip())
        if text_length > 0:
            # 文本长度合理性检查
            if 3 <= text_length <= 500:
                confidence += 0.2
            elif text_length > 500:
                confidence -= 0.1  # 过长可能是错误识别
        
        # 基于音频质量的置信度调整
        audio_quality = metadata.get('quality_score', 0)
        if audio_quality > 6:
            confidence += 0.2
        elif audio_quality > 4:
            confidence += 0.1
        elif audio_quality < 2:
            confidence -= 0.2
        
        # 基于信噪比的置信度调整
        snr = metadata.get('snr', 0)
        if snr > 15:
            confidence += 0.1
        elif snr < 5:
            confidence -= 0.1
        
        # 基于静音比例的置信度调整
        silence_ratio = metadata.get('silence_ratio', 0)
        if silence_ratio > 0.8:
            confidence -= 0.2
        elif silence_ratio < 0.2:
            confidence += 0.1
        
        # 检查是否包含常见的识别错误模式
        if self._has_recognition_errors(text):
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))

    def _has_recognition_errors(self, text: str) -> bool:
        """
        检查文本是否包含常见的识别错误模式
        
        Args:
            text: 识别文本
            
        Returns:
            bool: 是否包含错误模式
        """
        if not text:
            return True
        
        # 常见错误模式
        error_patterns = [
            # 重复字符过多
            r'(.)\1{4,}',
            # 过多的标点符号
            r'[。，！？]{3,}',
            # 无意义的字符组合
            r'[a-zA-Z]{10,}',  # 过长的英文字符串（在中文识别中）
            # 数字过多
            r'\d{10,}',
        ]
        
        import re
        for pattern in error_patterns:
            if re.search(pattern, text):
                return True
        
        return False

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        根据置信度数值获取置信度级别
        
        Args:
            confidence: 置信度数值
            
        Returns:
            ConfidenceLevel: 置信度级别
        """
        if confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def validate_audio_for_recognition(self, audio_data: Union[bytes, str]) -> Tuple[bool, str]:
        """
        验证音频是否适合进行语音识别
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            metadata = {}
            quality_score = self._assess_audio_quality(audio_data, metadata)
            
            issues = []
            
            # 检查质量得分
            if quality_score < self.min_audio_quality:
                issues.append(f"音频质量过低 (得分: {quality_score:.2f})")
            
            # 检查具体的质量问题
            validation_issues = metadata.get('validation_issues', [])
            if validation_issues:
                issues.extend(validation_issues)
            
            # 检查时长
            duration = metadata.get('duration', 0)
            if duration < 0.5:
                issues.append("音频时长过短，可能无法准确识别")
            elif duration > 60:
                issues.append("音频时长过长，建议分段处理")
            
            if issues:
                return False, "; ".join(issues)
            else:
                return True, "音频质量良好，适合识别"
                
        except Exception as e:
            return False, f"音频验证失败: {safe_str(e)}"

    def get_recognition_suggestions(self, audio_data: Union[bytes, str]) -> list[str]:
        """
        获取改善识别效果的建议
        
        Args:
            audio_data: 音频数据
            
        Returns:
            list[str]: 建议列表
        """
        suggestions = []
        
        try:
            metadata = {}
            self._assess_audio_quality(audio_data, metadata)
            
            # 基于音频质量给出建议
            snr = metadata.get('snr', 0)
            if snr < 10:
                suggestions.append("环境噪音较大，建议在安静环境中录音")
            
            silence_ratio = metadata.get('silence_ratio', 0)
            if silence_ratio > 0.7:
                suggestions.append("音频中静音过多，建议重新录制")
            
            max_amplitude = metadata.get('max_amplitude', 0)
            if max_amplitude < 0.1:
                suggestions.append("音频音量过低，建议提高录音音量")
            elif max_amplitude > 0.95:
                suggestions.append("音频可能存在削波失真，建议降低录音音量")
            
            duration = metadata.get('duration', 0)
            if duration < 1:
                suggestions.append("音频时长较短，建议录制更长的语音")
            
            if not suggestions:
                suggestions.append("音频质量良好，无需特别调整")
                
        except Exception as e:
            suggestions.append(f"无法分析音频质量: {safe_str(e)}")
        
        return suggestions
