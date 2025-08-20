# -*- coding: utf-8 -*-
"""
音频处理工具模块

提供音频文件的读取、写入、格式转换和基础处理功能。
"""

import os
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np

from .encoding_fix import safe_str


class AudioValidationError(Exception):
    """音频验证错误"""
    pass


class AudioQualityLevel(Enum):
    """音频质量级别"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class AudioValidationResult:
    """音频验证结果"""
    is_valid: bool
    duration: float
    quality_level: AudioQualityLevel
    issues: list[str]
    metadata: Dict[str, Any]


class AudioProcessor:
    """音频处理器类"""

    def __init__(self, sample_rate: int = 16000):
        """
        初始化音频处理器

        Args:
            sample_rate: 目标采样率，默认16kHz
        """
        self.sample_rate = sample_rate
        # 音频验证配置
        self.min_duration = 1.0  # 最小时长（秒）
        self.max_duration = 60.0  # 最大时长（秒）
        self.noise_threshold = 0.1  # 噪音阈值
        self.silence_threshold = 0.01  # 静音阈值

    def read_audio_file(self, file_path: Union[str, Path]) -> Tuple[np.ndarray, int]:
        """
        读取音频文件

        Args:
            file_path: 音频文件路径

        Returns:
            Tuple[np.ndarray, int]: (音频数据, 采样率)

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的音频格式
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {file_path}")

        # 根据文件扩展名选择处理方式
        ext = file_path.suffix.lower()

        if ext == ".wav":
            return self._read_wav_file(file_path)
        else:
            # 对于其他格式，尝试使用通用方法
            try:
                import librosa

                audio_data, sr = librosa.load(str(file_path), sr=self.sample_rate)
                return audio_data, sr
            except ImportError:
                raise ValueError(
                    f"不支持的音频格式: {ext}，请安装librosa库以支持更多格式"
                )

    def _read_wav_file(self, file_path: Path) -> Tuple[np.ndarray, int]:
        """读取WAV文件"""
        with wave.open(str(file_path), "rb") as wav_file:
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()

            # 转换为numpy数组
            if sample_width == 1:
                dtype = np.uint8
            elif sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            else:
                raise ValueError(f"不支持的采样位深: {sample_width}")

            audio_data = np.frombuffer(frames, dtype=dtype)

            # 处理多声道
            if channels > 1:
                audio_data = audio_data.reshape(-1, channels)
                # 转换为单声道（取平均值）
                audio_data = np.mean(audio_data, axis=1)

            # 归一化到[-1, 1]
            if dtype == np.uint8:
                audio_data = (audio_data - 128) / 128.0
            elif dtype == np.int16:
                audio_data = audio_data / 32768.0
            elif dtype == np.int32:
                audio_data = audio_data / 2147483648.0

            return audio_data.astype(np.float32), sample_rate

    def write_audio_file(
        self,
        audio_data: np.ndarray,
        file_path: Union[str, Path],
        sample_rate: Optional[int] = None,
    ) -> None:
        """
        写入音频文件

        Args:
            audio_data: 音频数据
            file_path: 输出文件路径
            sample_rate: 采样率，默认使用实例的采样率
        """
        file_path = Path(file_path)
        sample_rate = sample_rate or self.sample_rate

        # 确保输出目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 归一化音频数据到int16范围
        if audio_data.dtype != np.int16:
            # 限制到[-1, 1]范围
            audio_data = np.clip(audio_data, -1.0, 1.0)
            # 转换到int16
            audio_data = (audio_data * 32767).astype(np.int16)

        # 写入WAV文件
        with wave.open(str(file_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

    def resample_audio(
        self, audio_data: np.ndarray, original_sr: int, target_sr: Optional[int] = None
    ) -> np.ndarray:
        """
        重采样音频

        Args:
            audio_data: 原始音频数据
            original_sr: 原始采样率
            target_sr: 目标采样率，默认使用实例的采样率

        Returns:
            np.ndarray: 重采样后的音频数据
        """
        target_sr = target_sr or self.sample_rate

        if original_sr == target_sr:
            return audio_data

        try:
            import librosa

            return librosa.resample(
                audio_data, orig_sr=original_sr, target_sr=target_sr
            )
        except ImportError:
            # 简单的线性插值重采样（质量较低，但不依赖外部库）
            ratio = target_sr / original_sr
            new_length = int(len(audio_data) * ratio)
            indices = np.linspace(0, len(audio_data) - 1, new_length)
            return np.interp(indices, np.arange(len(audio_data)), audio_data)

    def normalize_audio(
        self, audio_data: np.ndarray, target_level: float = -20.0
    ) -> np.ndarray:
        """
        音频归一化

        Args:
            audio_data: 音频数据
            target_level: 目标音量级别（dB），默认-20dB

        Returns:
            np.ndarray: 归一化后的音频数据
        """
        # 计算RMS
        rms = np.sqrt(np.mean(audio_data**2))

        if rms == 0:
            return audio_data

        # 计算当前音量级别（dB）
        current_level = 20 * np.log10(rms)

        # 计算增益
        gain_db = target_level - current_level
        gain_linear = 10 ** (gain_db / 20)

        # 应用增益并限制幅度
        normalized = audio_data * gain_linear
        return np.clip(normalized, -1.0, 1.0)

    def trim_silence(
        self, audio_data: np.ndarray, threshold: float = 0.01, frame_length: int = 1024
    ) -> np.ndarray:
        """
        去除音频首尾的静音

        Args:
            audio_data: 音频数据
            threshold: 静音阈值
            frame_length: 帧长度

        Returns:
            np.ndarray: 去除静音后的音频数据
        """
        # 计算每帧的能量
        num_frames = len(audio_data) // frame_length
        energy = []

        for i in range(num_frames):
            start = i * frame_length
            end = start + frame_length
            frame_energy = np.mean(audio_data[start:end] ** 2)
            energy.append(frame_energy)

        energy = np.array(energy)

        # 找到非静音帧
        non_silent = energy > threshold

        if not np.any(non_silent):
            return audio_data  # 如果全是静音，返回原音频

        # 找到第一个和最后一个非静音帧
        first_frame = np.argmax(non_silent)
        last_frame = len(non_silent) - 1 - np.argmax(non_silent[::-1])

        # 计算对应的样本索引
        start_sample = first_frame * frame_length
        end_sample = min((last_frame + 1) * frame_length, len(audio_data))

        return audio_data[start_sample:end_sample]

    def validate_audio_input(self, audio_data: Union[np.ndarray, bytes, Any]) -> AudioValidationResult:
        """
        验证音频输入数据
        
        Args:
            audio_data: 音频数据，可以是numpy数组、字节数据或其他格式
            
        Returns:
            AudioValidationResult: 验证结果
        """
        issues = []
        metadata = {}
        
        try:
            # 转换音频数据为numpy数组
            if isinstance(audio_data, bytes):
                # 假设是16位PCM数据
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif isinstance(audio_data, np.ndarray):
                audio_array = audio_data.astype(np.float32)
            else:
                # 尝试其他转换方式
                try:
                    audio_array = np.array(audio_data, dtype=np.float32)
                except:
                    issues.append("无法识别的音频数据格式")
                    return AudioValidationResult(
                        is_valid=False,
                        duration=0.0,
                        quality_level=AudioQualityLevel.POOR,
                        issues=issues,
                        metadata=metadata
                    )
            
            # 检查音频数据是否为空
            if len(audio_array) == 0:
                issues.append("音频数据为空")
                return AudioValidationResult(
                    is_valid=False,
                    duration=0.0,
                    quality_level=AudioQualityLevel.POOR,
                    issues=issues,
                    metadata=metadata
                )
            
            # 计算时长
            duration = len(audio_array) / self.sample_rate
            metadata['duration'] = duration
            metadata['sample_count'] = len(audio_array)
            
            # 检查时长
            if duration < self.min_duration:
                issues.append(f"音频时长过短（{duration:.2f}秒），最少需要{self.min_duration}秒")
            elif duration > self.max_duration:
                issues.append(f"音频时长过长（{duration:.2f}秒），最多允许{self.max_duration}秒")
            
            # 音频质量检测
            quality_level = self._assess_audio_quality(audio_array, metadata)
            
            # 检查是否主要是静音
            silence_ratio = self._calculate_silence_ratio(audio_array)
            metadata['silence_ratio'] = silence_ratio
            
            if silence_ratio > 0.8:
                issues.append(f"音频中静音比例过高（{silence_ratio:.1%}）")
            
            # 检查音频幅度
            max_amplitude = np.max(np.abs(audio_array))
            rms_amplitude = np.sqrt(np.mean(audio_array ** 2))
            metadata['max_amplitude'] = max_amplitude
            metadata['rms_amplitude'] = rms_amplitude
            
            if max_amplitude < 0.005 or rms_amplitude < 0.001:
                issues.append("音频音量过低，可能录制失败")
            elif max_amplitude > 0.95:
                issues.append("音频可能存在削波失真")
            
            # 判断整体有效性
            is_valid = len(issues) == 0 and quality_level != AudioQualityLevel.POOR
            
            return AudioValidationResult(
                is_valid=is_valid,
                duration=duration,
                quality_level=quality_level,
                issues=issues,
                metadata=metadata
            )
            
        except Exception as e:
            issues.append(f"音频验证过程中发生错误: {safe_str(e)}")
            return AudioValidationResult(
                is_valid=False,
                duration=0.0,
                quality_level=AudioQualityLevel.POOR,
                issues=issues,
                metadata=metadata
            )

    def _assess_audio_quality(self, audio_data: np.ndarray, metadata: Dict[str, Any]) -> AudioQualityLevel:
        """
        评估音频质量
        
        Args:
            audio_data: 音频数据
            metadata: 元数据字典，用于存储质量指标
            
        Returns:
            AudioQualityLevel: 音频质量级别
        """
        # 计算信噪比
        snr = self._calculate_snr(audio_data)
        metadata['snr'] = snr
        
        # 计算频谱质量
        spectral_quality = self._calculate_spectral_quality(audio_data)
        metadata['spectral_quality'] = spectral_quality
        
        # 计算动态范围
        dynamic_range = self._calculate_dynamic_range(audio_data)
        metadata['dynamic_range'] = dynamic_range
        
        # 综合评估
        quality_score = 0
        
        # SNR评分 - 调整阈值使其更合理
        if snr > 15:
            quality_score += 3
        elif snr > 8:
            quality_score += 2
        elif snr > 3:
            quality_score += 1
        
        # 频谱质量评分 - 调整阈值
        if spectral_quality > 0.3:
            quality_score += 3
        elif spectral_quality > 0.15:
            quality_score += 2
        elif spectral_quality > 0.05:
            quality_score += 1
        
        # 动态范围评分 - 调整阈值
        if dynamic_range > 25:
            quality_score += 2
        elif dynamic_range > 15:
            quality_score += 1
        
        metadata['quality_score'] = quality_score
        
        # 根据总分确定质量级别 - 调整阈值
        if quality_score >= 6:
            return AudioQualityLevel.EXCELLENT
        elif quality_score >= 4:
            return AudioQualityLevel.GOOD
        elif quality_score >= 2:
            return AudioQualityLevel.FAIR
        else:
            return AudioQualityLevel.POOR

    def _calculate_snr(self, audio_data: np.ndarray) -> float:
        """计算信噪比"""
        # 简化的SNR计算：使用RMS和最小值的比值
        rms = np.sqrt(np.mean(audio_data ** 2))
        noise_floor = np.percentile(np.abs(audio_data), 10)  # 使用10%分位数作为噪音基准
        
        if noise_floor == 0:
            return 60.0  # 返回一个高SNR值
        
        snr = 20 * np.log10(rms / noise_floor)
        return max(0, snr)  # 确保SNR不为负

    def _calculate_spectral_quality(self, audio_data: np.ndarray) -> float:
        """计算频谱质量"""
        # 使用FFT分析频谱分布
        fft = np.fft.fft(audio_data)
        magnitude = np.abs(fft[:len(fft)//2])
        
        # 计算频谱的平坦度（越平坦质量越好）
        if len(magnitude) == 0:
            return 0.0
        
        # 计算频谱重心
        freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)[:len(magnitude)]
        spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude) if np.sum(magnitude) > 0 else 0
        
        # 归一化到0-1范围
        normalized_centroid = min(spectral_centroid / (self.sample_rate / 4), 1.0)
        
        return normalized_centroid

    def _calculate_dynamic_range(self, audio_data: np.ndarray) -> float:
        """计算动态范围"""
        if len(audio_data) == 0:
            return 0.0
        
        max_val = np.max(np.abs(audio_data))
        min_val = np.percentile(np.abs(audio_data), 5)  # 使用5%分位数避免噪音影响
        
        if min_val == 0:
            return 60.0  # 返回一个高动态范围值
        
        dynamic_range = 20 * np.log10(max_val / min_val)
        return max(0, dynamic_range)

    def _calculate_silence_ratio(self, audio_data: np.ndarray) -> float:
        """计算静音比例"""
        silence_mask = np.abs(audio_data) < self.silence_threshold
        return np.sum(silence_mask) / len(audio_data)

    def convert_audio_format_enhanced(
        self, 
        audio_data: Union[np.ndarray, bytes], 
        source_format: str = "pcm",
        target_format: str = "wav",
        source_sample_rate: int = None,
        target_sample_rate: int = None
    ) -> bytes:
        """
        增强的音频格式转换功能
        
        Args:
            audio_data: 源音频数据
            source_format: 源格式 ("pcm", "wav", "mp3", etc.)
            target_format: 目标格式 ("wav", "mp3", "flac", etc.)
            source_sample_rate: 源采样率
            target_sample_rate: 目标采样率
            
        Returns:
            bytes: 转换后的音频数据
        """
        source_sample_rate = source_sample_rate or self.sample_rate
        target_sample_rate = target_sample_rate or self.sample_rate
        
        # 转换为numpy数组
        if isinstance(audio_data, bytes):
            if source_format.lower() == "pcm":
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                # 对于其他格式，需要更复杂的解码
                raise ValueError(f"暂不支持从字节数据解码 {source_format} 格式")
        else:
            audio_array = audio_data.astype(np.float32)
        
        # 重采样
        if source_sample_rate != target_sample_rate:
            audio_array = self.resample_audio(audio_array, source_sample_rate, target_sample_rate)
        
        # 转换为目标格式
        if target_format.lower() == "wav":
            return self._convert_to_wav_bytes(audio_array, target_sample_rate)
        elif target_format.lower() == "pcm":
            # 转换为16位PCM
            pcm_data = (np.clip(audio_array, -1.0, 1.0) * 32767).astype(np.int16)
            return pcm_data.tobytes()
        else:
            raise ValueError(f"暂不支持转换到 {target_format} 格式")

    def _convert_to_wav_bytes(self, audio_data: np.ndarray, sample_rate: int) -> bytes:
        """将音频数据转换为WAV格式的字节数据"""
        import io
        
        # 转换为16位整数
        audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
        
        # 创建WAV文件的字节流
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return wav_buffer.getvalue()

    def get_audio_duration_from_data(self, audio_data: Union[np.ndarray, bytes], sample_rate: int = None) -> float:
        """
        从音频数据获取时长
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            float: 时长（秒）
        """
        sample_rate = sample_rate or self.sample_rate
        
        if isinstance(audio_data, bytes):
            # 假设是16位PCM数据
            sample_count = len(audio_data) // 2
        elif isinstance(audio_data, np.ndarray):
            sample_count = len(audio_data)
        else:
            raise ValueError("不支持的音频数据类型")
        
        return sample_count / sample_rate

    def detect_voice_activity(self, audio_data: np.ndarray, frame_length: int = 1024) -> np.ndarray:
        """
        语音活动检测 (Voice Activity Detection)
        
        Args:
            audio_data: 音频数据
            frame_length: 帧长度
            
        Returns:
            np.ndarray: 布尔数组，True表示有语音活动
        """
        num_frames = len(audio_data) // frame_length
        vad_result = np.zeros(num_frames, dtype=bool)
        
        for i in range(num_frames):
            start = i * frame_length
            end = start + frame_length
            frame = audio_data[start:end]
            
            # 计算帧能量
            energy = np.mean(frame ** 2)
            
            # 计算过零率
            zero_crossings = np.sum(np.diff(np.sign(frame)) != 0)
            zcr = zero_crossings / len(frame)
            
            # 简单的VAD判断：能量高且过零率适中
            has_voice = energy > self.silence_threshold and 0.01 < zcr < 0.3
            vad_result[i] = has_voice
        
        return vad_result


def create_temp_audio_file(suffix: str = ".wav") -> str:
    """
    创建临时音频文件

    Args:
        suffix: 文件后缀

    Returns:
        str: 临时文件路径
    """
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path: str) -> None:
    """
    清理临时文件

    Args:
        file_path: 文件路径
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except OSError:
        pass  # 忽略删除失败的情况


def get_audio_duration(file_path: Union[str, Path]) -> float:
    """
    获取音频文件时长

    Args:
        file_path: 音频文件路径

    Returns:
        float: 时长（秒）
    """
    processor = AudioProcessor()
    audio_data, sample_rate = processor.read_audio_file(file_path)
    return len(audio_data) / sample_rate


def convert_audio_format(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    target_sample_rate: int = 16000,
) -> None:
    """
    转换音频格式

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        target_sample_rate: 目标采样率
    """
    processor = AudioProcessor(sample_rate=target_sample_rate)
    audio_data, original_sr = processor.read_audio_file(input_path)

    if original_sr != target_sample_rate:
        audio_data = processor.resample_audio(
            audio_data, original_sr, target_sample_rate
        )

    processor.write_audio_file(audio_data, output_path, target_sample_rate)
