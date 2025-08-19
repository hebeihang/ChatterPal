# -*- coding: utf-8 -*-
"""
文本处理工具模块

提供文本清理、分析、格式化和语言处理功能。
"""

import re
import string
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter


class TextProcessor:
    """文本处理器类"""

    def __init__(self, language: str = "en"):
        """
        初始化文本处理器

        Args:
            language: 语言代码，默认为英语('en')
        """
        self.language = language
        self._setup_language_specific()

    def _setup_language_specific(self) -> None:
        """设置语言特定的配置"""
        if self.language == "en":
            self.stop_words = {
                "a",
                "an",
                "and",
                "are",
                "as",
                "at",
                "be",
                "by",
                "for",
                "from",
                "has",
                "he",
                "in",
                "is",
                "it",
                "its",
                "of",
                "on",
                "that",
                "the",
                "to",
                "was",
                "will",
                "with",
                "i",
                "you",
                "we",
                "they",
                "she",
                "him",
                "her",
                "his",
                "my",
                "your",
                "our",
                "their",
                "this",
                "these",
                "those",
            }
        else:
            self.stop_words = set()

    def clean_text(
        self,
        text: str,
        remove_punctuation: bool = False,
        lowercase: bool = True,
        remove_extra_spaces: bool = True,
    ) -> str:
        """
        清理文本

        Args:
            text: 原始文本
            remove_punctuation: 是否移除标点符号
            lowercase: 是否转换为小写
            remove_extra_spaces: 是否移除多余空格

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        # 移除控制字符和特殊字符
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

        # 标准化空白字符
        text = re.sub(r"\s+", " ", text)

        if remove_punctuation:
            # 移除标点符号，但保留空格
            text = text.translate(str.maketrans("", "", string.punctuation))

        if lowercase:
            text = text.lower()

        if remove_extra_spaces:
            text = text.strip()

        return text

    def tokenize_words(self, text: str, remove_stop_words: bool = False) -> List[str]:
        """
        分词

        Args:
            text: 输入文本
            remove_stop_words: 是否移除停用词

        Returns:
            List[str]: 词汇列表
        """
        # 清理文本
        cleaned_text = self.clean_text(text, remove_punctuation=True)

        # 简单的空格分词
        words = cleaned_text.split()

        if remove_stop_words:
            words = [word for word in words if word.lower() not in self.stop_words]

        return words

    def tokenize_sentences(self, text: str) -> List[str]:
        """
        分句

        Args:
            text: 输入文本

        Returns:
            List[str]: 句子列表
        """
        # 简单的句子分割（基于标点符号）
        sentences = re.split(r"[.!?]+", text)

        # 清理并过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, int]]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前k个关键词

        Returns:
            List[Tuple[str, int]]: (关键词, 频次) 列表
        """
        words = self.tokenize_words(text, remove_stop_words=True)

        # 过滤短词
        words = [word for word in words if len(word) > 2]

        # 统计词频
        word_counts = Counter(words)

        return word_counts.most_common(top_k)

    def calculate_readability_score(self, text: str) -> Dict[str, float]:
        """
        计算文本可读性分数

        Args:
            text: 输入文本

        Returns:
            Dict[str, float]: 包含各种可读性指标的字典
        """
        sentences = self.tokenize_sentences(text)
        words = self.tokenize_words(text)

        if not sentences or not words:
            return {
                "avg_sentence_length": 0.0,
                "avg_word_length": 0.0,
                "lexical_diversity": 0.0,
            }

        # 平均句子长度
        avg_sentence_length = len(words) / len(sentences)

        # 平均词长
        avg_word_length = sum(len(word) for word in words) / len(words)

        # 词汇多样性（不重复词汇数 / 总词汇数）
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words)

        return {
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "lexical_diversity": lexical_diversity,
        }

    def normalize_text_for_comparison(self, text: str) -> str:
        """
        标准化文本用于比较

        Args:
            text: 输入文本

        Returns:
            str: 标准化后的文本
        """
        # 转换为小写
        text = text.lower()

        # 移除标点符号
        text = re.sub(r"[^\w\s]", "", text)

        # 标准化空白字符
        text = re.sub(r"\s+", " ", text)

        # 去除首尾空格
        text = text.strip()

        return text

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（基于词汇重叠）

        Args:
            text1: 第一个文本
            text2: 第二个文本

        Returns:
            float: 相似度分数 (0-1)
        """
        words1 = set(self.tokenize_words(self.normalize_text_for_comparison(text1)))
        words2 = set(self.tokenize_words(self.normalize_text_for_comparison(text2)))

        if not words1 and not words2:
            return 1.0

        if not words1 or not words2:
            return 0.0

        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def extract_phonetic_features(self, text: str) -> Dict[str, int]:
        """
        提取文本的语音特征

        Args:
            text: 输入文本

        Returns:
            Dict[str, int]: 语音特征统计
        """
        text = text.lower()

        # 元音字母
        vowels = "aeiou"
        vowel_count = sum(1 for char in text if char in vowels)

        # 辅音字母
        consonants = "bcdfghjklmnpqrstvwxyz"
        consonant_count = sum(1 for char in text if char in consonants)

        # 音节估算（简单方法：元音组的数量）
        syllable_count = len(re.findall(r"[aeiou]+", text))

        return {
            "vowel_count": vowel_count,
            "consonant_count": consonant_count,
            "syllable_count": max(1, syllable_count),  # 至少1个音节
            "total_letters": vowel_count + consonant_count,
        }


def remove_filler_words(text: str, language: str = "en") -> str:
    """
    移除填充词（如"um", "uh", "like"等）

    Args:
        text: 输入文本
        language: 语言代码

    Returns:
        str: 移除填充词后的文本
    """
    if language == "en":
        filler_words = {
            "um",
            "uh",
            "er",
            "ah",
            "like",
            "you know",
            "i mean",
            "sort of",
            "kind of",
            "basically",
            "actually",
            "literally",
        }
    else:
        filler_words = set()

    # 创建正则表达式模式
    pattern = r"\b(?:" + "|".join(re.escape(word) for word in filler_words) + r")\b"

    # 移除填充词
    cleaned_text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 清理多余空格
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return cleaned_text


def format_transcript_with_timestamps(transcript: str, timestamps: List[float]) -> str:
    """
    格式化带时间戳的转录文本

    Args:
        transcript: 转录文本
        timestamps: 时间戳列表

    Returns:
        str: 格式化后的文本
    """
    words = transcript.split()

    if len(timestamps) != len(words):
        # 如果时间戳数量不匹配，返回原文本
        return transcript

    formatted_lines = []
    for word, timestamp in zip(words, timestamps):
        formatted_lines.append(f"[{timestamp:.2f}s] {word}")

    return "\n".join(formatted_lines)


def extract_pronunciation_targets(text: str) -> List[Dict[str, str]]:
    """
    提取发音练习目标词汇

    Args:
        text: 输入文本

    Returns:
        List[Dict[str, str]]: 目标词汇信息列表
    """
    processor = TextProcessor()
    words = processor.tokenize_words(text)

    targets = []
    for word in words:
        if len(word) >= 3:  # 只考虑长度>=3的词
            phonetic_features = processor.extract_phonetic_features(word)
            targets.append(
                {
                    "word": word,
                    "syllables": phonetic_features["syllable_count"],
                    "difficulty": (
                        "easy" if phonetic_features["syllable_count"] <= 2 else "medium"
                    ),
                }
            )

    return targets


def generate_pronunciation_feedback(
    original_text: str, recognized_text: str
) -> Dict[str, any]:
    """
    生成发音反馈

    Args:
        original_text: 原始文本
        recognized_text: 识别文本

    Returns:
        Dict[str, any]: 反馈信息
    """
    processor = TextProcessor()

    # 标准化文本
    original_normalized = processor.normalize_text_for_comparison(original_text)
    recognized_normalized = processor.normalize_text_for_comparison(recognized_text)

    # 计算相似度
    similarity = processor.calculate_text_similarity(
        original_normalized, recognized_normalized
    )

    # 分析错误
    original_words = processor.tokenize_words(original_normalized)
    recognized_words = processor.tokenize_words(recognized_normalized)

    # 找出缺失和多余的词
    original_set = set(original_words)
    recognized_set = set(recognized_words)

    missing_words = original_set - recognized_set
    extra_words = recognized_set - original_set

    return {
        "similarity_score": similarity,
        "accuracy_percentage": similarity * 100,
        "missing_words": list(missing_words),
        "extra_words": list(extra_words),
        "word_count_original": len(original_words),
        "word_count_recognized": len(recognized_words),
        "feedback_level": (
            "excellent"
            if similarity > 0.9
            else "good" if similarity > 0.7 else "needs_improvement"
        ),
    }
