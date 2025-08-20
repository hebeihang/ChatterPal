# -*- coding: utf-8 -*-
"""
音频处理性能优化模块
提供音频数据的优化处理功能
"""

import io
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from pathlib import Path
import logging
from dataclasses import dataclass
from queue import Queue, Empty
import wave
import audioop

from .cache import get_tts_cache


logger = logging.getLogger(__name__)


@dataclass
class AudioProcessingTask:
    """音频处理任务"""
    task_id: str
    audio_data: bytes
    operation: str
    params: Dict[str, Any]
    callback: Optional[Callable] = None
    priority: int = 0  # 优先级，数字越小优先级越高


class AudioBuffer:
    """音频缓冲区"""
    
    def __init__(self, max_size: int = 10):
        """
        初始化音频缓冲区
        
        Args:
            max_size: 最大缓冲区大小
        """
        self.max_size = max_size
        self._buffer: Queue = Queue(maxsize=max_size)
        self._lock = threading.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def put(self, audio_data: bytes, timeout: Optional[float] = None) -> bool:
        """
        添加音频数据到缓冲区
        
        Args:
            audio_data: 音频数据
            timeout: 超时时间
            
        Returns:
            是否成功添加
        """
        try:
            self._buffer.put(audio_data, timeout=timeout)
            return True
        except Exception as e:
            self.logger.error(f"添加音频数据到缓冲区失败: {e}")
            return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """
        从缓冲区获取音频数据
        
        Args:
            timeout: 超时时间
            
        Returns:
            音频数据，如果超时返回None
        """
        try:
            return self._buffer.get(timeout=timeout)
        except Empty:
            return None
        except Exception as e:
            self.logger.error(f"从缓冲区获取音频数据失败: {e}")
            return None
    
    def size(self) -> int:
        """获取缓冲区当前大小"""
        return self._buffer.qsize()
    
    def is_full(self) -> bool:
        """检查缓冲区是否已满"""
        return self._buffer.full()
    
    def is_empty(self) -> bool:
        """检查缓冲区是否为空"""
        return self._buffer.empty()


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self, max_workers: int = 4):
        """
        初始化音频处理器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 处理统计
        self._stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0
        }
        self._stats_lock = threading.Lock()
    
    def _update_stats(self, processing_time: float, success: bool) -> None:
        """更新处理统计"""
        with self._stats_lock:
            if success:
                self._stats["tasks_processed"] += 1
                self._stats["total_processing_time"] += processing_time
                self._stats["average_processing_time"] = (
                    self._stats["total_processing_time"] / self._stats["tasks_processed"]
                )
            else:
                self._stats["tasks_failed"] += 1
    
    def convert_sample_rate(self, audio_data: bytes, from_rate: int, 
                          to_rate: int) -> bytes:
        """
        转换音频采样率
        
        Args:
            audio_data: 原始音频数据
            from_rate: 原始采样率
            to_rate: 目标采样率
            
        Returns:
            转换后的音频数据
        """
        start_time = time.time()
        
        try:
            # 使用audioop进行采样率转换
            converted_data, _ = audioop.ratecv(
                audio_data, 2, 1, from_rate, to_rate, None
            )
            
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            return converted_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            self.logger.error(f"采样率转换失败: {e}")
            raise
    
    def normalize_volume(self, audio_data: bytes, target_volume: float = 0.8) -> bytes:
        """
        标准化音频音量
        
        Args:
            audio_data: 音频数据
            target_volume: 目标音量（0.0-1.0）
            
        Returns:
            标准化后的音频数据
        """
        start_time = time.time()
        
        try:
            # 计算当前音量
            max_amplitude = audioop.max(audio_data, 2)
            if max_amplitude == 0:
                return audio_data
            
            # 计算缩放因子
            scale_factor = int((target_volume * 32767) / max_amplitude)
            
            # 应用音量调整
            normalized_data = audioop.mul(audio_data, 2, scale_factor)
            
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            return normalized_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            self.logger.error(f"音量标准化失败: {e}")
            raise
    
    def compress_audio(self, audio_data: bytes, compression_ratio: float = 0.5) -> bytes:
        """
        压缩音频数据
        
        Args:
            audio_data: 音频数据
            compression_ratio: 压缩比例
            
        Returns:
            压缩后的音频数据
        """
        start_time = time.time()
        
        try:
            # 简单的音频压缩：降低位深度
            compressed_data = audioop.lin2lin(audio_data, 2, 1)
            
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            return compressed_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            self.logger.error(f"音频压缩失败: {e}")
            raise
    
    def process_async(self, task: AudioProcessingTask) -> Future:
        """
        异步处理音频任务
        
        Args:
            task: 音频处理任务
            
        Returns:
            Future对象
        """
        def _process_task():
            start_time = time.time()
            
            try:
                if task.operation == "convert_sample_rate":
                    result = self.convert_sample_rate(
                        task.audio_data,
                        task.params["from_rate"],
                        task.params["to_rate"]
                    )
                elif task.operation == "normalize_volume":
                    result = self.normalize_volume(
                        task.audio_data,
                        task.params.get("target_volume", 0.8)
                    )
                elif task.operation == "compress":
                    result = self.compress_audio(
                        task.audio_data,
                        task.params.get("compression_ratio", 0.5)
                    )
                else:
                    raise ValueError(f"未知的操作: {task.operation}")
                
                # 调用回调函数
                if task.callback:
                    task.callback(task.task_id, result, None)
                
                return result
                
            except Exception as e:
                if task.callback:
                    task.callback(task.task_id, None, e)
                raise
        
        return self.executor.submit(_process_task)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        with self._stats_lock:
            return self._stats.copy()
    
    def shutdown(self) -> None:
        """关闭处理器"""
        self.executor.shutdown(wait=True)


class OptimizedTTSService:
    """优化的TTS服务"""
    
    def __init__(self, tts_service, enable_cache: bool = True, 
                 enable_preprocessing: bool = True):
        """
        初始化优化的TTS服务
        
        Args:
            tts_service: 原始TTS服务
            enable_cache: 是否启用缓存
            enable_preprocessing: 是否启用预处理
        """
        self.tts_service = tts_service
        self.enable_cache = enable_cache
        self.enable_preprocessing = enable_preprocessing
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 获取缓存和处理器
        if enable_cache:
            self.cache = get_tts_cache()
        
        if enable_preprocessing:
            self.audio_processor = AudioProcessor()
        
        # 预处理队列
        self.preprocessing_queue = Queue()
        self._start_preprocessing_worker()
    
    def _start_preprocessing_worker(self) -> None:
        """启动预处理工作线程"""
        if not self.enable_preprocessing:
            return
        
        def preprocessing_worker():
            while True:
                try:
                    task = self.preprocessing_queue.get(timeout=1.0)
                    if task is None:  # 停止信号
                        break
                    
                    text, voice, rate, volume = task
                    self._preprocess_text(text, voice, rate, volume)
                    
                except Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"预处理工作线程出错: {e}")
        
        worker_thread = threading.Thread(target=preprocessing_worker, daemon=True)
        worker_thread.start()
    
    def _preprocess_text(self, text: str, voice: str, rate: str, volume: str) -> None:
        """预处理文本"""
        try:
            # 检查缓存中是否已存在
            if self.enable_cache:
                cached_result = self.cache.get(text, voice, rate, volume)
                if cached_result is not None:
                    return
            
            # 生成TTS并缓存
            audio_data = self.tts_service.synthesize(text, voice, rate, volume)
            
            if self.enable_cache and audio_data:
                self.cache.put(text, voice, audio_data, rate, volume)
                
        except Exception as e:
            self.logger.error(f"预处理文本失败: {e}")
    
    def synthesize(self, text: str, voice: str = "en-US-JennyNeural", 
                  rate: str = "+0%", volume: str = "+0%") -> Optional[bytes]:
        """
        合成语音（优化版本）
        
        Args:
            text: 要合成的文本
            voice: 语音
            rate: 语速
            volume: 音量
            
        Returns:
            音频数据
        """
        # 检查缓存
        if self.enable_cache:
            cached_result = self.cache.get(text, voice, rate, volume)
            if cached_result is not None:
                self.logger.debug(f"从缓存获取TTS结果: {text[:50]}...")
                return cached_result
        
        # 生成TTS
        try:
            audio_data = self.tts_service.synthesize(text, voice, rate, volume)
            
            # 缓存结果
            if self.enable_cache and audio_data:
                self.cache.put(text, voice, audio_data, rate, volume)
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"TTS合成失败: {e}")
            return None
    
    def preload_common_phrases(self, phrases: List[str], voice: str = "en-US-JennyNeural",
                              rate: str = "+0%", volume: str = "+0%") -> None:
        """
        预加载常用短语
        
        Args:
            phrases: 常用短语列表
            voice: 语音
            rate: 语速
            volume: 音量
        """
        if not self.enable_preprocessing:
            return
        
        for phrase in phrases:
            self.preprocessing_queue.put((phrase, voice, rate, volume))
        
        self.logger.info(f"已添加 {len(phrases)} 个短语到预处理队列")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if self.enable_cache:
            return self.cache.get_stats()
        return {}
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.enable_cache:
            self.cache.clear()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._metrics = {}
        self._lock = threading.Lock()
    
    def start_timing(self, operation: str) -> str:
        """开始计时"""
        timing_id = f"{operation}_{int(time.time() * 1000000)}"
        
        with self._lock:
            self._metrics[timing_id] = {
                "operation": operation,
                "start_time": time.time(),
                "end_time": None,
                "duration": None
            }
        
        return timing_id
    
    def end_timing(self, timing_id: str) -> Optional[float]:
        """结束计时"""
        end_time = time.time()
        
        with self._lock:
            if timing_id not in self._metrics:
                return None
            
            metric = self._metrics[timing_id]
            metric["end_time"] = end_time
            metric["duration"] = end_time - metric["start_time"]
            
            return metric["duration"]
    
    def record_metric(self, name: str, value: Union[int, float], 
                     tags: Optional[Dict[str, str]] = None) -> None:
        """记录指标"""
        with self._lock:
            metric_key = f"{name}_{int(time.time())}"
            self._metrics[metric_key] = {
                "name": name,
                "value": value,
                "timestamp": time.time(),
                "tags": tags or {}
            }
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """获取操作统计信息"""
        with self._lock:
            operation_metrics = [
                m for m in self._metrics.values()
                if m.get("operation") == operation and m.get("duration") is not None
            ]
            
            if not operation_metrics:
                return {}
            
            durations = [m["duration"] for m in operation_metrics]
            
            return {
                "count": len(durations),
                "total_time": sum(durations),
                "average_time": sum(durations) / len(durations),
                "min_time": min(durations),
                "max_time": max(durations)
            }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息"""
        with self._lock:
            operations = set(
                m.get("operation") for m in self._metrics.values()
                if m.get("operation") is not None
            )
            
            stats = {}
            for operation in operations:
                stats[operation] = self.get_operation_stats(operation)
            
            return stats
    
    def clear_metrics(self) -> None:
        """清空指标"""
        with self._lock:
            self._metrics.clear()


# 全局性能监控器
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    获取全局性能监控器实例
    
    Returns:
        性能监控器实例
    """
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor


def time_operation(operation_name: str):
    """
    操作计时装饰器
    
    Args:
        operation_name: 操作名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            timing_id = monitor.start_timing(operation_name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.end_timing(timing_id)
        
        return wrapper
    return decorator