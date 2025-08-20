"""
Pytest configuration and shared fixtures for ChatterPal tests.
"""

import pytest
import tempfile
import os
import numpy as np
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to Python path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        # Write some fake audio data
        temp_file.write(b"fake audio data for testing")
        temp_path = temp_file.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_audio_array():
    """Create a sample audio array for testing."""
    # Generate 1 second of sine wave at 440Hz
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_array = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    
    return sample_rate, audio_array


@pytest.fixture
def gradio_audio_data(sample_audio_array):
    """Create Gradio-style audio data tuple."""
    sample_rate, audio_array = sample_audio_array
    return (sample_rate, audio_array)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return {
        "audio_sample_rate": 16000,
        "whisper_model": "base",
        "asr_provider": "whisper",
        "tts_provider": "edge",
        "llm_provider": "alibaba",
        "api_key": "test_key",
        "api_secret": "test_secret",
        "temperature": 0.7,
        "max_tokens": 1000
    }


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    # Set test environment variables
    test_env_vars = {
        "ENVIRONMENT": "development",  # Use valid environment value
        "DEBUG": "true",
        "AUDIO_TEMP_DIR": "test_temp_audio",
        "CACHE_DIR": "test_cache",
        "MODEL_CACHE_DIR": "test_models"
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_asr():
    """Create a mock ASR instance."""
    mock = Mock()
    mock.recognize.return_value = "Hello, this is a test recognition result."
    mock.recognize_file.return_value = "Hello, this is a test recognition result."
    mock.recognize_gradio_audio.return_value = "Hello, this is a test recognition result."
    mock.test_connection.return_value = True
    mock.get_supported_formats.return_value = ["wav", "mp3", "flac"]
    mock.validate_audio_file.return_value = True
    
    return mock


@pytest.fixture
def mock_tts():
    """Create a mock TTS instance."""
    mock = Mock()
    mock.synthesize.return_value = b"fake synthesized audio data"
    mock.synthesize_to_file.return_value = True
    mock.test_connection.return_value = True
    mock.get_supported_voices.return_value = ["en-US-AriaNeural", "en-US-GuyNeural"]
    mock.get_supported_formats.return_value = ["wav", "mp3"]
    mock.validate_text.return_value = True
    mock.clean_text_for_tts.side_effect = lambda x: x
    
    return mock


@pytest.fixture
def mock_llm():
    """Create a mock LLM instance."""
    mock = Mock()
    mock.chat.return_value = "This is a mock response from the language model."
    mock.chat_stream.return_value = iter(["This ", "is ", "a ", "mock ", "response."])
    mock.test_connection.return_value = True
    mock.normalize_messages.side_effect = lambda x: x if isinstance(x, list) else [{"role": "user", "content": str(x)}]
    mock.validate_messages.return_value = True
    mock.create_conversation.return_value = Mock()
    mock.get_model_info.return_value = {
        "provider": "MockLLM",
        "model": "test-model",
        "temperature": 0.7
    }
    
    return mock


@pytest.fixture
def mock_assessment():
    """Create a mock Assessment instance."""
    from chatterpal.core.assessment.base import AssessmentResult, ProsodyFeatures, WordAnalysis, PhonemeAnalysis
    
    mock = Mock()
    
    # Create a realistic assessment result
    result = AssessmentResult(
        overall_score=0.85,
        fluency_score=0.8,
        pronunciation_score=0.9,
        prosody_score=0.8,
        accuracy_score=0.85,
        prosody_features=ProsodyFeatures(
            speaking_rate=120.0,
            f0_mean=150.0,
            fluency_score=0.8
        ),
        word_analysis=[
            WordAnalysis(
                target_word="hello",
                recognized_word="hello", 
                is_correct=True,
                confidence_score=0.9
            )
        ],
        phoneme_analysis=[
            PhonemeAnalysis(
                phoneme="h",
                error_type="correct",
                description="Correctly pronounced"
            )
        ],
        recognized_text="Hello, how are you today",
        target_text="Hello, how are you today",
        feedback="Good pronunciation overall",
        suggestions=["Continue practicing", "Work on intonation"]
    )
    
    mock.assess.return_value = result
    mock.test_functionality.return_value = True
    mock.validate_audio_data.return_value = True
    mock.detect_language.return_value = "en"
    mock.calculate_text_similarity.return_value = 0.9
    mock.estimate_audio_duration.return_value = 2.5
    
    return mock


@pytest.fixture
def sample_conversation_history():
    """Create sample conversation history for testing."""
    return [
        {"role": "system", "content": "You are a helpful English teacher."},
        {"role": "user", "content": "Hello, how are you"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you practice English today"},
        {"role": "user", "content": "I want to practice pronunciation."},
        {"role": "assistant", "content": "Great! Let's start with some basic words. Can you say 'hello' for me"}
    ]


@pytest.fixture
def sample_assessment_result():
    """Create a sample assessment result for testing."""
    from chatterpal.core.assessment.base import AssessmentResult, ProsodyFeatures, WordAnalysis, PhonemeAnalysis
    
    return AssessmentResult(
        overall_score=0.75,
        fluency_score=0.7,
        pronunciation_score=0.8,
        prosody_score=0.75,
        accuracy_score=0.8,
        prosody_features=ProsodyFeatures(
            speaking_rate=110.0,
            f0_mean=160.0,
            fluency_score=0.7,
            vowel_accuracy=0.8
        ),
        word_analysis=[
            WordAnalysis(
                target_word="pronunciation",
                recognized_word="pronunciation",
                is_correct=True,
                confidence_score=0.85,
                correction_tips=[]
            ),
            WordAnalysis(
                target_word="practice",
                recognized_word="practise",
                is_correct=False,
                confidence_score=0.6,
                correction_tips=["Focus on the 'c' sound"]
            )
        ],
        phoneme_analysis=[
            PhonemeAnalysis(
                phoneme="æ",
                error_type="substitution",
                description="Vowel substitution detected",
                correction_method=["Practice with minimal pairs"],
                severity="medium"
            )
        ],
        recognized_text="I want to practice pronunciation",
        target_text="I want to practice pronunciation",
        audio_duration=3.2,
        feedback="Good effort! Focus on vowel clarity.",
        suggestions=[
            "Practice vowel sounds with minimal pairs",
            "Record yourself and compare with native speakers",
            "Work on word stress patterns"
        ]
    )


# Test markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "web: mark test as web component test"
    )
    config.addinivalue_line(
        "markers", "service: mark test as service layer test"
    )


# Skip tests that require external dependencies in CI
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle external dependencies."""
    import pytest
    
    # Skip tests that require external APIs if not available
    skip_external = pytest.mark.skip(reason="External API not available in test environment")
    
    for item in items:
        # Skip tests that require actual API calls
        if "external_api" in item.keywords:
            item.add_marker(skip_external)
        
        # Mark slow tests
        if "slow" in item.name or "integration" in item.name:
            item.add_marker(pytest.mark.slow)








