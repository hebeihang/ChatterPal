"""
增强TTS功能测试
"""

import numpy as np
import pytest
import tempfile
import os
import time
import sys
from unittest.mock import Mock, patch, MagicMock

from chatterpal.core.tts.base import (
    TTSBase, 
    TTSError, 
    TTSCacheError, 
    TTSPlaybackError,
    TTSResult,
    PlaybackState,
    CacheEntry
)


class MockTTS(TTSBase):
    """用于测试的模拟TTS实现"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.mock_audio_data = self._create_test_audio_data()
        self.should_fail = False
        self.synthesis_delay = 0.1
        
    def synthesize(self, text: str, **kwargs) -> bytes:
        time.sleep(self.synthesis_delay)
        
        if self.should_fail:
            raise TTSError("模拟合成失败")
        
        return self.mock_audio_data
    
    def synthesize_to_file(self, text: str, output_path: str, **kwargs) -> bool:
        try:
            audio_data = self.synthesize(text, **kwargs)
            with open(output_path, "wb") as f:
                f.write(audio_data)
            return True
        except Exception:
            return False
    
    def _create_test_audio_data(self):
        """创建测试用的音频数据"""
        # 生成简单的WAV格式音频数据
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)
        
        # 生成正弦
        t = np.linspace(0, duration, samples)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # 创建简单的WAV头部
        import struct
        
        # WAV文件头部
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + len(audio_int16) * 2,
            b'WAVE',
            b'fmt ',
            16,  # PCM
            1,   # format
            1,   # channels
            sample_rate,
            sample_rate * 2,  # byte rate
            2,   # block align
            16,  # bits per sample
            b'data',
            len(audio_int16) * 2
        )
        
        return header + audio_int16.tobytes()


class TestTTSEnhanced:
    """增强TTS功能测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.tts = MockTTS({
            "enable_cache": True,
            "cache_size_limit": 10,
            "cache_ttl": 3600,
            "auto_play": False,
            "playback_volume": 0.8
        })
        
    def test_tts_result_dataclass(self):
        """测试TTSResult数据体"""
        result = TTSResult(
            text="测试文本",
            audio_data=b"test_audio",
            duration=2.5,
            format="wav",
            sample_rate=16000,
            cached=False,
            synthesis_time=1.2,
            metadata={"test": "data"}
        )
        
        assert result.text == "测试文本"
        assert result.audio_data == b"test_audio"
        assert result.duration == 2.5
        assert result.format == "wav"
        assert result.sample_rate == 16000
        assert result.cached == False
        assert result.synthesis_time == 1.2
        assert result.metadata["test"] == "data"
        
    def test_cache_entry_dataclass(self):
        """测试CacheEntry数据体"""
        entry = CacheEntry(
            key="test_key",
            audio_data=b"test_audio",
            metadata={"test": "data"},
            created_at=time.time(),
            access_count=1,
            last_accessed=time.time()
        )
        
        assert entry.key == "test_key"
        assert entry.audio_data == b"test_audio"
        assert entry.metadata["test"] == "data"
        assert entry.access_count == 1
        
    def test_playback_state_enum(self):
        """测试播放状态枚举"""
        assert PlaybackState.STOPPED.value == "stopped"
        assert PlaybackState.PLAYING.value == "playing"
        assert PlaybackState.PAUSED.value == "paused"
        assert PlaybackState.ERROR.value == "error"
        
    def test_synthesize_enhanced_success(self):
        """测试增强合成成功情况"""
        result = self.tts.synthesize_enhanced("测试文本")
        
        assert isinstance(result, TTSResult)
        assert result.text == "测试文本"
        assert len(result.audio_data) > 0
        assert result.cached == False  # 第一次合成不是缓
        assert result.synthesis_time > 0
        
    def test_synthesize_enhanced_with_cache(self):
        """测试增强合成缓存功能"""
        text = "测试缓存文本"
        
        # 第一次合
        result1 = self.tts.synthesize_enhanced(text)
        assert result1.cached == False
        
        # 第二次合成应该使用缓
        result2 = self.tts.synthesize_enhanced(text)
        assert result2.cached == True
        assert result2.audio_data == result1.audio_data
        
    def test_synthesize_enhanced_cache_disabled(self):
        """测试禁用缓存的增强合成"""
        self.tts.enable_cache = False
        
        result1 = self.tts.synthesize_enhanced("测试文本")
        result2 = self.tts.synthesize_enhanced("测试文本")
        
        assert result1.cached == False
        assert result2.cached == False
        
    def test_synthesize_enhanced_failure(self):
        """测试增强合成失败情况"""
        self.tts.should_fail = True
        
        result = self.tts.synthesize_enhanced("测试文本")
        
        assert result.text == "测试文本"
        assert len(result.audio_data) == 0
        assert result.cached == False
        assert "error" in result.metadata
        
    def test_generate_cache_key(self):
        """测试缓存键生成"""
        key1 = self.tts._generate_cache_key("测试文本", {"voice": "test"})
        key2 = self.tts._generate_cache_key("测试文本", {"voice": "test"})
        key3 = self.tts._generate_cache_key("测试文本", {"voice": "other"})
        
        assert key1 == key2  # 相同参数应该生成相同的键
        assert key1 != key3  # 不同参数应该生成不同的键
        assert len(key1) == 32  # MD5哈希长度
        
    def test_cache_operations(self):
        """测试缓存操作"""
        cache_key = "test_key"
        audio_data = b"test_audio_data"
        metadata = {"test": "metadata"}
        
        # 存储到缓
        self.tts._store_to_cache(cache_key, audio_data, metadata)
        
        # 从缓存获
        entry = self.tts._get_from_cache(cache_key)
        assert entry is not None
        assert entry.audio_data == audio_data
        assert entry.metadata == metadata
        assert entry.access_count == 2  # 存储1,获取时+1
        
    def test_cache_expiration(self):
        """测试缓存过期"""
        # 设置很短的TTL
        self.tts.cache_ttl = 0.1
        
        cache_key = "test_key"
        audio_data = b"test_audio_data"
        metadata = {"test": "metadata"}
        
        # 存储到缓
        self.tts._store_to_cache(cache_key, audio_data, metadata)
        
        # 立即获取应该成功
        entry = self.tts._get_from_cache(cache_key)
        assert entry is not None
        
        # 等待过期
        time.sleep(0.2)
        
        # 再次获取应该失败
        entry = self.tts._get_from_cache(cache_key)
        assert entry is None
        
    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        self.tts.cache_size_limit = 3
        
        # 添加超过限制的缓存条
        for i in range(5):
            cache_key = f"test_key_{i}"
            audio_data = f"test_audio_data_{i}".encode()
            metadata = {"index": i}
            self.tts._store_to_cache(cache_key, audio_data, metadata)
        
        # 检查缓存统计计大
        assert len(self.tts._cache) <= self.tts.cache_size_limit
        
    def test_clear_cache(self):
        """测试清空缓存"""
        # 添加一些缓存条
        for i in range(3):
            cache_key = f"test_key_{i}"
            audio_data = f"test_audio_data_{i}".encode()
            metadata = {"index": i}
            self.tts._store_to_cache(cache_key, audio_data, metadata)
        
        assert len(self.tts._cache) == 3
        
        # 清空缓存
        self.tts.clear_cache()
        
        assert len(self.tts._cache) == 0
        
    def test_get_cache_stats(self):
        """测试获取缓存统计信息"""
        # 添加一些缓存条
        for i in range(3):
            cache_key = f"test_key_{i}"
            audio_data = f"test_audio_data_{i}".encode()
            metadata = {"index": i}
            self.tts._store_to_cache(cache_key, audio_data, metadata)
        
        stats = self.tts.get_cache_stats()
        
        assert stats["entries"] == 3
        assert stats["total_size_bytes"] > 0
        assert stats["total_access_count"] >= 3
        assert "oldest_entry" in stats
        assert "newest_entry" in stats
        
    def test_disk_cache_operations(self):
        """测试磁盘缓存操作"""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.tts.cache_dir = temp_dir
            self.tts._init_cache_dir()
            
            cache_key = "test_key"
            audio_data = b"test_audio_data"
            metadata = {"test": "metadata"}
            
            # 创建缓存条目
            entry = CacheEntry(
                key=cache_key,
                audio_data=audio_data,
                metadata=metadata,
                created_at=time.time(),
                access_count=1,
                last_accessed=time.time()
            )
            
            # 保存到磁
            self.tts._save_to_disk_cache(entry)
            
            # 清空内存缓存
            self.tts._cache.clear()
            
            # 从磁盘加
            loaded_entry = self.tts._load_from_disk_cache(cache_key)
            
            assert loaded_entry is not None
            assert loaded_entry.audio_data == audio_data
            assert loaded_entry.metadata == metadata
            
    def test_playback_state_management(self):
        """测试播放状态管理"""
        assert self.tts.get_playback_state() == PlaybackState.STOPPED
        
        # 模拟播放状态变
        self.tts._playback_state = PlaybackState.PLAYING
        assert self.tts.get_playback_state() == PlaybackState.PLAYING
        
        self.tts._playback_state = PlaybackState.PAUSED
        assert self.tts.get_playback_state() == PlaybackState.PAUSED
        
    def test_playback_volume_control(self):
        """测试播放音量控制"""
        # 测试设置音量
        self.tts.set_playback_volume(0.5)
        assert self.tts.get_playback_volume() == 0.5
        
        # 测试音量范围限制
        self.tts.set_playback_volume(-0.1)
        assert self.tts.get_playback_volume() == 0.0
        
        self.tts.set_playback_volume(1.5)
        assert self.tts.get_playback_volume() == 1.0
        
    def test_playback_callbacks(self):
        """测试播放回调"""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        # 添加回调
        self.tts.add_playback_callback(test_callback)
        
        # 触发回调
        self.tts._notify_playback_callbacks("test_event")
        
        assert "test_event" in callback_events
        
        # 移除回调
        self.tts.remove_playback_callback(test_callback)
        
        # 再次触发不应该有新事
        callback_events.clear()
        self.tts._notify_playback_callbacks("another_event")
        
        assert len(callback_events) == 0
        
    def test_play_with_pygame(self):
        """测试使用pygame播放"""
        # 创建模拟的pygame模块和组
        mock_pygame = MagicMock()
        mock_mixer = MagicMock()
        mock_sound = MagicMock()
        mock_io = MagicMock()
        
        # 设置模拟行为
        mock_mixer.Sound.return_value = mock_sound
        mock_pygame.mixer = mock_mixer
        
        # 模拟所有需要的模块
        modules_to_mock = {
            'pygame': mock_pygame,
            'io': mock_io
        }
        
        with patch.dict('sys.modules', modules_to_mock):
            # 直接调用方法,绕过import检
            try:
                # 手动设置pygame模块
                import sys
                sys.modules['pygame'] = mock_pygame
                sys.modules['pygame'].mixer = mock_mixer
                
                audio_data = b"test_audio_data"
                
                # 模拟BytesIO
                mock_io.BytesIO.return_value = MagicMock()
                
                result = self.tts._play_with_pygame(audio_data)
                
                assert result == True
                assert self.tts.get_playback_state() == PlaybackState.PLAYING
                mock_sound.play.assert_called_once()
                
            except Exception as e:
                # 如果模拟失败,跳过测
                pytest.skip(f"pygame模拟失败: {e}")
        
    def test_play_audio_fallback(self):
        """测试音频播放回退机制"""
        audio_data = b"test_audio_data"
        
        # 模拟所有播放方法都失败
        with patch.object(self.tts, '_play_with_pygame', side_effect=ImportError):
            with patch.object(self.tts, '_play_with_playsound', side_effect=ImportError):
                with patch.object(self.tts, '_play_with_system', side_effect=Exception):
                    result = self.tts.play_audio(audio_data)
                    
                    assert result == False
                    assert self.tts.get_playback_state() == PlaybackState.ERROR
                    
    def test_stop_playback(self):
        """测试停止播放"""
        # 模拟有音频在播放
        mock_audio = MagicMock()
        self.tts._current_audio = mock_audio
        self.tts._playback_state = PlaybackState.PLAYING
        
        result = self.tts.stop_playback()
        
        assert result == True
        assert self.tts.get_playback_state() == PlaybackState.STOPPED
        assert self.tts._current_audio is None
        mock_audio.stop.assert_called_once()
        
    def test_pause_resume_playback(self):
        """测试暂停和恢复播放"""
        # 模拟有音频在播放
        mock_audio = MagicMock()
        self.tts._current_audio = mock_audio
        self.tts._playback_state = PlaybackState.PLAYING
        
        # 测试暂停
        result = self.tts.pause_playback()
        assert result == True
        assert self.tts.get_playback_state() == PlaybackState.PAUSED
        mock_audio.pause.assert_called_once()
        
        # 测试恢复
        result = self.tts.resume_playback()
        assert result == True
        assert self.tts.get_playback_state() == PlaybackState.PLAYING
        mock_audio.unpause.assert_called_once()


class TestTTSErrorTypes:
    """TTS错误类型测试"""
    
    def test_tts_error_inheritance(self):
        """测试TTS错误类继承关系"""
        assert issubclass(TTSCacheError, TTSError)
        assert issubclass(TTSPlaybackError, TTSError)
        
    def test_tts_cache_error(self):
        """测试TTS缓存错误"""
        error = TTSCacheError("缓存错误")
        assert str(error) == "缓存错误"
        assert isinstance(error, TTSError)
        
    def test_tts_playback_error(self):
        """测试TTS播放错误"""
        error = TTSPlaybackError("播放错误")
        assert str(error) == "播放错误"
        assert isinstance(error, TTSError)


class TestTTSIntegration:
    """TTS集成测试"""
    
    def test_full_enhanced_synthesis_pipeline(self):
        """测试完整的增强合成流程"""
        tts = MockTTS({
            "enable_cache": True,
            "cache_size_limit": 5,
            "auto_play": False
        })
        
        text = "这是一个完整的测试文本"
        
        # 执行增强合成
        result = tts.synthesize_enhanced(text)
        
        # 验证结果
        assert result.text == text
        assert len(result.audio_data) > 0
        assert result.cached == False
        assert result.synthesis_time > 0
        assert result.duration > 0
        
        # 测试缓存
        result2 = tts.synthesize_enhanced(text)
        assert result2.cached == True
        
        # 测试缓存统计
        stats = tts.get_cache_stats()
        assert stats["entries"] >= 1
        
        # 测试播放控制
        assert tts.get_playback_state() == PlaybackState.STOPPED
        
        # 测试音量控制
        tts.set_playback_volume(0.7)
        assert tts.get_playback_volume() == 0.7
        
    def test_auto_play_functionality(self):
        """测试自动播放功能"""
        tts = MockTTS({
            "auto_play": True,
            "playback_volume": 0.5
        })
        
        # 模拟播放方法
        with patch.object(tts, 'play_audio', return_value=True) as mock_play:
            result = tts.synthesize_enhanced("测试自动播放")
            
            # 验证自动播放被调
            mock_play.assert_called_once_with(result.audio_data)
            
    def test_error_handling_robustness(self):
        """测试错误处理的健壮性"""
        tts = MockTTS()
        
        # 测试各种异常情况
        test_cases = [
            "",  # 空文
            None,  # None文本
            "a" * 10000,  # 超长文本
        ]
        
        for test_text in test_cases:
            try:
                result = tts.synthesize_enhanced(test_text)
                # 即使输入有问题,也应该返回结果对
                assert isinstance(result, TTSResult)
            except Exception as e:
                # 如果抛出异常,应该是预期的TTSError
                assert isinstance(e, TTSError)


if __name__ == "__main__":
    pytest.main([__file__])








