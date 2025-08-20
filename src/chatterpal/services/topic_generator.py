# -*- coding: utf-8 -*-
"""
对话主题生成器
实现随机主题生成和基于上下文的主题生成功能
"""

from typing import Dict, Any, List, Optional
import logging
import random
from datetime import datetime

from ..core.llm.base import LLMBase, LLMError
from ..core.errors import error_handler, TopicGenerationError as TopicGenError
from ..utils.encoding_fix import safe_str


logger = logging.getLogger(__name__)


class TopicGenerationError(Exception):
    """主题生成错误（向后兼容）"""
    pass


class TopicGenerator:
    """对话主题生成器"""
    
    def __init__(self, llm: Optional[LLMBase] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化主题生成器
        
        Args:
            llm: 大语言模型实例
            config: 配置参数
        """
        self.llm = llm
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 配置参数
        self.difficulty_levels = self.config.get("difficulty_levels", ["beginner", "intermediate", "advanced"])
        self.categories = self.config.get("categories", ["daily", "hobby", "travel", "work", "tech", "culture"])
        self.max_retries = self.config.get("max_retries", 3)
        
        # 预定义主题库
        self._init_default_topics()
    
    def _init_default_topics(self):
        """初始化默认主题库"""
        self.default_topics = {
            "beginner": {
                "daily": [
                    "What did you have for breakfast today?",
                    "Tell me about your daily routine.",
                    "What's your favorite color and why?",
                    "Describe your family.",
                    "What time do you usually wake up?",
                    "What's your favorite food?",
                    "Tell me about your home.",
                    "What do you like to do in your free time?",
                    "What's the weather like today?",
                    "Do you have any pets?"
                ],
                "hobby": [
                    "Do you like reading books?",
                    "What sports do you enjoy?",
                    "Do you like listening to music?",
                    "Can you cook? What's your favorite dish to make?",
                    "Do you enjoy watching movies?",
                    "What games do you like to play?",
                    "Do you like drawing or painting?",
                    "Are you interested in photography?",
                    "Do you enjoy gardening?",
                    "What do you like to do on weekends?"
                ]
            },
            "intermediate": {
                "daily": [
                    "What's your favorite way to spend a weekend?",
                    "Describe a memorable meal you've had recently.",
                    "Tell me about a place you'd love to visit.",
                    "What's your favorite season and why?",
                    "Describe your ideal day off from work or school.",
                    "What's something that always makes you smile?",
                    "Tell me about a skill you're proud of having.",
                    "Describe your morning routine.",
                    "What's something interesting about your hometown?",
                    "How do you usually celebrate your birthday?"
                ],
                "hobby": [
                    "What's a hobby you enjoy or would like to try?",
                    "Tell me about a book or movie that impressed you.",
                    "What's your favorite type of music or artist?",
                    "Describe a creative project you've worked on.",
                    "What's your favorite way to stay healthy and active?",
                    "Tell me about a skill you'd like to learn.",
                    "What's your favorite outdoor activity?",
                    "Describe a memorable concert or performance you attended.",
                    "What's your favorite way to relax after a busy day?",
                    "Tell me about a hobby that helps you express creativity."
                ],
                "travel": [
                    "Describe the most interesting place you've visited.",
                    "What's your dream vacation destination?",
                    "Tell me about a cultural difference you've experienced.",
                    "What's the best travel advice you've received?",
                    "Describe a memorable journey you've taken.",
                    "What do you always pack when traveling?",
                    "Tell me about local food you've tried while traveling.",
                    "What's your preferred way to travel and why?",
                    "Describe a travel experience that changed your perspective.",
                    "What's something you always do when visiting a new city?"
                ],
                "work": [
                    "What's the most rewarding part of your work or studies?",
                    "Describe a typical day at work or school.",
                    "What skills do you think are important for success?",
                    "Tell me about a challenge you've overcome recently.",
                    "What's your ideal work environment?",
                    "Describe a project you're particularly proud of.",
                    "What motivates you to work hard?",
                    "Tell me about someone who has influenced your career.",
                    "What's something new you've learned recently?",
                    "How do you balance work and personal life?"
                ]
            },
            "advanced": {
                "culture": [
                    "How has technology changed the way people communicate?",
                    "What role does tradition play in modern society?",
                    "Discuss the impact of globalization on local cultures.",
                    "How do you think education will evolve in the future?",
                    "What are the benefits and challenges of living in a multicultural society?",
                    "How has social media influenced people's behavior and relationships?",
                    "What's your opinion on the work-life balance in different cultures?",
                    "How do you think climate change will affect future generations?",
                    "Discuss the importance of preserving cultural heritage.",
                    "What role does art play in society?"
                ],
                "tech": [
                    "How do you think artificial intelligence will change our daily lives?",
                    "What are the ethical considerations of using personal data?",
                    "Discuss the impact of remote work on society and economy.",
                    "How has the internet changed the way we access information?",
                    "What are the pros and cons of social media platforms?",
                    "How do you think virtual reality will be used in the future?",
                    "Discuss the role of technology in education.",
                    "What are your thoughts on digital privacy and security?",
                    "How has e-commerce changed shopping habits?",
                    "What's your opinion on the digital divide between generations?"
                ],
                "work": [
                    "What qualities make an effective leader?",
                    "How do you handle conflicts in a professional environment?",
                    "Discuss the importance of continuous learning in your career.",
                    "What's your approach to making difficult decisions?",
                    "How do you think the job market will change in the next decade?",
                    "Discuss the role of creativity and innovation in business.",
                    "What are the challenges of working in a diverse team?",
                    "How do you maintain motivation during challenging projects?",
                    "What's your opinion on the gig economy and freelancing?",
                    "How do you think companies can better support employee wellbeing?"
                ]
            }
        }
    
    def generate_random_topic(self, difficulty: str = "intermediate", category: Optional[str] = None) -> str:
        """
        生成随机主题（增强错误处理版本）
        
        Args:
            difficulty: 难度级别 ("beginner", "intermediate", "advanced")
            category: 主题分类，如果为None则随机选择
            
        Returns:
            生成的主题字符串
            
        Raises:
            TopicGenError: 主题生成失败
        """
        try:
            # 验证难度级别
            if difficulty not in self.difficulty_levels:
                difficulty = "intermediate"
                self.logger.warning(f"无效的难度级别，使用默认值: {difficulty}")
            
            # 获取可用分类
            available_categories = list(self.default_topics.get(difficulty, {}).keys())
            if not available_categories:
                raise error_handler.create_error("TOPIC_GENERATION_FAILED", 
                                                difficulty=difficulty,
                                                reason="没有找到对应难度级别的主题")
            
            # 选择分类
            if category is None or category not in available_categories:
                category = random.choice(available_categories)
            
            # 获取主题列表
            topics = self.default_topics[difficulty][category]
            if not topics:
                raise error_handler.create_error("TOPIC_GENERATION_FAILED",
                                                difficulty=difficulty,
                                                category=category,
                                                reason="分类下没有可用主题")
            
            # 随机选择主题
            selected_topic = random.choice(topics)
            
            self.logger.info(f"生成随机主题 - 难度: {difficulty}, 分类: {category}, 主题: {selected_topic}")
            return selected_topic
            
        except TopicGenError:
            # 重新抛出已知错误
            raise
        except Exception as e:
            self.logger.error(f"生成随机主题失败: {e}")
            # 创建并抛出错误
            raise error_handler.create_error("TOPIC_GENERATION_FAILED", error_message=safe_str(e))

    def generate_random_topic_with_fallback(self, difficulty: str = "intermediate", category: Optional[str] = None) -> str:
        """
        生成随机主题（带备用方案）
        
        Args:
            difficulty: 难度级别
            category: 主题分类
            
        Returns:
            生成的主题字符串（保证不为空）
        """
        try:
            return self.generate_random_topic(difficulty, category)
        except Exception as e:
            self.logger.warning(f"主题生成失败，使用备用主题: {e}")
            # 返回备用主题列表中的一个
            fallback_topics = [
                "What's something interesting that happened to you recently?",
                "Tell me about your favorite hobby.",
                "What's your favorite season and why?",
                "Describe a place you'd love to visit.",
                "What's something you're proud of?"
            ]
            return random.choice(fallback_topics)
    
    def generate_contextual_topic(self, chat_history: List[Dict[str, Any]], difficulty: str = "intermediate") -> str:
        """
        基于对话历史生成相关主题（增强错误处理版本）
        
        Args:
            chat_history: 对话历史
            difficulty: 难度级别
            
        Returns:
            生成的主题字符串
            
        Raises:
            TopicGenError: 主题生成失败
        """
        if not self.llm:
            self.logger.warning("LLM未初始化，使用随机主题生成")
            return self.generate_random_topic_with_fallback(difficulty)
        
        if not chat_history or len(chat_history) < 2:
            self.logger.info("对话历史不足，使用随机主题生成")
            return self.generate_random_topic_with_fallback(difficulty)
        
        try:
            # 提取最近的对话内容
            recent_messages = chat_history[-6:]  # 最近3轮对话
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in recent_messages
                if msg['role'] in ['user', 'assistant'] and msg.get('content')
            ])
            
            if not conversation_text.strip():
                return self.generate_random_topic_with_fallback(difficulty)
            
            # 构建上下文相关的主题生成提示
            difficulty_descriptions = {
                "beginner": "simple vocabulary and basic sentence structures",
                "intermediate": "moderate complexity with varied vocabulary",
                "advanced": "complex topics requiring analytical thinking"
            }
            
            difficulty_desc = difficulty_descriptions.get(difficulty, "moderate complexity")
            
            prompt = f"""Based on the following conversation, generate a new related topic that would naturally continue the discussion. The topic should be suitable for {difficulty} English learners using {difficulty_desc}.

Recent conversation:
{conversation_text}

Requirements:
1. The topic should be related to what was discussed but introduce a new angle
2. It should be engaging and encourage natural conversation
3. Keep it appropriate for {difficulty} level learners
4. Provide just the topic as a question, without explanation

New topic:"""

            # 调用LLM生成主题（带重试和错误处理）
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    generated_topic = self.llm.chat(prompt)
                    
                    # 清理生成的主题
                    generated_topic = generated_topic.strip().strip('"').strip("'")
                    
                    # 验证主题质量
                    if self._validate_topic(generated_topic):
                        self.logger.info(f"生成上下文相关主题: {generated_topic}")
                        return generated_topic
                    else:
                        self.logger.warning(f"生成的主题质量不佳，重试 {attempt + 1}/{self.max_retries}")
                        last_error = error_handler.create_error("TOPIC_GENERATION_FAILED",
                                                              attempt=attempt + 1,
                                                              reason="主题质量验证失败")
                        
                except Exception as e:
                    self.logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    last_error = error_handler.create_error("TOPIC_GENERATION_FAILED",
                                                          attempt=attempt + 1,
                                                          error_message=safe_str(e))
            
            # 如果所有尝试都失败，记录错误并回退到随机主题
            if last_error:
                error_handler.log_error(last_error, {
                    "difficulty": difficulty,
                    "conversation_length": len(conversation_text),
                    "history_messages": len(chat_history)
                })
            
            self.logger.warning("上下文主题生成失败，使用随机主题")
            return self.generate_random_topic_with_fallback(difficulty)
            
        except TopicGenError:
            # 重新抛出已知错误
            raise
        except Exception as e:
            self.logger.error(f"生成上下文相关主题失败: {e}")
            # 记录错误并回退
            error = error_handler.create_error("TOPIC_GENERATION_FAILED", error_message=safe_str(e))
            error_handler.log_error(error, {"difficulty": difficulty})
            return self.generate_random_topic_with_fallback(difficulty)
    
    def _validate_topic(self, topic: str) -> bool:
        """
        验证主题质量
        
        Args:
            topic: 主题字符串
            
        Returns:
            是否为有效主题
        """
        if not topic or not isinstance(topic, str):
            return False
        
        topic = topic.strip()
        
        # 检查长度
        if len(topic) < 10 or len(topic) > 200:
            return False
        
        # 检查是否包含问号（大多数主题应该是问题）
        if not topic.endswith('?') and not any(word in topic.lower() for word in ['tell me', 'describe', 'explain', 'discuss']):
            return False
        
        # 检查是否包含不当内容的简单过滤
        inappropriate_words = ['politics', 'religion', 'controversial', 'sensitive', 'personal']
        if any(word in topic.lower() for word in inappropriate_words):
            return False
        
        return True
    
    def get_topic_categories(self, difficulty: str = "intermediate") -> List[str]:
        """
        获取主题分类
        
        Args:
            difficulty: 难度级别
            
        Returns:
            分类列表
        """
        return list(self.default_topics.get(difficulty, {}).keys())
    
    def get_topics_by_category(self, category: str, difficulty: str = "intermediate") -> List[str]:
        """
        根据分类获取主题列表
        
        Args:
            category: 主题分类
            difficulty: 难度级别
            
        Returns:
            主题列表
        """
        return self.default_topics.get(difficulty, {}).get(category, [])
    
    def add_custom_topic(self, topic: str, category: str, difficulty: str = "intermediate") -> bool:
        """
        添加自定义主题
        
        Args:
            topic: 主题内容
            category: 主题分类
            difficulty: 难度级别
            
        Returns:
            是否成功添加
        """
        try:
            if not self._validate_topic(topic):
                self.logger.warning(f"无效的主题内容: {topic}")
                return False
            
            # 确保分类存在
            if difficulty not in self.default_topics:
                self.default_topics[difficulty] = {}
            
            if category not in self.default_topics[difficulty]:
                self.default_topics[difficulty][category] = []
            
            # 避免重复添加
            if topic not in self.default_topics[difficulty][category]:
                self.default_topics[difficulty][category].append(topic)
                self.logger.info(f"添加自定义主题 - 难度: {difficulty}, 分类: {category}, 主题: {topic}")
                return True
            else:
                self.logger.info(f"主题已存在: {topic}")
                return True
                
        except Exception as e:
            self.logger.error(f"添加自定义主题失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取主题生成器统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_topics": 0,
            "topics_by_difficulty": {},
            "topics_by_category": {},
            "available_difficulties": self.difficulty_levels,
            "available_categories": self.categories
        }
        
        for difficulty, categories in self.default_topics.items():
            difficulty_count = 0
            stats["topics_by_difficulty"][difficulty] = {}
            
            for category, topics in categories.items():
                topic_count = len(topics)
                difficulty_count += topic_count
                stats["topics_by_difficulty"][difficulty][category] = topic_count
                
                if category not in stats["topics_by_category"]:
                    stats["topics_by_category"][category] = 0
                stats["topics_by_category"][category] += topic_count
            
            stats["topics_by_difficulty"][difficulty]["total"] = difficulty_count
            stats["total_topics"] += difficulty_count
        
        return stats