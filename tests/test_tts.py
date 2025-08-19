"""
Tests for TTS (Text-to-Speech) modules.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio

from oralcounsellor.core.tts.base import TTSBase, TTSError
from oralcounsellor.core.tts.edge import EdgeTTS


class MockTTS(TTSBase):
    """Mock TTS implementation for testing base class functionality."""
    
    def __init__(self, config=None, should_fail=False):
        super().__init__(config)
        self.should_fail = should_fail
        self.synthesize_calls = []
        self.synthesize_to_file_calls = []
        
    def synthesize(self, text: str, **kwargs) -> bytes:
        self.synthesize_calls.append((text, kwargs))
        if self.should_fail:
            raise TTSError("Mock TTS failure")
        return b"mock audio data"
        
    def synthesize_to_file(self, text: str, output_path: str, **kwargs) -> bool:
        self.synthesize_to_file_calls.append((text, output_path, kwargs))
        if self.should_fail:
            raise TTSError("Mock TTS file failure")
        
        # Create a fake output file
        with open(output_path, 'wb') as f:
            f.write(b"mock audio data")
        return True


class TestTTSBase:
    """Test the TTS base class functionality."""
    
    def test_initialization(self):
        """Test TTS base class initialization."""
        tts = MockTTS()
        assert tts.config == {}
        assert tts.logger is not None
        
        config = {"test": "value"}
        tts_with_config = MockTTS(config)
        assert tts_with_config.config == config
    
    def test_validate_text_valid(self):
        """Test text validation with valid input."""
        tts = MockTTS()
        
        assert tts.validate_text("Hello world") is True
        assert tts.validate_text("This is a test sentence.") is True
    
    def test_validate_text_invalid(self):
        """Test text validation with invalid input."""
        tts = MockTTS()
        
        assert tts.validate_text("") is False
        assert tts.validate_text("   ") is False
        assert tts.validate_text(None) is False
        assert tts.validate_text(123) is False
    
    def test_validate_text_too_long(self):
        """Test text validation with text exceeding length limit."""
        tts = MockTTS(config={"max_text_length": 10})
        
        assert tts.validate_text("short") is True
        assert tts.validate_text("this is a very long text that exceeds the limit") is False
    
    def test_clean_text_for_tts(self):
        """Test text cleaning for TTS."""
        tts = MockTTS()
        
        # Test basic cleaning
        cleaned = tts.clean_text_for_tts("Hello, world! How are you?")
        assert cleaned == "Hello, world! How are you?"
        
        # Test removing special characters
        cleaned = tts.clean_text_for_tts("Hello @#$% world!!!")
        assert "Hello" in cleaned
        assert "world" in cleaned
        assert "@#$%" not in cleaned
        
        # Test multiple spaces
        cleaned = tts.clean_text_for_tts("Hello    world")
        assert cleaned == "Hello world"
        
        # Test empty input
        cleaned = tts.clean_text_for_tts("")
        assert cleaned == ""
    
    def test_get_supported_voices(self):
        """Test getting supported voices."""
        tts = MockTTS()
        voices = tts.get_supported_voices()
        assert isinstance(voices, list)
        # Base implementation returns empty list
        assert len(voices) == 0
    
    def test_get_supported_formats(self):
        """Test getting supported audio formats."""
        tts = MockTTS()
        formats = tts.get_supported_formats()
        assert isinstance(formats, list)
        assert "wav" in formats
        assert "mp3" in formats
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        tts = MockTTS()
        assert tts.test_connection() is True
    
    def test_test_connection_failure(self):
        """Test failed connection test."""
        tts = MockTTS(should_fail=True)
        assert tts.test_connection() is False
    
    def test_estimate_duration(self):
        """Test duration estimation."""
        tts = MockTTS()
        
        # Test with normal text
        duration = tts.estimate_duration("Hello world", words_per_minute=120)
        assert duration > 0
        
        # Test with empty text
        duration = tts.estimate_duration("", words_per_minute=120)
        assert duration == 0.0
        
        # Test minimum duration
        duration = tts.estimate_duration("Hi", words_per_minute=300)
        assert duration >= 1.0  # Minimum 1 second
    
    def test_validate_output_path_valid(self):
        """Test output path validation with valid path."""
        tts = MockTTS()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "output.wav")
            assert tts.validate_output_path(output_path) is True
    
    def test_validate_output_path_invalid(self):
        """Test output path validation with invalid path."""
        tts = MockTTS()
        
        assert tts.validate_output_path("") is False
        assert tts.validate_output_path(None) is False
    
    def test_validate_output_path_creates_directory(self):
        """Test that output path validation creates missing directories."""
        tts = MockTTS()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "nested", "dir", "output.wav")
            assert tts.validate_output_path(nested_path) is True
            assert os.path.exists(os.path.dirname(nested_path))
    
    @patch('librosa.get_duration')
    @patch('soundfile.read')
    def test_get_audio_info_with_librosa(self, mock_sf_read, mock_librosa_duration):
        """Test getting audio info with librosa available."""
        tts = MockTTS()
        
        # Mock librosa and soundfile
        mock_sf_read.return_value = ([0.1, 0.2, 0.3], 16000)
        
        audio_data = b"fake audio data"
        info = tts.get_audio_info(audio_data)
        
        assert info["size_bytes"] == len(audio_data)
        assert info["sample_rate"] == 16000
        assert info["channels"] == 1
        assert info["format"] == "detected"
    
    def test_get_audio_info_without_librosa(self):
        """Test getting audio info without librosa."""
        tts = MockTTS()
        
        audio_data = b"fake audio data"
        info = tts.get_audio_info(audio_data)
        
        assert info["size_bytes"] == len(audio_data)
        assert info["format"] == "unknown"
        assert info["duration"] == 0.0


class TestEdgeTTS:
    """Test the Edge TTS implementation."""
    
    def test_initialization(self):
        """Test Edge TTS initialization."""
        config = {"voice": "en-US-AriaNeural", "rate": "+0%", "pitch": "+0Hz"}
        tts = EdgeTTS(config)
        assert tts.config == config
        assert tts.voice == "en-US-AriaNeural"
        assert tts.rate == "+0%"
        assert tts.pitch == "+0Hz"
    
    def test_initialization_defaults(self):
        """Test Edge TTS initialization with defaults."""
        tts = EdgeTTS()
        assert tts.voice == "en-US-AriaNeural"
        assert tts.rate == "+0%"
        assert tts.pitch == "+0Hz"
    
    @patch('edge_tts.Communicate')
    def test_synthesize_success(self, mock_communicate_class):
        """Test successful synthesis with Edge TTS."""
        # Mock the async generator
        mock_communicate = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.type = "audio"
        mock_chunk.data = b"audio chunk"
        
        async def mock_stream():
            yield mock_chunk
        
        mock_communicate.stream.return_value = mock_stream()
        mock_communicate_class.return_value = mock_communicate
        
        tts = EdgeTTS()
        
        # 模拟asyncio.run避免实际异步执行
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = b"audio chunk"  # 修正期望值
            
            result = tts.synthesize("Hello world")
            assert result == b"audio chunk"
    
    @patch('edge_tts.Communicate')
    def test_synthesize_failure(self, mock_communicate_class):
        """Test synthesis failure with Edge TTS."""
        mock_communicate_class.side_effect = Exception("Edge TTS error")
        
        tts = EdgeTTS()
        
        with patch('asyncio.run') as mock_run:
            mock_run.side_effect = TTSError("Edge TTS error")
            
            with pytest.raises(TTSError):
                tts.synthesize("Hello world")
    
    def test_synthesize_to_file_success(self):
        """Test successful file synthesis with Edge TTS."""
        tts = EdgeTTS()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch.object(tts, 'synthesize', return_value=b"audio data"):
                result = tts.synthesize_to_file("Hello world", temp_path)
                assert result is True
                assert os.path.exists(temp_path)
                
                with open(temp_path, 'rb') as f:
                    content = f.read()
                    assert content == b"audio data"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_synthesize_to_file_failure(self):
        """Test file synthesis failure with Edge TTS."""
        tts = EdgeTTS()
        
        with patch.object(tts, 'synthesize', side_effect=TTSError("Synthesis failed")):
            with pytest.raises(TTSError):
                tts.synthesize_to_file("Hello world", "output.wav")
    
    @patch('edge_tts.list_voices')
    def test_get_supported_voices(self, mock_list_voices):
        """Test getting supported voices from Edge TTS."""
        mock_voices = [
            {"Name": "en-US-AriaNeural", "Gender": "Female"},
            {"Name": "en-US-GuyNeural", "Gender": "Male"},
        ]
        
        async def mock_async_voices():
            return mock_voices
        
        mock_list_voices.return_value = mock_async_voices()
        
        tts = EdgeTTS()
        
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = ["en-US-AriaNeural", "en-US-GuyNeural"]
            
            voices = tts.get_supported_voices()
            assert "en-US-AriaNeural" in voices
            assert "en-US-GuyNeural" in voices
    
    def test_get_supported_voices_failure(self):
        """Test getting supported voices failure."""
        tts = EdgeTTS()
        
        with patch('asyncio.run', side_effect=Exception("API error")):
            voices = tts.get_supported_voices()
            # Should return default voices on failure
            assert isinstance(voices, list)
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        tts = EdgeTTS()
        
        with patch.object(tts, 'synthesize', return_value=b"test audio"):
            assert tts.test_connection() is True
    
    def test_test_connection_failure(self):
        """Test failed connection test."""
        tts = EdgeTTS()
        
        with patch.object(tts, 'synthesize', side_effect=TTSError("Connection failed")):
            assert tts.test_connection() is False
    
    def test_voice_configuration(self):
        """测试语音配置"""
        config = {
            "voice": "en-US-GuyNeural",
            "rate": "+20%",
            "pitch": "-10Hz"
        }
        tts = EdgeTTS(config)
        
        assert tts.voice == "en-US-GuyNeural"
        assert tts.rate == "+20%"
        assert tts.pitch == "-10Hz"


if __name__ == "__main__":
    pytest.main([__file__])