"""
性能测试模块
测试缓存和音频处理的性能
"""

import pytest
import time
import threading
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from chatterpal.utils.cache import (
    LRUCache, TTSCache, SessionCache, CacheManager,
    get_cache_manager, get_tts_cache, get_session_cache
)
from chatterpal.utils.audio_optimizer import (
    AudioProcessor, AudioBuffer, OptimizedTTSService,
    PerformanceMonitor, get_performance_monitor, time_operation
)


class TestLRUCache:
    """LRU缓存性能测试"""
    
    def test_cache_performance(self):
        """测试缓存性能"""
        cache = LRUCache(max_size=1000)
        
        # 测试写入性能
        start_time = time.time()
        for i in range(1000):
            cache.put(f"key_{i}", f"value_{i}")
        write_time = time.time() - start_time
        
        # 测试读取性能
        start_time = time.time()
        for i in range(1000):
            cache.get(f"key_{i}")
        read_time = time.time() - start_time
        
        print(f"写入1000个条目耗时: 秒{write_time:.4f})
        print(f"读取1000个条目耗时: 秒{read_time:.4f})
        
        # 性能断言
        assert write_time < 1.0  # 写入应该秒内完成
        assert read_time < 0.5   # 读取应该.5秒内完成
    
    def test_concurrent_access(self):
        """测试并发访问性能"""
        cache = LRUCache(max_size=1000)
        
        def writer_thread(start_idx: int, count: int):
            for i in range(start_idx, start_idx + count):
                cache.put(f"key_{i}", f"value_{i}")
        
        def reader_thread(start_idx: int, count: int):
            for i in range(start_idx, start_idx + count):
                cache.get(f"key_{i}")
        
        # 启动多个写入线程
        threads = []
        start_time = time.time()
        
        for i in range(4):
            thread = threading.Thread(target=writer_thread, args=(i * 250, 250))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        write_time = time.time() - start_time
        
        # 启动多个读取线程
        threads = []
        start_time = time.time()
        
        for i in range(4):
            thread = threading.Thread(target=reader_thread, args=(i * 250, 250))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        read_time = time.time() - start_time
        
        print(f"并发写入耗时: 秒{write_time:.4f})
        print(f"并发读取耗时: 秒{read_time:.4f})
        
        # 并发性能断言
        assert write_time < 2.0
        assert read_time < 1.0
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        cache = LRUCache(max_size=10000)
        
        # 添加大量数据
        large_value = "x" * 1000  # 1KB的字符串
        
        for i in range(1000):
            cache.put(f"key_{i}", large_value)
        
        stats = cache.get_stats()
        
        # 检查统计信息息
        assert stats["size"] == 1000
        assert stats["total_size_bytes"] > 0
        
        print(f"缓存大小: {stats['size']}")
        print(f"总内存使用 {stats['total_size_bytes']} 字节")


class TestTTSCache:
    """TTS缓存性能测试"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_tts_cache_performance(self, temp_cache_dir):
        """测试TTS缓存性能"""
        cache = TTSCache(cache_dir=temp_cache_dir, max_memory_size=100)
        
        # 模拟音频数据
        audio_data = b"fake_audio_data" * 1000  # 5KB
        
        # 测试存储性能
        start_time = time.time()
        for i in range(100):
            cache.put(f"text_{i}", "voice", audio_data)
        store_time = time.time() - start_time
        
        # 测试检索性能
        start_time = time.time()
        for i in range(100):
            result = cache.get(f"text_{i}", "voice")
            assert result is not None
        retrieve_time = time.time() - start_time
        
        print(f"存储1检索100个TTS结果耗时: 秒秒{store_time:.4f})
        print(f"检检索100个TTS结果耗时: 秒{retrieve_time:.4f})
        
        # 性能断言
        assert store_time < 2.0
        assert retrieve_time < 0.5
        
        # 检查缓存统计计
        stats = cache.get_stats()
        assert stats["stats"]["memory_hits"] > 0
        assert stats["hit_rate"] > 0.8
    
    def test_disk_cache_performance(self, temp_cache_dir):
        """测试磁盘缓存性能"""
        cache = TTSCache(cache_dir=temp_cache_dir, max_memory_size=10)
        
        # 添加超过内存缓存大小的数据
        audio_data = b"fake_audio_data" * 1000
        
        for i in range(50):
            cache.put(f"text_{i}", "voice", audio_data)
        
        # 清空内存缓存以测试磁盘缓存
        cache._memory_cache.clear()
        
        # 测试从磁盘读取性能
        start_time = time.time()
        for i in range(20):
            result = cache.get(f"text_{i}", "voice")
            assert result is not None
        disk_read_time = time.time() - start_time
        
        print(f"从磁盘读0个TTS结果耗时: {disk_read_time:.4f})
        
        # 磁盘读取性能断言
        assert disk_read_time < 1.0
        
        stats = cache.get_stats()
        assert stats["stats"]["disk_hits"] > 0


class TestAudioProcessor:
    """音频处理器性能测试"""
    
    def test_audio_processing_performance(self):
        """测试音频处理性能"""
        processor = AudioProcessor(max_workers=4)
        
        # 模拟音频数据6位,单声道,1秒@16kHz
        audio_data = b"\x00\x01" * 16000
        
        # 测试采样率转换性能
        start_time = time.time()
        for _ in range(10):
            processor.convert_sample_rate(audio_data, 16000, 22050)
        convert_time = time.time() - start_time
        
        # 测试音量标准化性能
        start_time = time.time()
        for _ in range(10):
            processor.normalize_volume(audio_data, 0.8)
        normalize_time = time.time() - start_time
        
        print(f"10次采样率转换耗时: 秒{convert_time:.4f})
        print(f"10次音量标准化耗时: 秒{normalize_time:.4f})
        
        # 性能断言
        assert convert_time < 2.0
        assert normalize_time < 1.0
        
        # 检查处理统计
        stats = processor.get_stats()
        assert stats["tasks_processed"] > 0
        assert stats["average_processing_time"] > 0
        
        processor.shutdown()
    
    def test_concurrent_audio_processing(self):
        """测试并发音频处理"""
        processor = AudioProcessor(max_workers=4)
        
        # 模拟音频数据
        audio_data = b"\x00\x01" * 8000
        
        from chatterpal.utils.audio_optimizer import AudioProcessingTask
        
        # 创建多个处理任务
        tasks = []
        for i in range(20):
            task = AudioProcessingTask(
                task_id=f"task_{i}",
                audio_data=audio_data,
                operation="normalize_volume",
                params={"target_volume": 0.8}
            )
            tasks.append(task)
        
        # 并发处理
        start_time = time.time()
        futures = [processor.process_async(task) for task in tasks]
        
        # 等待所有任务完成
        for future in futures:
            future.result()
        
        processing_time = time.time() - start_time
        
        print(f"并发处理20个音频任务耗时: 秒{processing_time:.4f})
        
        # 并发处理应该比串行处理快
        assert processing_time < 5.0
        
        processor.shutdown()


class TestAudioBuffer:
    """音频缓冲区性能测试"""
    
    def test_buffer_throughput(self):
        """测试缓冲区吞吐量"""
        buffer = AudioBuffer(max_size=100)
        
        # 模拟音频数据
        audio_data = b"audio_chunk" * 100
        
        # 测试写入吞吐量
        start_time = time.time()
        for i in range(100):
            success = buffer.put(audio_data, timeout=1.0)
            assert success
        write_time = time.time() - start_time
        
        # 测试读取吞吐量
        start_time = time.time()
        for i in range(100):
            data = buffer.get(timeout=1.0)
            assert data is not None
        read_time = time.time() - start_time
        
        print(f"缓冲区写00个块耗时: {write_time:.4f})
        print(f"缓冲区读00个块耗时: {read_time:.4f})
        
        # 吞吐量断言
        assert write_time < 1.0
        assert read_time < 1.0


class TestOptimizedTTSService:
    """优化TTS服务性能测试"""
    
    def test_tts_optimization_performance(self):
        """测试TTS优化性能"""
        # 模拟原始TTS服务
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"fake_audio_data" * 1000
        
        # 创建优化服务
        optimized_tts = OptimizedTTSService(
            mock_tts, 
            enable_cache=True, 
            enable_preprocessing=True
        )
        
        # 测试首次合成(无缓存)
        start_time = time.time()
        result1 = optimized_tts.synthesize("Hello world", "voice")
        first_time = time.time() - start_time
        
        # 测试缓存命中
        start_time = time.time()
        result2 = optimized_tts.synthesize("Hello world", "voice")
        cached_time = time.time() - start_time
        
        assert result1 == result2
        # 缓存应该更快或至少不慢太多(考虑测量误差)
        assert cached_time <= first_time * 1.5
        
        print(f"首次TTS合成耗时: 秒{first_time:.4f})
        print(f"缓存命中耗时: 秒{cached_time:.4f})
        if first_time > 0:
            print(f"性能提升: {(first_time - cached_time) / first_time * 100:.1f}%")
        else:
            print("时间太短,无法准确测量性能提升")
        
        # 检查缓存统计计
        stats = optimized_tts.get_cache_stats()
        assert stats["stats"]["memory_hits"] > 0
    
    def test_preloading_performance(self):
        """测试预加载性能"""
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"fake_audio_data" * 500
        
        optimized_tts = OptimizedTTSService(mock_tts, enable_preprocessing=True)
        
        # 预加载常用短语
        common_phrases = [
            "Hello", "How are you", "Thank you", "Goodbye",
            "Please", "Sorry", "Excuse me", "You're welcome"
        ]
        
        optimized_tts.preload_common_phrases(common_phrases)
        
        # 等待预处理完成
        time.sleep(2.0)
        
        # 测试预加载短语的访问速度
        start_time = time.time()
        for phrase in common_phrases:
            result = optimized_tts.synthesize(phrase)
            assert result is not None
        preloaded_time = time.time() - start_time
        
        print(f"访问8个预加载短语耗时: 秒{preloaded_time:.4f})
        
        # 预加载的短语应该很快访问
        assert preloaded_time < 0.1


class TestPerformanceMonitor:
    """性能监控器测试""
    
    def test_timing_accuracy(self):
        """测试计时精度"""
        monitor = PerformanceMonitor()
        
        # 测试短时间操作
        timing_id = monitor.start_timing("short_operation")
        time.sleep(0.1)
        duration = monitor.end_timing(timing_id)
        
        assert duration is not None
        assert 0.09 <= duration <= 0.15  # 允许一定误差
        
        # 测试长时间操作
        timing_id = monitor.start_timing("long_operation")
        time.sleep(0.5)
        duration = monitor.end_timing(timing_id)
        
        assert duration is not None
        assert 0.45 <= duration <= 0.55
    
    def test_operation_statistics(self):
        """测试操作统计"""
        monitor = PerformanceMonitor()
        
        # 执行多次相同操作
        for i in range(10):
            timing_id = monitor.start_timing("test_operation")
            time.sleep(0.01 * (i + 1))  # 递增的延迟
            monitor.end_timing(timing_id)
        
        stats = monitor.get_operation_stats("test_operation")
        
        assert stats["count"] == 10
        assert stats["total_time"] > 0
        assert stats["average_time"] > 0
        assert stats["min_time"] > 0
        assert stats["max_time"] > stats["min_time"]
        
        print(f"操作统计: {stats}")
    
    def test_timing_decorator(self):
        """测试计时装饰器""
        
        @time_operation("decorated_function")
        def test_function(delay: float):
            time.sleep(delay)
            return "result"
        
        # 执行被装饰的函数
        result = test_function(0.1)
        assert result == "result"
        
        # 检查是否记录了计时
        monitor = get_performance_monitor()
        stats = monitor.get_operation_stats("decorated_function")
        
        assert stats["count"] >= 1
        assert stats["average_time"] >= 0.09


class TestSessionCache:
    """会话缓存性能测试"""
    
    def test_session_cache_performance(self):
        """测试会话缓存性能"""
        cache = SessionCache(max_sessions=1000, session_ttl_seconds=3600)
        
        # 测试会话存储性能
        start_time = time.time()
        for i in range(1000):
            session_data = {
                "user_id": f"user_{i}",
                "messages": [f"message_{j}" for j in range(10)],
                "created_at": time.time()
            }
            cache.put_session(f"session_{i}", session_data)
        store_time = time.time() - start_time
        
        # 测试会话检索性能
        start_time = time.time()
        for i in range(1000):
            session = cache.get_session(f"session_{i}")
            assert session is not None
        retrieve_time = time.time() - start_time
        
        print(f"存储1检索1000个会话耗时: 秒秒{store_time:.4f})
        print(f"检检索1000个会话耗时: 秒{retrieve_time:.4f})
        
        # 性能断言
        assert store_time < 1.0
        assert retrieve_time < 0.5
        
        # 检查统计信息息
        stats = cache.get_stats()
        assert stats["size"] == 1000
    
    def test_concurrent_session_access(self):
        """测试并发会话访问"""
        cache = SessionCache(max_sessions=1000)
        
        def session_worker(start_idx: int, count: int):
            for i in range(start_idx, start_idx + count):
                session_data = {"data": f"session_{i}"}
                cache.put_session(f"session_{i}", session_data)
                
                # 立即读取
                retrieved = cache.get_session(f"session_{i}")
                assert retrieved is not None
        
        # 启动多个并发工作线程
        threads = []
        start_time = time.time()
        
        for i in range(4):
            thread = threading.Thread(target=session_worker, args=(i * 100, 100))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        
        print(f"并发处理400个会话耗时: 秒{concurrent_time:.4f})
        
        # 并发性能断言
        assert concurrent_time < 2.0
        
        # 验证所有会话都存在
        stats = cache.get_stats()
        assert stats["size"] == 400


class TestCacheManager:
    """缓存管理器集成性能测试"""
    
    def test_integrated_cache_performance(self):
        """测试集成缓存性能"""
        manager = get_cache_manager()
        
        # 测试TTS缓存
        tts_cache = manager.get_tts_cache()
        audio_data = b"test_audio" * 1000
        
        start_time = time.time()
        for i in range(100):
            tts_cache.put(f"text_{i}", "voice", audio_data)
        tts_store_time = time.time() - start_time
        
        # 测试会话缓存
        session_cache = manager.get_session_cache()
        
        start_time = time.time()
        for i in range(100):
            session_data = {"messages": [f"msg_{j}" for j in range(5)]}
            session_cache.put_session(f"session_{i}", session_data)
        session_store_time = time.time() - start_time
        
        print(f"TTS缓存存储耗时: 秒{tts_store_time:.4f})
        print(f"会话缓存存储耗时: 秒{session_store_time:.4f})
        
        # 获取整体统计
        overall_stats = manager.get_overall_stats()
        
        assert "tts" in overall_stats
        assert "session" in overall_stats
        
        # 性能断言
        assert tts_store_time < 2.0
        assert session_store_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])








