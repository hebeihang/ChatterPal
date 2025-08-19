# -*- coding: utf-8 -*-
"""
缓存管理系统
提供TTS结果缓存、会话数据缓存等功能
"""

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import logging
from collections import OrderedDict

from ..config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        """更新访问时间和计数"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        """
        初始化LRU缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 生存时间（秒），None表示永不过期
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _calculate_size(self, value: Any) -> int:
        """计算值的大小（字节）"""
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (int, float)):
                return 8
            else:
                # 使用pickle序列化来估算大小
                return len(pickle.dumps(value))
        except Exception:
            return 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if entry.is_expired():
                del self._cache[key]
                return None
            
            # 更新访问信息
            entry.touch()
            
            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            
            return entry.value
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            # 计算过期时间
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            elif self.ttl_seconds is not None:
                expires_at = datetime.now() + timedelta(seconds=self.ttl_seconds)
            
            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=self._calculate_size(value)
            )
            
            # 如果键已存在，更新
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
            else:
                # 检查是否需要清理空间
                while len(self._cache) >= self.max_size:
                    self._evict_oldest()
                
                self._cache[key] = entry
    
    def _evict_oldest(self) -> None:
        """清理最旧的条目"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_size = sum(entry.size_bytes for entry in self._cache.values())
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_size_bytes": total_size,
                "hit_rate": self._calculate_hit_rate(),
                "oldest_entry": min(
                    (entry.created_at for entry in self._cache.values()),
                    default=None
                ),
                "newest_entry": max(
                    (entry.created_at for entry in self._cache.values()),
                    default=None
                )
            }
    
    def _calculate_hit_rate(self) -> float:
        """计算缓存命中率"""
        if not self._cache:
            return 0.0
        
        total_accesses = sum(entry.access_count for entry in self._cache.values())
        if total_accesses == 0:
            return 0.0
        
        return len(self._cache) / total_accesses


class TTSCache:
    """TTS结果缓存"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_memory_size: int = 100, 
                 max_disk_size_mb: int = 500):
        """
        初始化TTS缓存
        
        Args:
            cache_dir: 磁盘缓存目录
            max_memory_size: 内存缓存最大条目数
            max_disk_size_mb: 磁盘缓存最大大小（MB）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 内存缓存
        self._memory_cache = LRUCache(max_size=max_memory_size, ttl_seconds=3600)
        
        # 磁盘缓存设置
        if cache_dir is None:
            settings = get_settings()
            self.cache_dir = settings.get_cache_path() / "tts"
        else:
            self.cache_dir = Path(cache_dir)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_disk_size_bytes = max_disk_size_mb * 1024 * 1024
        
        # 统计信息
        self._stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "stores": 0
        }
    
    def _generate_cache_key(self, text: str, voice: str, rate: str = "+0%", 
                          volume: str = "+0%") -> str:
        """生成缓存键"""
        content = f"{text}|{voice}|{rate}|{volume}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_disk_cache_path(self, cache_key: str) -> Path:
        """获取磁盘缓存文件路径"""
        return self.cache_dir / f"{cache_key}.wav"
    
    def get(self, text: str, voice: str, rate: str = "+0%", 
            volume: str = "+0%") -> Optional[bytes]:
        """
        获取TTS缓存结果
        
        Args:
            text: 要合成的文本
            voice: 语音
            rate: 语速
            volume: 音量
            
        Returns:
            音频数据（字节），如果未找到返回None
        """
        cache_key = self._generate_cache_key(text, voice, rate, volume)
        
        # 先检查内存缓存
        audio_data = self._memory_cache.get(cache_key)
        if audio_data is not None:
            self._stats["memory_hits"] += 1
            return audio_data
        
        # 检查磁盘缓存
        disk_path = self._get_disk_cache_path(cache_key)
        if disk_path.exists():
            try:
                with open(disk_path, 'rb') as f:
                    audio_data = f.read()
                
                # 将结果放入内存缓存
                self._memory_cache.put(cache_key, audio_data)
                self._stats["disk_hits"] += 1
                return audio_data
                
            except Exception as e:
                self.logger.error(f"读取磁盘缓存失败: {e}")
        
        self._stats["misses"] += 1
        return None
    
    def put(self, text: str, voice: str, audio_data: bytes, 
            rate: str = "+0%", volume: str = "+0%") -> None:
        """
        存储TTS结果到缓存
        
        Args:
            text: 合成的文本
            voice: 语音
            audio_data: 音频数据
            rate: 语速
            volume: 音量
        """
        cache_key = self._generate_cache_key(text, voice, rate, volume)
        
        try:
            # 存储到内存缓存
            self._memory_cache.put(cache_key, audio_data)
            
            # 存储到磁盘缓存
            disk_path = self._get_disk_cache_path(cache_key)
            with open(disk_path, 'wb') as f:
                f.write(audio_data)
            
            self._stats["stores"] += 1
            
            # 检查磁盘缓存大小
            self._cleanup_disk_cache()
            
        except Exception as e:
            self.logger.error(f"存储TTS缓存失败: {e}")
    
    def _cleanup_disk_cache(self) -> None:
        """清理磁盘缓存"""
        try:
            # 获取所有缓存文件
            cache_files = list(self.cache_dir.glob("*.wav"))
            
            # 计算总大小
            total_size = sum(f.stat().st_size for f in cache_files)
            
            if total_size <= self.max_disk_size_bytes:
                return
            
            # 按修改时间排序，删除最旧的文件
            cache_files.sort(key=lambda x: x.stat().st_mtime)
            
            while total_size > self.max_disk_size_bytes and cache_files:
                oldest_file = cache_files.pop(0)
                file_size = oldest_file.stat().st_size
                oldest_file.unlink()
                total_size -= file_size
                
        except Exception as e:
            self.logger.error(f"清理磁盘缓存失败: {e}")
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._memory_cache.clear()
        
        try:
            for cache_file in self.cache_dir.glob("*.wav"):
                cache_file.unlink()
        except Exception as e:
            self.logger.error(f"清空磁盘缓存失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_stats = self._memory_cache.get_stats()
        
        # 计算磁盘缓存统计
        try:
            disk_files = list(self.cache_dir.glob("*.wav"))
            disk_size = sum(f.stat().st_size for f in disk_files)
            disk_count = len(disk_files)
        except Exception:
            disk_size = 0
            disk_count = 0
        
        total_requests = sum(self._stats.values()) - self._stats["stores"]
        hit_rate = 0.0
        if total_requests > 0:
            hits = self._stats["memory_hits"] + self._stats["disk_hits"]
            hit_rate = hits / total_requests
        
        return {
            "memory": memory_stats,
            "disk": {
                "count": disk_count,
                "size_bytes": disk_size,
                "max_size_bytes": self.max_disk_size_bytes
            },
            "stats": self._stats.copy(),
            "hit_rate": hit_rate
        }


class SessionCache:
    """会话数据缓存"""
    
    def __init__(self, max_sessions: int = 100, session_ttl_seconds: int = 3600):
        """
        初始化会话缓存
        
        Args:
            max_sessions: 最大会话数
            session_ttl_seconds: 会话生存时间（秒）
        """
        self._cache = LRUCache(max_size=max_sessions, ttl_seconds=session_ttl_seconds)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        return self._cache.get(session_id)
    
    def put_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """存储会话数据"""
        self._cache.put(session_id, session_data)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """更新会话数据"""
        session_data = self._cache.get(session_id)
        if session_data is None:
            return False
        
        session_data.update(updates)
        self._cache.put(session_id, session_data)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        return self._cache.delete(session_id)
    
    def cleanup_expired(self) -> int:
        """清理过期会话"""
        return self._cache.cleanup_expired()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话缓存统计"""
        return self._cache.get_stats()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化各种缓存
        self.tts_cache = TTSCache()
        self.session_cache = SessionCache()
        
        # 启动清理任务
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """启动定期清理任务"""
        def cleanup_task():
            while True:
                try:
                    # 清理过期的会话
                    expired_sessions = self.session_cache.cleanup_expired()
                    if expired_sessions > 0:
                        self.logger.info(f"清理了 {expired_sessions} 个过期会话")
                    
                    # 等待5分钟后再次清理
                    time.sleep(300)
                    
                except Exception as e:
                    self.logger.error(f"缓存清理任务出错: {e}")
                    time.sleep(60)  # 出错后等待1分钟
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def get_tts_cache(self) -> TTSCache:
        """获取TTS缓存"""
        return self.tts_cache
    
    def get_session_cache(self) -> SessionCache:
        """获取会话缓存"""
        return self.session_cache
    
    def clear_all_caches(self) -> None:
        """清空所有缓存"""
        self.tts_cache.clear()
        self.session_cache._cache.clear()
        self.logger.info("已清空所有缓存")
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """获取整体缓存统计"""
        return {
            "tts": self.tts_cache.get_stats(),
            "session": self.session_cache.get_stats()
        }


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    获取全局缓存管理器实例
    
    Returns:
        缓存管理器实例
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager


def get_tts_cache() -> TTSCache:
    """
    获取TTS缓存的便捷函数
    
    Returns:
        TTS缓存实例
    """
    return get_cache_manager().get_tts_cache()


def get_session_cache() -> SessionCache:
    """
    获取会话缓存的便捷函数
    
    Returns:
        会话缓存实例
    """
    return get_cache_manager().get_session_cache()


def get_chat_cache() -> SessionCache:
    """
    获取聊天缓存的便捷函数（会话缓存的别名）
    
    Returns:
        会话缓存实例
    """
    return get_session_cache()