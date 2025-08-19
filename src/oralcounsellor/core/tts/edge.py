# -*- coding: utf-8 -*-
"""
Edge TTS语音合成实现
基于Microsoft Edge TTS进行语音合成
"""

import asyncio
import tempfile
import os
from typing import Optional, Dict, Any, List

try:
    import edge_tts
except ImportError:
    edge_tts = None

from .base import TTSBase, TTSError


class EdgeTTS(TTSBase):
    """
    基于Microsoft Edge TTS的语音合成实现
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Edge TTS

        Args:
            config: 配置参数，支持以下参数：
                - voice: 语音名称 (默认: en-US-AriaNeural)
                - rate: 语速 (默认: +0%)
                - pitch: 音调 (默认: +0Hz)
                - volume: 音量 (默认: +0%)
        """
        super().__init__(config)

        if not edge_tts:
            raise ImportError("edge-tts库未安装，请运行: pip install edge-tts")

        self.voice = self.config.get("voice", "en-US-AriaNeural")
        self.rate = self.config.get("rate", "+0%")
        self.pitch = self.config.get("pitch", "+0Hz")
        self.volume = self.config.get("volume", "+0%")

        self.logger.info(f"EdgeTTS初始化完成，语音: {self.voice}")

    def synthesize(self, text: str, **kwargs) -> bytes:
        """
        合成语音并返回音频数据

        Args:
            text: 要合成的文本
            **kwargs: 其他参数，支持：
                - voice: 临时覆盖语音
                - rate: 临时覆盖语速
                - pitch: 临时覆盖音调
                - volume: 临时覆盖音量

        Returns:
            音频字节数据

        Raises:
            TTSError: 合成过程中的错误
        """
        try:
            if not self.validate_text(text):
                raise TTSError("输入文本无效")

            # 清理文本
            cleaned_text = self.clean_text_for_tts(text)
            if not cleaned_text:
                raise TTSError("清理后的文本为空")

            # 获取参数
            voice = kwargs.get("voice", self.voice)
            rate = kwargs.get("rate", self.rate)
            pitch = kwargs.get("pitch", self.pitch)
            volume = kwargs.get("volume", self.volume)

            # 使用临时文件进行合成
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # 异步合成语音
                success = asyncio.run(
                    self._async_synthesize_to_file(
                        cleaned_text, temp_path, voice, rate, pitch, volume
                    )
                )

                if not success:
                    raise TTSError("语音合成失败")

                # 读取音频数据
                with open(temp_path, "rb") as f:
                    audio_data = f.read()

                self.logger.info(f"语音合成成功，生成 {len(audio_data)} 字节音频数据")
                return audio_data

            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except TTSError:
            raise
        except Exception as e:
            self.logger.error(f"语音合成异常: {e}")
            raise TTSError(f"语音合成异常: {e}")

    def synthesize_to_file(self, text: str, output_path: str, **kwargs) -> bool:
        """
        合成语音并保存到文件

        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            **kwargs: 其他参数

        Returns:
            是否成功保存

        Raises:
            TTSError: 合成过程中的错误
        """
        try:
            if not self.validate_text(text):
                raise TTSError("输入文本无效")

            if not self.validate_output_path(output_path):
                raise TTSError("输出路径无效")

            # 清理文本
            cleaned_text = self.clean_text_for_tts(text)
            if not cleaned_text:
                raise TTSError("清理后的文本为空")

            # 获取参数
            voice = kwargs.get("voice", self.voice)
            rate = kwargs.get("rate", self.rate)
            pitch = kwargs.get("pitch", self.pitch)
            volume = kwargs.get("volume", self.volume)

            # 异步合成语音
            success = asyncio.run(
                self._async_synthesize_to_file(
                    cleaned_text, output_path, voice, rate, pitch, volume
                )
            )

            if success:
                self.logger.info(f"语音合成成功，保存到: {output_path}")
            else:
                raise TTSError("语音合成失败")

            return success

        except TTSError:
            raise
        except Exception as e:
            self.logger.error(f"语音合成到文件异常: {e}")
            raise TTSError(f"语音合成到文件异常: {e}")

    async def _async_synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
    ) -> bool:
        """
        异步合成语音到文件

        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            voice: 语音名称
            rate: 语速
            pitch: 音调
            volume: 音量

        Returns:
            是否成功
        """
        try:
            # 创建TTS通信对象
            communicate = edge_tts.Communicate(
                text, voice, rate=rate, pitch=pitch, volume=volume
            )

            # 保存到文件
            await communicate.save(output_path)

            # 检查文件是否成功创建
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0

        except Exception as e:
            self.logger.error(f"异步语音合成失败: {e}")
            return False

    def synthesize_with_command(self, text: str, output_path: str, **kwargs) -> bool:
        """
        使用命令行方式合成语音（兼容旧代码）

        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            **kwargs: 其他参数

        Returns:
            是否成功
        """
        try:
            if not self.validate_text(text):
                return False

            if not self.validate_output_path(output_path):
                return False

            # 清理文本
            cleaned_text = self.clean_text_for_tts(text)
            if not cleaned_text:
                return False

            # 获取参数
            voice = kwargs.get("voice", self.voice)
            rate = kwargs.get("rate", self.rate)

            # 构建命令
            cmd_parts = [
                "edge-tts",
                "--text",
                f'"{cleaned_text}"',
                "--voice",
                voice,
                "--rate",
                rate,
                "--write-media",
                output_path,
            ]

            cmd = " ".join(cmd_parts)

            # 执行命令
            result = os.system(cmd)

            # 检查结果
            success = (
                result == 0
                and os.path.exists(output_path)
                and os.path.getsize(output_path) > 0
            )

            if success:
                self.logger.info(f"命令行语音合成成功: {output_path}")
            else:
                self.logger.error(f"命令行语音合成失败，返回码: {result}")

            return success

        except Exception as e:
            self.logger.error(f"命令行语音合成异常: {e}")
            return False

    def get_supported_voices(self) -> List[str]:
        """
        获取支持的语音列表

        Returns:
            支持的语音列表
        """
        try:
            # 异步获取语音列表
            voices = asyncio.run(self._async_get_voices())
            return [voice["Name"] for voice in voices]
        except Exception as e:
            self.logger.error(f"获取语音列表失败: {e}")
            # 返回一些常用的语音
            return [
                "en-US-AriaNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
                "zh-CN-XiaoxiaoNeural",
                "zh-CN-YunxiNeural",
                "zh-CN-YunjianNeural",
            ]

    async def _async_get_voices(self) -> List[Dict]:
        """
        异步获取语音列表

        Returns:
            语音信息列表
        """
        voices = await edge_tts.list_voices()
        return voices

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的音频格式列表

        Returns:
            支持的音频格式列表
        """
        return ["wav", "mp3"]

    def test_connection(self) -> bool:
        """
        测试Edge TTS服务连接

        Returns:
            连接是否正常
        """
        try:
            # 尝试合成一个简单的测试文本
            test_text = "Hello, this is a test."

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                success = self.synthesize_to_file(test_text, temp_path)

                if (
                    success
                    and os.path.exists(temp_path)
                    and os.path.getsize(temp_path) > 0
                ):
                    self.logger.info("Edge TTS连接测试成功")
                    return True
                else:
                    self.logger.error("Edge TTS连接测试失败")
                    return False

            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            self.logger.error(f"Edge TTS连接测试异常: {e}")
            return False

    def get_voice_info(self, voice_name: str = None) -> Dict[str, Any]:
        """
        获取语音信息

        Args:
            voice_name: 语音名称，如果为None则使用当前配置的语音

        Returns:
            语音信息字典
        """
        target_voice = voice_name or self.voice

        try:
            voices = asyncio.run(self._async_get_voices())

            for voice in voices:
                if voice.get("Name") == target_voice:
                    return {
                        "name": voice.get("Name", ""),
                        "display_name": voice.get("DisplayName", ""),
                        "local_name": voice.get("LocalName", ""),
                        "gender": voice.get("Gender", ""),
                        "locale": voice.get("Locale", ""),
                        "language": voice.get("Language", ""),
                        "sample_rate": voice.get("SampleRateHertz", 0),
                        "voice_type": voice.get("VoiceType", ""),
                    }

        except Exception as e:
            self.logger.error(f"获取语音信息失败: {e}")

        # 返回默认信息
        return {
            "name": target_voice,
            "display_name": target_voice,
            "local_name": target_voice,
            "gender": "Unknown",
            "locale": "en-US",
            "language": "English",
            "sample_rate": 24000,
            "voice_type": "Neural",
        }


# 便捷函数
def create_edge_tts(
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> EdgeTTS:
    """
    创建EdgeTTS实例的便捷函数

    Args:
        voice: 语音名称
        rate: 语速
        pitch: 音调
        volume: 音量

    Returns:
        EdgeTTS实例
    """
    config = {"voice": voice, "rate": rate, "pitch": pitch, "volume": volume}
    return EdgeTTS(config)


def synthesize_text(
    text: str, output_path: str, voice: str = "en-US-AriaNeural", rate: str = "+0%"
) -> bool:
    """
    合成文本到文件的便捷函数

    Args:
        text: 要合成的文本
        output_path: 输出文件路径
        voice: 语音名称
        rate: 语速

    Returns:
        是否成功
    """
    tts = create_edge_tts(voice=voice, rate=rate)
    return tts.synthesize_to_file(text, output_path)


def get_available_voices() -> List[str]:
    """
    获取可用语音列表的便捷函数

    Returns:
        语音名称列表
    """
    tts = create_edge_tts()
    return tts.get_supported_voices()
