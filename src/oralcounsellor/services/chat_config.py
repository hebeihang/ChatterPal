# -*- coding: utf-8 -*-
"""
聊天模块配置管理系统
提供聊天模块专用的配置管理功能，包括音频设置、主题生成、会话管理等
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

from ..config.settings import get_settings
from ..utils.preferences import get_preferences_manager


logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """音频配置"""
    max_recording_duration: int = 60  # 最大录音时长（秒）
    min_recording_duration: int = 1   # 最小录音时长（秒）
    sample_rate: int = 16000          # 采样率
    format: str = "wav"               # 音频格式
    auto_play: bool = True            # 自动播放回复
    playback_speed: float = 1.0       # 播放速度
    volume: float = 0.8               # 音量
    noise_threshold: float = 0.1      # 噪音阈值
    
    def validate(self) -> bool:
        """验证音频配置"""
        if self.max_recording_duration <= 0 or self.max_recording_duration > 300:
            return False
        if self.min_recording_duration <= 0 or self.min_recording_duration >= self.max_recording_duration:
            return False
        if self.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            return False
        if self.format not in ["wav", "mp3", "flac"]:
            return False
        if not (0.1 <= self.playback_speed <= 3.0):
            return False
        if not (0.0 <= self.volume <= 1.0):
            return False
        return True


@dataclass
class TopicGenerationConfig:
    """主题生成配置"""
    difficulty_levels: List[str] = field(default_factory=lambda: ["beginner", "intermediate", "advanced"])
    categories: List[str] = field(default_factory=lambda: ["daily", "hobby", "travel", "work", "tech", "culture"])
    max_retries: int = 3              # 最大重试次数
    default_difficulty: str = "intermediate"  # 默认难度
    preferred_categories: List[str] = field(default_factory=list)  # 用户偏好分类
    auto_generate: bool = False       # 自动生成主题
    context_aware: bool = True        # 基于上下文生成
    
    def validate(self) -> bool:
        """验证主题生成配置"""
        if self.default_difficulty not in self.difficulty_levels:
            return False
        if self.max_retries <= 0 or self.max_retries > 10:
            return False
        for category in self.preferred_categories:
            if category not in self.categories:
                return False
        return True


@dataclass  
class SessionConfig:
    """会话配置"""
    max_history_length: int = 50      # 最大历史记录长度
    session_timeout: int = 3600       # 会话超时时间（秒）
    auto_save: bool = True            # 自动保存
    save_interval: int = 300          # 保存间隔（秒）
    max_sessions: int = 100           # 最大会话数量
    cleanup_interval: int = 86400     # 清理间隔（秒）
    
    def validate(self) -> bool:
        """验证会话配置"""
        if self.max_history_length <= 0 or self.max_history_length > 1000:
            return False
        if self.session_timeout <= 0 or self.session_timeout > 86400:
            return False
        if self.save_interval <= 0 or self.save_interval > 3600:
            return False
        if self.max_sessions <= 0 or self.max_sessions > 1000:
            return False
        return True


@dataclass
class UIConfig:
    """用户界面配置"""
    default_input_mode: str = "text"  # 默认输入模式
    show_history: bool = False        # 显示历史记录
    compact_mode: bool = False        # 紧凑模式
    theme: str = "default"            # 主题
    language: str = "zh-CN"           # 语言
    auto_scroll: bool = True          # 自动滚动
    
    def validate(self) -> bool:
        """验证UI配置"""
        if self.default_input_mode not in ["text", "voice"]:
            return False
        if self.theme not in ["default", "dark", "light"]:
            return False
        if self.language not in ["zh-CN", "en-US"]:
            return False
        return True


@dataclass
class ChatModuleConfig:
    """聊天模块完整配置"""
    audio: AudioConfig = field(default_factory=AudioConfig)
    topic_generation: TopicGenerationConfig = field(default_factory=TopicGenerationConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    version: str = "1.0.0"
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def validate(self) -> bool:
        """验证所有配置"""
        return (
            self.audio.validate() and
            self.topic_generation.validate() and
            self.session.validate() and
            self.ui.validate()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatModuleConfig':
        """从字典创建配置"""
        return cls(
            audio=AudioConfig(**data.get('audio', {})),
            topic_generation=TopicGenerationConfig(**data.get('topic_generation', {})),
            session=SessionConfig(**data.get('session', {})),
            ui=UIConfig(**data.get('ui', {})),
            version=data.get('version', '1.0.0'),
            last_updated=data.get('last_updated', datetime.now().isoformat())
        )


class ChatConfigManager:
    """聊天模块配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认使用系统配置目录
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if config_dir is None:
            # 使用系统配置目录
            settings = get_settings()
            self.config_dir = Path(settings.get_cache_path()) / "chat_config"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_file = self.config_dir / "chat_config.json"
        self.backup_dir = self.config_dir / "backups"
        
        # 确保目录存在
        self._ensure_directories()
        
        # 加载配置
        self._config = self._load_config()
        
        # 获取用户偏好管理器
        self.preferences = get_preferences_manager()
    
    def _ensure_directories(self) -> None:
        """确保配置目录存在"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建配置目录失败: {e}")
            raise    

    def _load_config(self) -> ChatModuleConfig:
        """
        加载配置文件
        
        Returns:
            聊天模块配置
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                config = ChatModuleConfig.from_dict(data)
                
                # 验证配置
                if not config.validate():
                    self.logger.warning("配置验证失败，使用默认配置")
                    config = ChatModuleConfig()
                
                self.logger.info(f"成功加载聊天模块配置: {self.config_file}")
                return config
            else:
                self.logger.info("配置文件不存在，创建默认配置")
                config = ChatModuleConfig()
                self._save_config(config)
                return config
                
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return ChatModuleConfig()
    
    def _save_config(self, config: Optional[ChatModuleConfig] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置，默认使用当前配置
            
        Returns:
            是否保存成功
        """
        if config is None:
            config = self._config
        
        try:
            # 更新时间戳
            config.last_updated = datetime.now().isoformat()
            
            # 创建备份
            self._create_backup()
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"成功保存聊天模块配置: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def _create_backup(self) -> None:
        """创建配置文件备份"""
        try:
            if self.config_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"chat_config_{timestamp}.json"
                
                import shutil
                shutil.copy2(self.config_file, backup_file)
                
                # 清理旧备份（保留最近10个）
                self._cleanup_backups()
                
        except Exception as e:
            self.logger.warning(f"创建备份失败: {e}")
    
    def _cleanup_backups(self, keep_count: int = 10) -> None:
        """清理旧备份文件"""
        try:
            backup_files = list(self.backup_dir.glob("chat_config_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 删除多余的备份
            for backup_file in backup_files[keep_count:]:
                backup_file.unlink()
                
        except Exception as e:
            self.logger.warning(f"清理备份失败: {e}")
    
    def get_config(self) -> ChatModuleConfig:
        """
        获取当前配置
        
        Returns:
            聊天模块配置
        """
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            updates: 要更新的配置项
            
        Returns:
            是否更新成功
        """
        try:
            # 深度合并配置
            config_dict = self._config.to_dict()
            config_dict = self._deep_merge(config_dict, updates)
            
            # 创建新配置
            new_config = ChatModuleConfig.from_dict(config_dict)
            
            # 验证配置
            if not new_config.validate():
                self.logger.error("更新后的配置验证失败")
                return False
            
            # 保存配置
            self._config = new_config
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False 
   
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并字典
        
        Args:
            base: 基础字典
            updates: 更新字典
            
        Returns:
            合并后的字典
        """
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_audio_config(self) -> AudioConfig:
        """获取音频配置"""
        return self._config.audio
    
    def update_audio_config(self, **kwargs) -> bool:
        """更新音频配置"""
        return self.update_config({"audio": kwargs})
    
    def get_topic_config(self) -> TopicGenerationConfig:
        """获取主题生成配置"""
        return self._config.topic_generation
    
    def update_topic_config(self, **kwargs) -> bool:
        """更新主题生成配置"""
        return self.update_config({"topic_generation": kwargs})
    
    def get_session_config(self) -> SessionConfig:
        """获取会话配置"""
        return self._config.session
    
    def update_session_config(self, **kwargs) -> bool:
        """更新会话配置"""
        return self.update_config({"session": kwargs})
    
    def get_ui_config(self) -> UIConfig:
        """获取UI配置"""
        return self._config.ui
    
    def update_ui_config(self, **kwargs) -> bool:
        """更新UI配置"""
        return self.update_config({"ui": kwargs})
    
    def sync_with_user_preferences(self) -> bool:
        """
        与用户偏好设置同步
        
        Returns:
            是否同步成功
        """
        try:
            # 从用户偏好获取设置
            chat_prefs = self.preferences.get_chat_preferences()
            audio_prefs = self.preferences.get_audio_preferences()
            topic_prefs = self.preferences.get_topic_preferences()
            
            # 构建更新字典
            updates = {}
            
            # 同步音频设置
            if audio_prefs:
                audio_updates = {}
                if "auto_play" in audio_prefs:
                    audio_updates["auto_play"] = audio_prefs["auto_play"]
                if "playback_speed" in audio_prefs:
                    audio_updates["playback_speed"] = audio_prefs["playback_speed"]
                if "volume" in audio_prefs:
                    audio_updates["volume"] = audio_prefs["volume"]
                
                if audio_updates:
                    updates["audio"] = audio_updates
            
            # 同步聊天设置
            if chat_prefs:
                ui_updates = {}
                session_updates = {}
                
                if "input_mode" in chat_prefs:
                    ui_updates["default_input_mode"] = chat_prefs["input_mode"]
                if "show_history" in chat_prefs:
                    ui_updates["show_history"] = chat_prefs["show_history"]
                if "auto_play_response" in chat_prefs:
                    if "audio" not in updates:
                        updates["audio"] = {}
                    updates["audio"]["auto_play"] = chat_prefs["auto_play_response"]
                
                if ui_updates:
                    updates["ui"] = ui_updates
                if session_updates:
                    updates["session"] = session_updates
            
            # 同步主题设置
            if topic_prefs:
                topic_updates = {}
                if "difficulty" in topic_prefs:
                    topic_updates["default_difficulty"] = topic_prefs["difficulty"]
                if "preferred_categories" in topic_prefs:
                    topic_updates["preferred_categories"] = topic_prefs["preferred_categories"]
                if "auto_generate" in topic_prefs:
                    topic_updates["auto_generate"] = topic_prefs["auto_generate"]
                
                if topic_updates:
                    updates["topic_generation"] = topic_updates
            
            # 应用更新
            if updates:
                return self.update_config(updates)
            
            return True
            
        except Exception as e:
            self.logger.error(f"同步用户偏好失败: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            是否重置成功
        """
        try:
            self._config = ChatModuleConfig()
            return self._save_config()
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"成功导出配置到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        从文件导入配置
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            是否导入成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = ChatModuleConfig.from_dict(data)
            
            if not config.validate():
                self.logger.error("导入的配置验证失败")
                return False
            
            self._config = config
            success = self._save_config()
            
            if success:
                self.logger.info(f"成功导入配置从: {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            配置摘要字典
        """
        return {
            "version": self._config.version,
            "last_updated": self._config.last_updated,
            "audio": {
                "max_duration": self._config.audio.max_recording_duration,
                "sample_rate": self._config.audio.sample_rate,
                "auto_play": self._config.audio.auto_play
            },
            "topic": {
                "default_difficulty": self._config.topic_generation.default_difficulty,
                "categories_count": len(self._config.topic_generation.categories),
                "auto_generate": self._config.topic_generation.auto_generate
            },
            "session": {
                "max_history": self._config.session.max_history_length,
                "timeout": self._config.session.session_timeout,
                "auto_save": self._config.session.auto_save
            },
            "ui": {
                "input_mode": self._config.ui.default_input_mode,
                "show_history": self._config.ui.show_history,
                "language": self._config.ui.language
            }
        }


# 全局配置管理器实例
_chat_config_manager: Optional[ChatConfigManager] = None


def get_chat_config_manager() -> ChatConfigManager:
    """
    获取全局聊天配置管理器实例
    
    Returns:
        聊天配置管理器实例
    """
    global _chat_config_manager
    
    if _chat_config_manager is None:
        _chat_config_manager = ChatConfigManager()
    
    return _chat_config_manager


def get_chat_config() -> ChatModuleConfig:
    """
    获取聊天模块配置的便捷函数
    
    Returns:
        聊天模块配置
    """
    return get_chat_config_manager().get_config()


def update_chat_config(updates: Dict[str, Any]) -> bool:
    """
    更新聊天模块配置的便捷函数
    
    Args:
        updates: 要更新的配置项
        
    Returns:
        是否更新成功
    """
    return get_chat_config_manager().update_config(updates)