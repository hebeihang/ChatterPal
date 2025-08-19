"""
Integration tests for web components and Gradio interface.
Tests chat, score, and correction tabs functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import numpy as np
import gradio as gr

from oralcounsellor.web.components.chat_tab import ChatTab
from oralcounsellor.web.components.score_tab import ScoreTab
from oralcounsellor.web.components.correct_tab import CorrectTab
from oralcounsellor.services.chat import ChatService
from oralcounsellor.services.evaluation import EvaluationService
from oralcounsellor.services.correction import CorrectionService


class MockChatService:
    """Mock ChatService for testing web components."""
    
    def __init__(self):
        self.conversation_history = []
    
    def process_audio_input(self, audio_data):
        return {
            "success": True,
            "recognized_text": "Hello, how are you?",
            "response_text": "I'm doing well, thank you!",
            "response_audio": b"fake response audio"
        }
    
    def process_text_input(self, text):
        return {
            "success": True,
            "user_text": text,
            "response_text": f"Response to: {text}",
            "response_audio": b"fake response audio"
        }
    
    def get_conversation_history(self):
        return [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    
    def clear_conversation(self):
        self.conversation_history = []
    
    def generate_topic_suggestions(self):
        return ["Weather", "Hobbies", "Travel", "Food", "Technology"]


class MockEvaluationService:
    """Mock EvaluationService for testing web components."""
    
    def evaluate_pronunciation(self, audio_data, target_text=""):
        return {
            "success": True,
            "overall_score": 0.85,
            "detailed_scores": {
                "fluency": 0.8,
                "pronunciation": 0.9,
                "accuracy": 0.85
            },
            "recognized_text": "Hello, how are you today?",
            "target_text": target_text,
            "feedback": "Good pronunciation overall. Keep practicing!"
        }


class MockCorrectionService:
    """Mock CorrectionService for testing web components."""
    
    def analyze_pronunciation(self, audio_data, target_text=""):
        return {
            "success": True,
            "overall_score": 0.85,
            "detailed_analysis": {
                "fluency_score": 0.8,
                "pronunciation_score": 0.9,
                "prosody_score": 0.8,
                "accuracy_score": 0.85
            },
            "prosody_features": {
                "speaking_rate": 120.0,
                "f0_mean": 150.0,
                "fluency_score": 0.8
            },
            "word_analysis": [
                {
                    "target_word": "hello",
                    "recognized_word": "hello",
                    "is_correct": True,
                    "confidence_score": 0.9
                }
            ],
            "phoneme_analysis": [
                {
                    "phoneme": "h",
                    "error_type": "correct",
                    "description": "Correctly pronounced",
                    "severity": "none"
                }
            ],
            "feedback": "Excellent pronunciation! Your speech is clear and well-paced.",
            "suggestions": ["Continue practicing", "Work on intonation"],
            "recognized_text": "Hello, how are you today?",
            "target_text": target_text
        }
    
    def get_detailed_feedback(self):
        return {
            "overall_assessment": "Good pronunciation",
            "specific_issues": ["Minor intonation issues"],
            "improvement_tips": ["Practice stress patterns"]
        }
    
    def generate_practice_exercises(self, problem_areas):
        return [
            {
                "exercise": "Repeat after me: Hello world",
                "description": "Practice basic greeting"
            },
            {
                "exercise": "Read aloud: The quick brown fox",
                "description": "Practice consonant sounds"
            }
        ]


class TestChatTab:
    """Test the ChatTab component functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = MockChatService()
        self.chat_tab = ChatTab(self.mock_service)
    
    def test_initialization(self):
        """Test ChatTab initialization."""
        assert self.chat_tab.chat_service is self.mock_service
        assert hasattr(self.chat_tab, 'conversation_display')
        assert hasattr(self.chat_tab, 'user_input')
    
    def test_create_interface(self):
        """Test creating Gradio interface."""
        interface = self.chat_tab.create_interface()
        
        # Should return Gradio components
        assert interface is not None
        # The interface should be a tuple or list of Gradio components
        assert isinstance(interface, (tuple, list, gr.Column, gr.Row))
    
    def test_process_text_message(self):
        """Test processing text message."""
        user_text = "Hello, how are you?"
        
        result = self.chat_tab.process_text_message(user_text)
        
        # Should return conversation display and audio
        assert isinstance(result, (tuple, list))
        assert len(result) >= 2  # At least conversation and audio
    
    def test_process_audio_message(self):
        """Test processing audio message."""
        # Simulate Gradio audio input
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        result = self.chat_tab.process_audio_message(audio_data)
        
        # Should return conversation display and audio
        assert isinstance(result, (tuple, list))
        assert len(result) >= 2
    
    def test_clear_conversation(self):
        """Test clearing conversation."""
        result = self.chat_tab.clear_conversation()
        
        # Should return empty conversation display
        assert result is not None
    
    def test_get_topic_suggestions(self):
        """Test getting topic suggestions."""
        suggestions = self.chat_tab.get_topic_suggestions()
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(isinstance(topic, str) for topic in suggestions)
    
    def test_format_conversation_display(self):
        """Test formatting conversation for display."""
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        display = self.chat_tab.format_conversation_display(conversation)
        
        assert isinstance(display, str)
        assert "Hello" in display
        assert "Hi there!" in display
    
    def test_error_handling_empty_input(self):
        """Test error handling with empty input."""
        result = self.chat_tab.process_text_message("")
        
        # Should handle gracefully
        assert result is not None
    
    def test_error_handling_invalid_audio(self):
        """Test error handling with invalid audio."""
        result = self.chat_tab.process_audio_message(None)
        
        # Should handle gracefully
        assert result is not None


class TestScoreTab:
    """Test the ScoreTab component functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = MockEvaluationService()
        self.score_tab = ScoreTab(self.mock_service)
    
    def test_initialization(self):
        """Test ScoreTab initialization."""
        assert self.score_tab.evaluation_service is self.mock_service
        assert hasattr(self.score_tab, 'audio_input')
        assert hasattr(self.score_tab, 'target_text_input')
    
    def test_create_interface(self):
        """Test creating Gradio interface."""
        interface = self.score_tab.create_interface()
        
        # Should return Gradio components
        assert interface is not None
        assert isinstance(interface, (tuple, list, gr.Column, gr.Row))
    
    def test_evaluate_pronunciation_with_target(self):
        """Test pronunciation evaluation with target text."""
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        target_text = "Hello, how are you today?"
        
        result = self.score_tab.evaluate_pronunciation(audio_data, target_text)
        
        # Should return evaluation results
        assert isinstance(result, (tuple, list))
        # Should include score display, feedback, etc.
        assert len(result) >= 3
    
    def test_evaluate_pronunciation_without_target(self):
        """Test pronunciation evaluation without target text."""
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        result = self.score_tab.evaluate_pronunciation(audio_data, "")
        
        # Should still work without target text
        assert isinstance(result, (tuple, list))
        assert len(result) >= 3
    
    def test_format_score_display(self):
        """Test formatting score display."""
        scores = {
            "overall_score": 0.85,
            "detailed_scores": {
                "fluency": 0.8,
                "pronunciation": 0.9,
                "accuracy": 0.85
            }
        }
        
        display = self.score_tab.format_score_display(scores)
        
        assert isinstance(display, str)
        assert "0.85" in display or "85" in display  # Score should be visible
        assert "fluency" in display.lower() or "流畅" in display
    
    def test_generate_feedback_text(self):
        """Test generating feedback text."""
        evaluation_result = {
            "overall_score": 0.85,
            "feedback": "Good pronunciation overall",
            "recognized_text": "Hello world",
            "target_text": "Hello world"
        }
        
        feedback = self.score_tab.generate_feedback_text(evaluation_result)
        
        assert isinstance(feedback, str)
        assert len(feedback) > 0
    
    def test_error_handling_no_audio(self):
        """Test error handling with no audio input."""
        result = self.score_tab.evaluate_pronunciation(None, "test")
        
        # Should handle gracefully
        assert result is not None
    
    def test_error_handling_service_failure(self):
        """Test error handling when service fails."""
        # Mock service to fail
        self.mock_service.evaluate_pronunciation = Mock(
            return_value={"success": False, "error": "Service failed"}
        )
        
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        result = self.score_tab.evaluate_pronunciation(audio_data, "test")
        
        # Should handle error gracefully
        assert result is not None


class TestCorrectTab:
    """Test the CorrectTab component functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = MockCorrectionService()
        self.correct_tab = CorrectTab(self.mock_service)
    
    def test_initialization(self):
        """Test CorrectTab initialization."""
        assert self.correct_tab.correction_service is self.mock_service
        assert hasattr(self.correct_tab, 'audio_input')
        assert hasattr(self.correct_tab, 'target_text_input')
    
    def test_create_interface(self):
        """Test creating Gradio interface."""
        interface = self.correct_tab.create_interface()
        
        # Should return Gradio components
        assert interface is not None
        assert isinstance(interface, (tuple, list, gr.Column, gr.Row))
    
    def test_analyze_pronunciation(self):
        """Test pronunciation analysis."""
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        target_text = "Hello, how are you today?"
        
        result = self.correct_tab.analyze_pronunciation(audio_data, target_text)
        
        # Should return analysis results
        assert isinstance(result, (tuple, list))
        # Should include multiple output components
        assert len(result) >= 4
    
    def test_format_detailed_analysis(self):
        """Test formatting detailed analysis."""
        analysis_result = {
            "overall_score": 0.85,
            "detailed_analysis": {
                "fluency_score": 0.8,
                "pronunciation_score": 0.9
            },
            "prosody_features": {
                "speaking_rate": 120.0,
                "f0_mean": 150.0
            },
            "word_analysis": [
                {
                    "target_word": "hello",
                    "recognized_word": "hello",
                    "is_correct": True
                }
            ]
        }
        
        display = self.correct_tab.format_detailed_analysis(analysis_result)
        
        assert isinstance(display, str)
        assert len(display) > 0
    
    def test_format_phoneme_analysis(self):
        """Test formatting phoneme analysis."""
        phoneme_analysis = [
            {
                "phoneme": "h",
                "error_type": "correct",
                "description": "Correctly pronounced",
                "severity": "none"
            },
            {
                "phoneme": "æ",
                "error_type": "substitution",
                "description": "Vowel substitution",
                "severity": "medium"
            }
        ]
        
        display = self.correct_tab.format_phoneme_analysis(phoneme_analysis)
        
        assert isinstance(display, str)
        assert "h" in display
        assert "æ" in display
    
    def test_generate_improvement_suggestions(self):
        """Test generating improvement suggestions."""
        analysis_result = {
            "suggestions": ["Practice vowel sounds", "Work on intonation"],
            "phoneme_analysis": [
                {
                    "phoneme": "æ",
                    "error_type": "substitution",
                    "severity": "high"
                }
            ]
        }
        
        suggestions = self.correct_tab.generate_improvement_suggestions(analysis_result)
        
        assert isinstance(suggestions, str)
        assert len(suggestions) > 0
    
    def test_get_practice_exercises(self):
        """Test getting practice exercises."""
        problem_areas = ["vowel_sounds", "intonation"]
        
        exercises = self.correct_tab.get_practice_exercises(problem_areas)
        
        assert isinstance(exercises, str)
        assert len(exercises) > 0
    
    def test_error_handling_no_audio(self):
        """Test error handling with no audio input."""
        result = self.correct_tab.analyze_pronunciation(None, "test")
        
        # Should handle gracefully
        assert result is not None
    
    def test_error_handling_service_failure(self):
        """Test error handling when service fails."""
        # Mock service to fail
        self.mock_service.analyze_pronunciation = Mock(
            return_value={"success": False, "error": "Analysis failed"}
        )
        
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        result = self.correct_tab.analyze_pronunciation(audio_data, "test")
        
        # Should handle error gracefully
        assert result is not None


class TestWebComponentIntegration:
    """Test integration between web components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_chat_service = MockChatService()
        self.mock_eval_service = MockEvaluationService()
        self.mock_correction_service = MockCorrectionService()
        
        self.chat_tab = ChatTab(self.mock_chat_service)
        self.score_tab = ScoreTab(self.mock_eval_service)
        self.correct_tab = CorrectTab(self.mock_correction_service)
    
    def test_cross_tab_data_flow(self):
        """Test data flow between different tabs."""
        # Simulate user interaction in chat tab
        chat_result = self.chat_tab.process_text_message("Hello")
        assert chat_result is not None
        
        # Use audio from chat in score tab
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        score_result = self.score_tab.evaluate_pronunciation(audio_data, "Hello")
        assert score_result is not None
        
        # Use same audio in correction tab
        correction_result = self.correct_tab.analyze_pronunciation(audio_data, "Hello")
        assert correction_result is not None
    
    def test_consistent_audio_handling(self):
        """Test that all tabs handle audio consistently."""
        audio_array = np.array([0.1, 0.2, 0.3])
        audio_data = (16000, audio_array)
        
        # All tabs should handle the same audio format
        chat_result = self.chat_tab.process_audio_message(audio_data)
        score_result = self.score_tab.evaluate_pronunciation(audio_data, "test")
        correction_result = self.correct_tab.analyze_pronunciation(audio_data, "test")
        
        assert chat_result is not None
        assert score_result is not None
        assert correction_result is not None
    
    def test_error_propagation(self):
        """Test that errors are handled consistently across tabs."""
        # Test with invalid audio
        invalid_audio = None
        
        chat_result = self.chat_tab.process_audio_message(invalid_audio)
        score_result = self.score_tab.evaluate_pronunciation(invalid_audio, "test")
        correction_result = self.correct_tab.analyze_pronunciation(invalid_audio, "test")
        
        # All should handle errors gracefully
        assert chat_result is not None
        assert score_result is not None
        assert correction_result is not None


if __name__ == "__main__":
    pytest.main([__file__])