"""
Tests for Assessment (Pronunciation Assessment) modules.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from chatterpal.core.assessment.base import (
    AssessmentBase, AssessmentError, AssessmentResult, 
    WordAnalysis, PhonemeAnalysis, ProsodyFeatures
)
from chatterpal.core.assessment.prosody import ProsodyAnalyzer
from chatterpal.core.assessment.phoneme import PhonemeAnalyzer
from chatterpal.core.assessment.corrector import PronunciationCorrector


class MockAssessment(AssessmentBase):
    """Mock Assessment implementation for testing base class functionality."""
    
    def __init__(self, config=None, should_fail=False):
        super().__init__(config)
        self.should_fail = should_fail
        self.assess_calls = []
        
    def assess(self, audio_data, target_text="", **kwargs):
        self.assess_calls.append((audio_data, target_text, kwargs))
        if self.should_fail:
            raise AssessmentError("Mock assessment failure")
        
        return AssessmentResult(
            overall_score=0.8,
            fluency_score=0.7,
            pronunciation_score=0.8,
            prosody_score=0.9,
            accuracy_score=0.75,
            prosody_features=ProsodyFeatures(),
            recognized_text="mock recognized text",
            target_text=target_text,
            feedback="Mock assessment feedback"
        )


class TestWordAnalysis:
    """Test the WordAnalysis dataclass."""
    
    def test_initialization(self):
        """Test WordAnalysis initialization."""
        analysis = WordAnalysis(
            target_word="hello",
            recognized_word="helo",
            is_correct=False,
            confidence_score=0.8
        )
        
        assert analysis.target_word == "hello"
        assert analysis.recognized_word == "helo"
        assert analysis.is_correct is False
        assert analysis.confidence_score == 0.8
        assert analysis.phonetic_info == {}
        assert analysis.correction_tips == []


class TestPhonemeAnalysis:
    """Test the PhonemeAnalysis dataclass."""
    
    def test_initialization(self):
        """Test PhonemeAnalysis initialization."""
        analysis = PhonemeAnalysis(
            phoneme="æ",
            error_type="substitution",
            description="Vowel substitution error",
            severity="high"
        )
        
        assert analysis.phoneme == "æ"
        assert analysis.error_type == "substitution"
        assert analysis.description == "Vowel substitution error"
        assert analysis.severity == "high"
        assert analysis.correction_method == []


class TestProsodyFeatures:
    """Test the ProsodyFeatures dataclass."""
    
    def test_initialization_defaults(self):
        """Test ProsodyFeatures initialization with defaults."""
        features = ProsodyFeatures()
        
        assert features.speaking_rate == 120.0
        assert features.articulation_rate == 150.0
        assert features.f0_mean == 150.0
        assert features.f0_std == 25.0
        assert features.pause_duration == 0.5
        assert features.fluency_score == 0.7
    
    def test_initialization_custom(self):
        """Test ProsodyFeatures initialization with custom values."""
        features = ProsodyFeatures(
            speaking_rate=140.0,
            f0_mean=180.0,
            fluency_score=0.9
        )
        
        assert features.speaking_rate == 140.0
        assert features.f0_mean == 180.0
        assert features.fluency_score == 0.9


class TestAssessmentResult:
    """Test the AssessmentResult dataclass."""
    
    def test_initialization(self):
        """Test AssessmentResult initialization."""
        prosody_features = ProsodyFeatures(speaking_rate=130.0)
        word_analysis = [WordAnalysis("hello", "hello", True)]
        
        result = AssessmentResult(
            overall_score=0.85,
            fluency_score=0.8,
            pronunciation_score=0.9,
            prosody_score=0.8,
            accuracy_score=0.85,
            prosody_features=prosody_features,
            word_analysis=word_analysis,
            feedback="Good pronunciation"
        )
        
        assert result.overall_score == 0.85
        assert result.fluency_score == 0.8
        assert result.prosody_features.speaking_rate == 130.0
        assert len(result.word_analysis) == 1
        assert result.feedback == "Good pronunciation"
    
    def test_to_dict(self):
        """Test AssessmentResult to_dict conversion."""
        word_analysis = [WordAnalysis("hello", "hello", True, confidence_score=0.9)]
        phoneme_analysis = [PhonemeAnalysis("æ", "correct", "Good pronunciation")]
        
        result = AssessmentResult(
            overall_score=0.85,
            fluency_score=0.8,
            pronunciation_score=0.9,
            prosody_score=0.8,
            accuracy_score=0.85,
            prosody_features=ProsodyFeatures(),
            word_analysis=word_analysis,
            phoneme_analysis=phoneme_analysis,
            feedback="Good job"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["overall_score"] == 0.85
        assert "detailed_scores" in result_dict
        assert "prosody_features" in result_dict
        assert "word_analysis" in result_dict
        assert "phoneme_analysis" in result_dict
        assert len(result_dict["word_analysis"]) == 1
        assert len(result_dict["phoneme_analysis"]) == 1


class TestAssessmentBase:
    """Test the Assessment base class functionality."""
    
    def test_initialization(self):
        """Test Assessment base class initialization."""
        assessment = MockAssessment()
        assert assessment.config == {}
        assert assessment.logger is not None
        
        config = {"test": "value"}
        assessment_with_config = MockAssessment(config)
        assert assessment_with_config.config == config
    
    def test_validate_audio_data_bytes(self):
        """Test audio data validation with bytes."""
        assessment = MockAssessment()
        
        assert assessment.validate_audio_data(b"audio data") is True
        assert assessment.validate_audio_data(b"") is False
        assert assessment.validate_audio_data(None) is False
    
    def test_validate_audio_data_file_path(self):
        """Test audio data validation with file path."""
        assessment = MockAssessment()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            assert assessment.validate_audio_data(temp_path) is True
        finally:
            os.unlink(temp_path)
        
        # Test non-existent file
        assert assessment.validate_audio_data("nonexistent.wav") is False
        
        # Test empty file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            assert assessment.validate_audio_data(temp_path) is False
        finally:
            os.unlink(temp_path)
    
    def test_validate_audio_data_gradio_tuple(self):
        """Test audio data validation with Gradio tuple."""
        assessment = MockAssessment()
        
        # Valid tuple
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        assert assessment.validate_audio_data(audio_data) is True
        
        # Invalid tuple format
        assert assessment.validate_audio_data((16000,)) is False
        assert assessment.validate_audio_data((16000, None)) is False
        assert assessment.validate_audio_data((16000, [])) is False
    
    def test_validate_audio_data_invalid_type(self):
        """Test audio data validation with invalid type."""
        assessment = MockAssessment()
        
        assert assessment.validate_audio_data(123) is False
        assert assessment.validate_audio_data([1, 2, 3]) is False
    
    @patch('soundfile.write')
    def test_convert_audio_to_file_bytes(self, mock_sf_write):
        """Test converting bytes audio data to file."""
        assessment = MockAssessment()
        
        audio_data = b"fake audio data"
        output_path = "output.wav"
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = assessment.convert_audio_to_file(audio_data, output_path)
            assert result is True
            mock_file.write.assert_called_once_with(audio_data)
    
    @patch('soundfile.write')
    def test_convert_audio_to_file_tuple(self, mock_sf_write):
        """Test converting Gradio tuple audio data to file."""
        assessment = MockAssessment()
        
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        output_path = "output.wav"
        
        result = assessment.convert_audio_to_file(audio_data, output_path)
        assert result is True
        mock_sf_write.assert_called_once_with(output_path, audio_array, 16000)
    
    def test_convert_audio_to_file_invalid(self):
        """Test converting invalid audio data to file."""
        assessment = MockAssessment()
        
        result = assessment.convert_audio_to_file("invalid", "output.wav")
        assert result is False
    
    def test_detect_language(self):
        """Test language detection."""
        assessment = MockAssessment()
        
        assert assessment.detect_language("Hello world") == "en"
        assert assessment.detect_language("你好世界") == "zh"
        assert assessment.detect_language("Hello 世界") == "zh"  # Mixed, Chinese detected
        assert assessment.detect_language("") == "en"  # Default
        assert assessment.detect_language("123456") == "en"  # Default
    
    def test_calculate_text_similarity(self):
        """Test text similarity calculation."""
        assessment = MockAssessment()
        
        # Identical texts
        assert assessment.calculate_text_similarity("hello world", "hello world") == 1.0
        
        # Completely different texts
        assert assessment.calculate_text_similarity("hello", "goodbye") == 0.0
        
        # Partially similar texts
        similarity = assessment.calculate_text_similarity("hello world", "hello there")
        assert 0 < similarity < 1
        
        # Empty texts
        assert assessment.calculate_text_similarity("", "") == 1.0
        assert assessment.calculate_text_similarity("hello", "") == 0.0
    
    @patch('librosa.get_duration')
    def test_estimate_audio_duration_file(self, mock_get_duration):
        """Test audio duration estimation from file."""
        mock_get_duration.return_value = 3.5
        
        assessment = MockAssessment()
        duration = assessment.estimate_audio_duration("test.wav")
        assert duration == 3.5
    
    def test_estimate_audio_duration_tuple(self):
        """Test audio duration estimation from Gradio tuple."""
        assessment = MockAssessment()
        
        audio_array = np.zeros(16000)  # 1 second at 16kHz
        audio_data = (16000, audio_array)
        
        duration = assessment.estimate_audio_duration(audio_data)
        assert duration == 1.0
    
    def test_estimate_audio_duration_fallback(self):
        """Test audio duration estimation fallback."""
        assessment = MockAssessment()
        
        # Should return default value for unsupported types
        duration = assessment.estimate_audio_duration(b"bytes")
        assert duration == 1.0
    
    def test_create_default_result(self):
        """Test creating default assessment result."""
        assessment = MockAssessment()
        
        result = assessment.create_default_result("Test error")
        assert isinstance(result, AssessmentResult)
        assert result.overall_score == 0.0
        assert result.feedback == "Test error"
        assert len(result.suggestions) > 0
    
    def test_test_functionality_success(self):
        """Test functionality test success."""
        assessment = MockAssessment()
        
        with patch('numpy.linspace'), patch('numpy.sin'):
            assert assessment.test_functionality() is True
    
    def test_test_functionality_failure(self):
        """Test functionality test failure."""
        assessment = MockAssessment(should_fail=True)
        
        with patch('numpy.linspace'), patch('numpy.sin'):
            assert assessment.test_functionality() is False


class TestProsodyAnalyzer:
    """Test the Prosody Analyzer implementation."""
    
    def test_initialization(self):
        """Test ProsodyAnalyzer initialization."""
        config = {"sample_rate": 16000}
        analyzer = ProsodyAnalyzer(config)
        assert analyzer.config == config
    
    @patch('parselmouth.Sound')
    @patch('myprosody.mysptotal')
    def test_analyze_prosody_success(self, mock_mysptotal, mock_sound):
        """Test successful prosody analysis."""
        # Mock myprosody output
        mock_mysptotal.return_value = [
            "test.wav", 120.0, 150.0, 180.0, 25.0, 100.0, 200.0,
            0.5, 120.0, 0.7, 0.8, 0.7, 0.7, 5, 1
        ]
        
        # Mock parselmouth Sound
        mock_sound_obj = MagicMock()
        mock_sound.return_value = mock_sound_obj
        
        analyzer = ProsodyAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            features = analyzer.analyze_prosody(temp_path)
            assert isinstance(features, ProsodyFeatures)
            assert features.speaking_rate == 120.0
            assert features.f0_mean == 180.0
        finally:
            os.unlink(temp_path)
    
    @patch('myprosody.mysptotal')
    def test_analyze_prosody_failure(self, mock_mysptotal):
        """Test prosody analysis failure."""
        mock_mysptotal.side_effect = Exception("Analysis failed")
        
        analyzer = ProsodyAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            with pytest.raises(AssessmentError):
                analyzer.analyze_prosody(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_assess_with_file_path(self):
        """Test assessment with file path."""
        analyzer = ProsodyAnalyzer()
        
        with patch.object(analyzer, 'analyze_prosody') as mock_analyze:
            mock_analyze.return_value = ProsodyFeatures()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(b"fake audio data")
                temp_path = temp_file.name
            
            try:
                result = analyzer.assess(temp_path, "test text")
                assert isinstance(result, AssessmentResult)
                assert result.target_text == "test text"
            finally:
                os.unlink(temp_path)


class TestPhonemeAnalyzer:
    """Test the Phoneme Analyzer implementation."""
    
    def test_initialization(self):
        """Test PhonemeAnalyzer initialization."""
        config = {"language": "en"}
        analyzer = PhonemeAnalyzer(config)
        assert analyzer.config == config
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_analyze_phonemes_success(self, mock_audio_file, mock_recognizer):
        """Test successful phoneme analysis."""
        # Mock speech recognition
        mock_r = MagicMock()
        mock_audio = MagicMock()
        mock_r.recognize_google.return_value = "hello world"
        mock_recognizer.return_value = mock_r
        mock_audio_file.return_value.__enter__.return_value = mock_audio
        
        analyzer = PhonemeAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            analysis = analyzer.analyze_phonemes(temp_path, "hello world")
            assert isinstance(analysis, list)
        finally:
            os.unlink(temp_path)
    
    def test_assess_with_gradio_tuple(self):
        """Test assessment with Gradio tuple."""
        analyzer = PhonemeAnalyzer()
        
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        with patch.object(analyzer, 'convert_audio_to_file', return_value=True):
            with patch.object(analyzer, 'analyze_phonemes', return_value=[]):
                result = analyzer.assess(audio_data, "test")
                assert isinstance(result, AssessmentResult)


class TestPronunciationCorrector:
    """Test the Pronunciation Corrector implementation."""
    
    def test_initialization(self):
        """Test PronunciationCorrector initialization."""
        config = {"correction_threshold": 0.7}
        corrector = PronunciationCorrector(config)
        assert corrector.config == config
    
    def test_assess_comprehensive(self):
        """Test comprehensive pronunciation assessment."""
        corrector = PronunciationCorrector()
        
        # Mock the component analyzers
        with patch.object(corrector, 'prosody_analyzer') as mock_prosody:
            with patch.object(corrector, 'phoneme_analyzer') as mock_phoneme:
                # Mock prosody analysis
                mock_prosody.analyze_prosody.return_value = ProsodyFeatures(
                    speaking_rate=120.0,
                    fluency_score=0.8
                )
                
                # Mock phoneme analysis
                mock_phoneme.analyze_phonemes.return_value = [
                    PhonemeAnalysis("æ", "correct", "Good pronunciation")
                ]
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(b"fake audio data")
                    temp_path = temp_file.name
                
                try:
                    result = corrector.assess(temp_path, "hello world")
                    assert isinstance(result, AssessmentResult)
                    assert result.overall_score > 0
                    assert len(result.phoneme_analysis) > 0
                finally:
                    os.unlink(temp_path)
    
    def test_generate_feedback(self):
        """Test feedback generation."""
        corrector = PronunciationCorrector()
        
        result = AssessmentResult(
            overall_score=0.7,
            fluency_score=0.6,
            pronunciation_score=0.8,
            prosody_score=0.7,
            accuracy_score=0.75,
            prosody_features=ProsodyFeatures()
        )
        
        feedback = corrector.generate_feedback(result)
        assert isinstance(feedback, str)
        assert len(feedback) > 0
    
    def test_generate_suggestions(self):
        """Test suggestion generation."""
        corrector = PronunciationCorrector()
        
        result = AssessmentResult(
            overall_score=0.6,
            fluency_score=0.5,
            pronunciation_score=0.7,
            prosody_score=0.6,
            accuracy_score=0.65,
            prosody_features=ProsodyFeatures(speaking_rate=80.0)  # Slow speaking
        )
        
        suggestions = corrector.generate_suggestions(result)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("速度" in suggestion for suggestion in suggestions)

if __name__ == "__main__":
    pytest.main([__file__])







