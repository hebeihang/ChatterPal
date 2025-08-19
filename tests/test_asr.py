"""
Tests for ASR (Automatic Speech Recognition) modules.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from oralcounsellor.core.asr.base import ASRBase, ASRError
from oralcounsellor.core.asr.whisper import WhisperASR
from oralcounsellor.core.asr.aliyun import AliyunASR


class MockASR(ASRBase):
    """Mock ASR implementation for testing base class functionality."""
    
    def __init__(self, config=None, should_fail=False):
        super().__init__(config)
        self.should_fail = should_fail
        self.recognize_calls = []
        self.recognize_file_calls = []
        
    def recognize(self, audio_data: bytes, **kwargs):
        self.recognize_calls.append((audio_data, kwargs))
        if self.should_fail:
            raise ASRError("Mock ASR failure")
        return "mock recognition result"
        
    def recognize_file(self, audio_path: str, **kwargs):
        self.recognize_file_calls.append((audio_path, kwargs))
        if self.should_fail:
            raise ASRError("Mock ASR file failure")
        return "mock file recognition result"


class TestASRBase:
    """Test the ASR base class functionality."""
    
    def test_initialization(self):
        """Test ASR base class initialization."""
        asr = MockASR()
        assert asr.config == {}
        assert asr.logger is not None
        
        config = {"test": "value"}
        asr_with_config = MockASR(config)
        assert asr_with_config.config == config
    
    def test_recognize_gradio_audio_with_string(self):
        """Test recognize_gradio_audio with file path string."""
        asr = MockASR()
        
        # Test with file path
        result = asr.recognize_gradio_audio("test_file.wav")
        assert result == "mock file recognition result"
        assert len(asr.recognize_file_calls) == 1
        assert asr.recognize_file_calls[0][0] == "test_file.wav"
    
    def test_recognize_gradio_audio_with_none(self):
        """Test recognize_gradio_audio with None input."""
        asr = MockASR()
        
        result = asr.recognize_gradio_audio(None)
        assert result is None
    
    @patch('soundfile.write')
    @patch('tempfile.NamedTemporaryFile')
    def test_recognize_gradio_audio_with_tuple(self, mock_tempfile, mock_sf_write):
        """Test recognize_gradio_audio with Gradio tuple format."""
        # Setup mocks
        mock_temp = MagicMock()
        mock_temp.name = "temp_audio.wav"
        mock_tempfile.return_value.__enter__.return_value = mock_temp
        
        asr = MockASR()
        
        # Test with tuple format
        sample_rate = 16000
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (sample_rate, audio_array)
        
        with patch('os.unlink'):
            result = asr.recognize_gradio_audio(audio_data)
        
        assert result == "mock file recognition result"
        mock_sf_write.assert_called_once_with("temp_audio.wav", audio_array, sample_rate)
    
    def test_recognize_gradio_audio_with_invalid_format(self):
        """Test recognize_gradio_audio with invalid format."""
        asr = MockASR()
        
        result = asr.recognize_gradio_audio(123)  # Invalid format
        assert result is None
    
    def test_recognize_gradio_audio_error_handling(self):
        """Test error handling in recognize_gradio_audio."""
        asr = MockASR(should_fail=True)
        
        with pytest.raises(ASRError):
            asr.recognize_gradio_audio("test_file.wav")
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        asr = MockASR()
        assert asr.test_connection() is True
    
    def test_test_connection_failure(self):
        """Test failed connection test."""
        asr = MockASR(should_fail=True)
        # Base implementation always returns True, subclasses should override
        assert asr.test_connection() is True
    
    def test_get_supported_formats(self):
        """Test getting supported audio formats."""
        asr = MockASR()
        formats = asr.get_supported_formats()
        assert isinstance(formats, list)
        assert "wav" in formats
        assert "mp3" in formats
    
    def test_validate_audio_file_exists(self):
        """Test audio file validation with existing file."""
        asr = MockASR()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            assert asr.validate_audio_file(temp_path) is True
        finally:
            os.unlink(temp_path)
    
    def test_validate_audio_file_not_exists(self):
        """Test audio file validation with non-existing file."""
        asr = MockASR()
        assert asr.validate_audio_file("nonexistent_file.wav") is False
    
    def test_validate_audio_file_empty(self):
        """Test audio file validation with empty file."""
        asr = MockASR()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            assert asr.validate_audio_file(temp_path) is False
        finally:
            os.unlink(temp_path)
    
    def test_validate_audio_file_unsupported_format(self):
        """Test audio file validation with unsupported format."""
        asr = MockASR()
        
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            # Should still return True but log a warning
            assert asr.validate_audio_file(temp_path) is True
        finally:
            os.unlink(temp_path)


class TestWhisperASR:
    """Test the Whisper ASR implementation."""
    
    def test_initialization(self):
        """Test Whisper ASR initialization."""
        config = {"model_size": "base", "language": "en"}
        asr = WhisperASR(config)
        
        assert asr.config == config
        assert asr.model_size == "base"
        assert asr.language == "en"
    
    @patch('whisper.load_model')
    def test_recognize_file_success(self, mock_load_model):
        """Test successful file recognition with Whisper."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mock_load_model.return_value = mock_model
        
        asr = WhisperASR()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            result = asr.recognize_file(temp_path)
            assert result == "Hello world"
            mock_model.transcribe.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)
    
    @patch('whisper.load_model')
    def test_recognize_file_failure(self, mock_load_model):
        """Test file recognition failure with Whisper."""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("Transcription failed")
        mock_load_model.return_value = mock_model
        
        asr = WhisperASR()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            with pytest.raises(ASRError):
                asr.recognize_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    @patch('whisper.load_model')
    def test_recognize_bytes_data(self, mock_load_model):
        """Test recognition with bytes data."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello from bytes"}
        mock_load_model.return_value = mock_model
        
        asr = WhisperASR()
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            mock_temp = MagicMock()
            mock_temp.name = "temp_audio.wav"
            mock_tempfile.return_value.__enter__.return_value = mock_temp
            
            with patch('os.unlink'):
                result = asr.recognize(b"fake audio bytes")
            
            assert result == "Hello from bytes"
    
    @patch('whisper.load_model')
    def test_test_connection(self, mock_load_model):
        """Test Whisper connection test."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "test"}
        mock_load_model.return_value = mock_model
        
        asr = WhisperASR()
        
        with patch('tempfile.NamedTemporaryFile'):
            with patch('os.unlink'):
                assert asr.test_connection() is True


class TestAliyunASR:
    """Test the Aliyun ASR implementation."""
    
    def test_initialization(self):
        """Test Aliyun ASR initialization."""
        config = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "app_key": "test_app"
        }
        asr = AliyunASR(config)
        assert asr.config == config
    
    def test_initialization_missing_credentials(self):
        """Test Aliyun ASR initialization with missing credentials."""
        with pytest.raises(ASRError, match="缺少必要的API配置"):
            AliyunASR({})
    
    @patch('dashscope.audio.asr.Recognition.call')
    def test_recognize_file_success(self, mock_call):
        """Test successful file recognition with Aliyun."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.get_sentence.return_value = [{"text": "Hello world"}]
        mock_call.return_value = mock_response
        
        config = {
            "api_key": "test_key",
            "api_secret": "test_secret", 
            "app_key": "test_app"
        }
        asr = AliyunASR(config)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            result = asr.recognize_file(temp_path)
            assert result == "Hello world"
        finally:
            os.unlink(temp_path)
    
    @patch('dashscope.audio.asr.Recognition.call')
    def test_recognize_file_failure(self, mock_call):
        """Test file recognition failure with Aliyun."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.message = "API Error"
        mock_call.return_value = mock_response
        
        config = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "app_key": "test_app"
        }
        asr = AliyunASR(config)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            with pytest.raises(ASRError):
                asr.recognize_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    @patch('dashscope.audio.asr.Recognition.call')
    def test_test_connection(self, mock_call):
        """Test Aliyun connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.get_sentence.return_value = [{"text": "test"}]
        mock_call.return_value = mock_response
        
        config = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "app_key": "test_app"
        }
        asr = AliyunASR(config)
        
        with patch('tempfile.NamedTemporaryFile'):
            with patch('os.unlink'):
                assert asr.test_connection() is True


if __name__ == "__main__":
    pytest.main([__file__])