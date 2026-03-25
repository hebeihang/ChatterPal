# -*- coding: utf-8 -*-
"""
评估服务
实现基于LLM的发音评价功能，集成音频处理和文本分析
"""

from typing import Optional, Dict, Any, List, Union, Tuple
import logging
import json
import tempfile
import os

from ..core.asr.base import ASRBase, ASRError
from ..core.llm.base import LLMBase, LLMError
from ..core.assessment.base import (
    AssessmentBase,
    AssessmentResult,
    AssessmentError,
    WordAnalysis,
    PhonemeAnalysis,
    ProsodyFeatures,
)


logger = logging.getLogger(__name__)


class EvaluationService:
    """
    评估服务类
    提供基于LLM的智能发音评价功能
    """

    def __init__(
        self,
        asr: Optional[ASRBase] = None,
        llm: Optional[LLMBase] = None,
        assessment: Optional[AssessmentBase] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化评估服务

        Args:
            asr: 语音识别实例
            llm: 大语言模型实例
            assessment: 发音评估实例
            config: 配置参数
        """
        self.asr = asr
        self.llm = llm
        self.assessment = assessment
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

        # 默认配置
        self.evaluation_prompts = self._load_evaluation_prompts()
        self.scoring_weights = self.config.get(
            "scoring_weights",
            {"pronunciation": 0.3, "fluency": 0.25, "prosody": 0.25, "accuracy": 0.2},
        )

    def _load_evaluation_prompts(self) -> Dict[str, str]:
        """加载评估提示词模板"""
        return {
            "pronunciation_analysis": """
You are an expert Japanese pronunciation teacher. Analyze the following pronunciation attempt:

Target Text: "{target_text}"
Recognized Text: "{recognized_text}"
Audio Duration: {duration} seconds

Please provide a detailed pronunciation analysis including:
1. Overall pronunciation quality (0-100 score)
2. Specific pronunciation errors and corrections
3. Fluency assessment
4. Suggestions for improvement

Format your response as JSON:
{{
    "overall_score": <0-100>,
    "pronunciation_score": <0-100>,
    "fluency_score": <0-100>,
    "accuracy_score": <0-100>,
    "errors": [
        {{
            "word": "<word>",
            "error_type": "<substitution|omission|insertion>",
            "description": "<description>",
            "correction": "<correction_tip>"
        }}
    ],
    "feedback": "<detailed_feedback>",
    "suggestions": ["<suggestion1>", "<suggestion2>", ...]
}}
""",
            "comparative_analysis": """
You are a Japanese pronunciation expert. Compare the student's pronunciation with the target:

Target: "{target_text}"
Student said: "{recognized_text}"
Similarity: {similarity:.2f}

Provide detailed feedback on:
1. Word-level accuracy
2. Common pronunciation patterns
3. Areas for improvement
4. Specific practice recommendations

Response format: JSON with scores and detailed analysis.
""",
            "fluency_assessment": """
Assess the fluency of this Japanese speech:

Duration: {duration} seconds
Word count: {word_count}
Speaking rate: {speaking_rate:.1f} words/minute

Evaluate:
1. Speaking pace (too fast/slow/appropriate)
2. Pauses and hesitations
3. Natural rhythm and flow
4. Overall fluency score (0-100)

Provide JSON response with fluency analysis.
""",
            "prosody_feedback": """
Analyze the prosody and intonation of this Japanese speech:

Text: "{text}"
Duration: {duration} seconds

Focus on:
1. Stress patterns
2. Intonation contours
3. Rhythm and timing
4. Emotional expression

Provide prosody score (0-100) and specific feedback.
""",
        }

    def evaluate_pronunciation(
        self,
        audio_data: Union[str, bytes, Tuple[int, Any]],
        target_text: str = "",
        detailed_analysis: bool = True,
        **kwargs,
    ) -> AssessmentResult:
        """
        评估发音质量

        Args:
            audio_data: 音频数据（文件路径、字节数据或Gradio格式）
            target_text: 目标文本
            detailed_analysis: 是否进行详细分析
            **kwargs: 其他参数

        Returns:
            评估结果

        Raises:
            AssessmentError: 评估失败
        """
        try:
            # 1. 语音识别
            recognized_text = self._recognize_audio(audio_data)
            if not recognized_text:
                raise AssessmentError("语音识别失败，无法获取文本")

            self.logger.info(f"语音识别结果: {recognized_text}")

            # 2. 基础音频分析（如果有assessment模块）
            base_result = None
            if self.assessment:
                try:
                    base_result = self.assessment.assess(audio_data, target_text)
                    self.logger.info("基础音频分析完成")
                except Exception as e:
                    self.logger.warning(f"基础音频分析失败: {e}")

            # 3. LLM智能分析
            llm_analysis = None
            if self.llm and detailed_analysis:
                try:
                    llm_analysis = self._analyze_with_llm(
                        recognized_text, target_text, audio_data
                    )
                    self.logger.info("LLM智能分析完成")
                except Exception as e:
                    self.logger.warning(f"LLM分析失败: {e}")

            # 4. 合并分析结果
            result = self._merge_analysis_results(
                recognized_text, target_text, base_result, llm_analysis, audio_data
            )

            self.logger.info(f"发音评估完成，总分: {result.overall_score:.1f}")
            return result

        except (ASRError, LLMError, AssessmentError) as e:
            # 重新抛出已知错误
            raise
        except Exception as e:
            self.logger.error(f"发音评估失败: {e}")
            raise AssessmentError(f"发音评估失败: {e}")

    def _recognize_audio(self, audio_data: Union[str, bytes, Tuple[int, Any]]) -> str:
        """语音识别"""
        if not self.asr:
            raise ASRError("ASR模块未初始化")

        try:
            if isinstance(audio_data, str):
                # 文件路径
                return self.asr.recognize_file(audio_data)
            elif isinstance(audio_data, bytes):
                # 字节数据
                return self.asr.recognize(audio_data)
            else:
                # Gradio格式
                return self.asr.recognize_gradio_audio(audio_data)

        except Exception as e:
            raise ASRError(f"语音识别失败: {e}")

    def _analyze_with_llm(
        self,
        recognized_text: str,
        target_text: str,
        audio_data: Union[str, bytes, Tuple[int, Any]],
    ) -> Dict[str, Any]:
        """使用LLM进行智能分析"""
        if not self.llm:
            return {}

        try:
            # 计算基础统计信息
            duration = self._estimate_duration(audio_data)
            word_count = len(recognized_text.split()) if recognized_text else 0
            speaking_rate = (word_count / duration * 60) if duration > 0 else 0
            similarity = self._calculate_similarity(recognized_text, target_text)

            # 构建分析提示词
            if target_text:
                prompt = self.evaluation_prompts["pronunciation_analysis"].format(
                    target_text=target_text,
                    recognized_text=recognized_text,
                    duration=duration,
                )
            else:
                prompt = self.evaluation_prompts["fluency_assessment"].format(
                    duration=duration,
                    word_count=word_count,
                    speaking_rate=speaking_rate,
                )

            # 调用LLM分析
            response = self.llm.chat(prompt)

            # 尝试解析JSON响应
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试提取关键信息
                return self._parse_text_response(response)

        except Exception as e:
            self.logger.error(f"LLM分析失败: {e}")
            return {}

    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """解析文本格式的LLM响应"""
        import re

        analysis = {
            "overall_score": 70.0,
            "pronunciation_score": 70.0,
            "fluency_score": 70.0,
            "accuracy_score": 70.0,
            "feedback": response,
            "suggestions": [],
        }

        # 尝试提取分数
        score_patterns = [
            r"overall[:\s]+(\d+)",
            r"total[:\s]+(\d+)",
            r"score[:\s]+(\d+)",
            r"(\d+)/100",
            r"(\d+)%",
        ]

        for pattern in score_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    if 0 <= score <= 100:
                        analysis["overall_score"] = score
                        break
                except ValueError:
                    continue

        # 提取建议
        suggestion_patterns = [
            r"suggest[^.]*[.!]",
            r"recommend[^.]*[.!]",
            r"try[^.]*[.!]",
            r"practice[^.]*[.!]",
        ]

        suggestions = []
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            suggestions.extend(matches)

        if suggestions:
            analysis["suggestions"] = suggestions[:5]  # 最多5个建议

        return analysis

    def _merge_analysis_results(
        self,
        recognized_text: str,
        target_text: str,
        base_result: Optional[AssessmentResult],
        llm_analysis: Optional[Dict[str, Any]],
        audio_data: Union[str, bytes, Tuple[int, Any]],
    ) -> AssessmentResult:
        """合并分析结果"""

        # 基础信息
        duration = self._estimate_duration(audio_data)
        similarity = self._calculate_similarity(recognized_text, target_text)

        # 初始化分数
        scores = {
            "overall": 0.0,
            "pronunciation": 0.0,
            "fluency": 0.0,
            "prosody": 0.0,
            "accuracy": similarity * 100,
        }

        # 合并基础评估结果
        if base_result:
            scores["pronunciation"] = base_result.pronunciation_score
            scores["fluency"] = base_result.fluency_score
            scores["prosody"] = base_result.prosody_score
            if base_result.accuracy_score > 0:
                scores["accuracy"] = base_result.accuracy_score

        # 合并LLM分析结果
        if llm_analysis:
            if "pronunciation_score" in llm_analysis:
                scores["pronunciation"] = max(
                    scores["pronunciation"], llm_analysis["pronunciation_score"]
                )
            if "fluency_score" in llm_analysis:
                scores["fluency"] = max(
                    scores["fluency"], llm_analysis["fluency_score"]
                )
            if "accuracy_score" in llm_analysis:
                scores["accuracy"] = max(
                    scores["accuracy"], llm_analysis["accuracy_score"]
                )

        # 计算总分
        weights = self.scoring_weights
        scores["overall"] = (
            scores["pronunciation"] * weights.get("pronunciation", 0.3)
            + scores["fluency"] * weights.get("fluency", 0.25)
            + scores["prosody"] * weights.get("prosody", 0.25)
            + scores["accuracy"] * weights.get("accuracy", 0.2)
        )

        # 构建反馈信息
        feedback_parts = []
        if llm_analysis and "feedback" in llm_analysis:
            feedback_parts.append(llm_analysis["feedback"])

        if base_result and base_result.feedback:
            feedback_parts.append(base_result.feedback)

        if not feedback_parts:
            feedback_parts.append(self._generate_default_feedback(scores, similarity))

        # 构建建议列表
        suggestions = []
        if llm_analysis and "suggestions" in llm_analysis:
            suggestions.extend(llm_analysis["suggestions"])

        if base_result and base_result.suggestions:
            suggestions.extend(base_result.suggestions)

        if not suggestions:
            suggestions = self._generate_default_suggestions(scores)

        # 构建单词分析
        word_analysis = []
        if base_result and base_result.word_analysis:
            word_analysis = base_result.word_analysis
        else:
            word_analysis = self._generate_word_analysis(recognized_text, target_text)

        # 构建韵律特征
        prosody_features = ProsodyFeatures()
        if base_result and base_result.prosody_features:
            prosody_features = base_result.prosody_features
        else:
            # 基于基础信息估算韵律特征
            word_count = len(recognized_text.split()) if recognized_text else 0
            prosody_features.speaking_rate = (
                (word_count / duration * 60) if duration > 0 else 120
            )
            prosody_features.fluency_score = scores["fluency"] / 100

        # 创建最终结果
        result = AssessmentResult(
            overall_score=scores["overall"],
            fluency_score=scores["fluency"],
            pronunciation_score=scores["pronunciation"],
            prosody_score=scores["prosody"],
            accuracy_score=scores["accuracy"],
            prosody_features=prosody_features,
            word_analysis=word_analysis,
            phoneme_analysis=[],  # 可以后续扩展
            feedback="\n".join(feedback_parts),
            suggestions=list(set(suggestions))[:5],  # 去重并限制数量
            recognized_text=recognized_text,
            target_text=target_text,
            audio_duration=duration,
            quality_score=min(scores["overall"], 100.0),
        )

        return result

    def _generate_word_analysis(
        self, recognized_text: str, target_text: str
    ) -> List[WordAnalysis]:
        """生成单词级别分析"""
        if not target_text or not recognized_text:
            return []

        target_words = target_text.lower().split()
        recognized_words = recognized_text.lower().split()

        analysis = []
        max_len = max(len(target_words), len(recognized_words))

        for i in range(max_len):
            target_word = target_words[i] if i < len(target_words) else ""
            recognized_word = recognized_words[i] if i < len(recognized_words) else ""

            if target_word:
                is_correct = target_word == recognized_word
                confidence = 1.0 if is_correct else 0.5

                tips = []
                if not is_correct:
                    if recognized_word:
                        tips.append(
                            f"您说的是 '{recognized_word}'，正确应该是 '{target_word}'"
                        )
                    else:
                        tips.append(f"您遗漏了单词 '{target_word}'")

                analysis.append(
                    WordAnalysis(
                        target_word=target_word,
                        recognized_word=recognized_word,
                        is_correct=is_correct,
                        confidence_score=confidence,
                        correction_tips=tips,
                    )
                )

        return analysis

    def _generate_default_feedback(
        self, scores: Dict[str, float], similarity: float
    ) -> str:
        """生成默认反馈"""
        feedback_parts = []

        overall = scores["overall"]
        if overall >= 80:
            feedback_parts.append("您的发音表现很好！")
        elif overall >= 60:
            feedback_parts.append("您的发音还不错，还有提升空间。")
        else:
            feedback_parts.append("您的发音需要更多练习。")

        if similarity < 0.5:
            feedback_parts.append("请注意准确性，确保说出正确的单词。")

        if scores["fluency"] < 60:
            feedback_parts.append("建议提高说话的流畅度。")

        if scores["pronunciation"] < 60:
            feedback_parts.append("请注意发音的准确性。")

        return " ".join(feedback_parts)

    def _generate_default_suggestions(self, scores: Dict[str, float]) -> List[str]:
        """生成默认建议"""
        suggestions = []

        if scores["pronunciation"] < 70:
            suggestions.append("多听标准发音，模仿语音语调")
            suggestions.append("练习音标，掌握正确的发音方法")

        if scores["fluency"] < 70:
            suggestions.append("多进行口语练习，提高流畅度")
            suggestions.append("减少停顿，保持自然的语音节奏")

        if scores["accuracy"] < 70:
            suggestions.append("仔细听题目要求，确保说出正确内容")
            suggestions.append("放慢语速，确保发音清晰")

        if not suggestions:
            suggestions.append("继续保持练习，您做得很好！")

        return suggestions

    def _estimate_duration(
        self, audio_data: Union[str, bytes, Tuple[int, Any]]
    ) -> float:
        """估算音频时长"""
        try:
            if isinstance(audio_data, str):
                # 文件路径
                import librosa

                return librosa.get_duration(filename=audio_data)
            elif isinstance(audio_data, tuple):
                # Gradio音频数据
                sample_rate, audio_array = audio_data
                return len(audio_array) / sample_rate
            else:
                # 默认估算
                return 3.0

        except ImportError:
            self.logger.warning("librosa库未安装，使用默认时长")
            return 3.0
        except Exception as e:
            self.logger.warning(f"时长计算失败: {e}")
            return 3.0

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        import re

        # 预处理文本
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        # Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def evaluate_free_speech(
        self, audio_data: Union[str, bytes, Tuple[int, Any]], **kwargs
    ) -> AssessmentResult:
        """
        评估自由发言

        Args:
            audio_data: 音频数据
            **kwargs: 其他参数

        Returns:
            评估结果
        """
        return self.evaluate_pronunciation(
            audio_data=audio_data, target_text="", detailed_analysis=True, **kwargs
        )

    def compare_pronunciations(
        self,
        audio_data1: Union[str, bytes, Tuple[int, Any]],
        audio_data2: Union[str, bytes, Tuple[int, Any]],
        target_text: str = "",
    ) -> Dict[str, Any]:
        """
        比较两个发音

        Args:
            audio_data1: 第一个音频
            audio_data2: 第二个音频
            target_text: 目标文本

        Returns:
            比较结果
        """
        try:
            # 分别评估两个音频
            result1 = self.evaluate_pronunciation(audio_data1, target_text)
            result2 = self.evaluate_pronunciation(audio_data2, target_text)

            # 构建比较结果
            comparison = {
                "audio1_result": result1.to_dict(),
                "audio2_result": result2.to_dict(),
                "comparison": {
                    "better_audio": (
                        1 if result1.overall_score > result2.overall_score else 2
                    ),
                    "score_difference": abs(
                        result1.overall_score - result2.overall_score
                    ),
                    "improvements": [],
                    "regressions": [],
                },
            }

            # 分析改进和退步
            if result2.pronunciation_score > result1.pronunciation_score:
                comparison["comparison"]["improvements"].append("发音准确性提高")
            elif result2.pronunciation_score < result1.pronunciation_score:
                comparison["comparison"]["regressions"].append("发音准确性下降")

            if result2.fluency_score > result1.fluency_score:
                comparison["comparison"]["improvements"].append("流畅度提高")
            elif result2.fluency_score < result1.fluency_score:
                comparison["comparison"]["regressions"].append("流畅度下降")

            return comparison

        except Exception as e:
            self.logger.error(f"发音比较失败: {e}")
            raise AssessmentError(f"发音比较失败: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态

        Returns:
            服务状态信息
        """
        status = {
            "asr_available": self.asr is not None,
            "llm_available": self.llm is not None,
            "assessment_available": self.assessment is not None,
            "service_config": {"scoring_weights": self.scoring_weights},
        }

        # 测试各模块状态
        if self.asr:
            try:
                status["asr_status"] = self.asr.test_connection()
            except:
                status["asr_status"] = False

        if self.llm:
            try:
                status["llm_status"] = self.llm.test_connection()
            except:
                status["llm_status"] = False

        if self.assessment:
            try:
                status["assessment_status"] = self.assessment.test_functionality()
            except:
                status["assessment_status"] = False

        return status
