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
                    "今日の朝ごはんは何を食べましたか？",
                    "あなたの毎日のルーティンについて教えてください。",
                    "好きな色は何ですか？それはなぜですか？",
                    "あなたの家族について教えてください。",
                    "普段、何時に起きますか？",
                    "好きな食べ物は何ですか？",
                    "あなたの家について教えてください。",
                    "暇な時は何をしますか？",
                    "今日の天気はどうですか？",
                    "ペットを飼っていますか？"
                ],
                "hobby": [
                    "本を読むのは好きですか？",
                    "どんなスポーツが好きですか？",
                    "音楽を聴くのは好きですか？",
                    "料理はできますか？得意料理は何ですか？",
                    "映画を見るのは好きですか？",
                    "どんなゲームが好きですか？",
                    "絵を描くのは好きですか？",
                    "写真に興味がありますか？",
                    "ガーデニングは好きですか？",
                    "週末は何をするのが好きですか？"
                ]
            },
            "intermediate": {
                "daily": [
                    "週末の好きな過ごし方は何ですか？",
                    "最近食べた美味しかった食事について教えてください。",
                    "行ってみたい場所について教えてください。",
                    "好きな季節とその理由を教えてください。",
                    "理想的な休日の過ごし方は何ですか？",
                    "いつも笑顔になるものは何ですか？",
                    "あなたの得意なことについて教えてください。",
                    "朝のルーティンについて教えてください。",
                    "あなたの地元の面白いところは何ですか？",
                    "誕生日はいつもどのように過ごしますか？"
                ],
                "hobby": [
                    "好きな趣味、またはやってみたい趣味は何ですか？",
                    "印象に残った本や映画について教えてください。",
                    "好きな音楽のジャンルやアーティストは何ですか？",
                    "自分が作ったクリエイティブな作品について教えてください。",
                    "健康を保つための好きな方法は何ですか？",
                    "新しく学びたいスキルについて教えてください。",
                    "好きなアウトドア活動は何ですか？",
                    "思い出に残っているコンサートやパフォーマンスについて教えてください。",
                    "忙しい一日の後のリラックス方法は何ですか？",
                    "創造性を表現できる趣味について教えてください。"
                ],
                "travel": [
                    "今までに行った中で一番面白かった場所について教えてください。",
                    "夢の旅行先はどこですか？",
                    "経験した文化の違いについて教えてください。",
                    "今までにもらった最高のアドバイスは何ですか？",
                    "思い出に残っている旅行について教えてください。",
                    "旅行の際、必ず持っていくものは何ですか？",
                    "旅行中に食べた地元の食べ物について教えてください。",
                    "好きな旅行のスタイルとその理由は何ですか？",
                    "あなたの考え方を変えた旅行の経験について教えてください。",
                    "新しい都市を訪れたときに必ずすることは何ですか？"
                ],
                "work": [
                    "仕事や勉強で最もやりがいを感じるのはどんな時ですか？",
                    "仕事や学校での典型的な一日を教えてください。",
                    "成功するために重要だと思うスキルは何ですか？",
                    "最近乗り越えた困難について教えてください。",
                    "あなたの理想的な職場環境はどのようなものですか？",
                    "誇りに思っているプロジェクトについて教えてください。",
                    "一生懸命働くモチベーションは何ですか？",
                    "あなたのキャリアに影響を与えた人について教えてください。",
                    "最近学んだ新しいことは何ですか？",
                    "仕事と私生活のバランスをどのように取っていますか？"
                ]
            },
            "advanced": {
                "culture": [
                    "テクノロジーは人々のコミュニケーション方法をどのように変えましたか？",
                    "現代社会において伝統はどのような役割を果たしていますか？",
                    "グローバリゼーションが地域文化に与える影響について議論してください。",
                    "将来、教育はどのように進化すると思いますか？",
                    "多文化社会で暮らすことのメリットと課題は何ですか？",
                    "ソーシャルメディアは人々の行動や人間関係にどのような影響を与えましたか？",
                    "異なる文化におけるワークライフバランスについてのあなたの意見は何ですか？",
                    "気候変動は将来の世代にどのような影響を与えると思いますか？",
                    "文化遺産を保護することの重要性について議論してください。",
                    "社会において芸術はどのような役割を果たしていますか？"
                ],
                "tech": [
                    "人工知能は私たちの日常生活をどのように変えると思いますか？",
                    "個人データを使用する際の倫理的な考慮事項は何ですか？",
                    "リモートワークが社会や経済に与える影響について議論してください。",
                    "インターネットは情報のアクセス方法をどのように変えましたか？",
                    "ソーシャルメディアプラットフォームの長所と短所は何ですか？",
                    "仮想現実（VR）は将来どのように使用されると思いますか？",
                    "教育におけるテクノロジーの役割について議論してください。",
                    "デジタルのプライバシーとセキュリティについてのあなたの考えは何ですか？",
                    "電子商取引（Eコマース）はショッピングの習慣をどのように変えましたか？",
                    "世代間のデジタルデバイドについてのあなたの意見は何ですか？"
                ],
                "work": [
                    "効果的なリーダーに必要な資質は何ですか？",
                    "職場での対立にどのように対処しますか？",
                    "キャリアにおける継続的な学習の重要性について議論してください。",
                    "難しい決断を下す際のアプローチは何ですか？",
                    "今後10年間で雇用市場はどのように変化すると思いますか？",
                    "ビジネスにおける創造性と革新の役割について議論してください。",
                    "多様なチームで働く際の課題は何ですか？",
                    "困難なプロジェクトの間、どのようにモチベーションを維持しますか？",
                    "ギグエコノミーやフリーランスについてのあなたの意見は何ですか？",
                    "企業は従業員の健康をどのようにサポートできると思いますか？"
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
                "最近あった面白いことについて教えてください。",
                "好きな趣味について教えてください。",
                "好きな季節とその理由は何ですか？",
                "行ってみたい場所について教えてください。",
                "誇りに思っていることは何ですか？"
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
            
            prompt = f"""Based on the following conversation, generate a new related topic that would naturally continue the discussion. The topic should be suitable for {difficulty} Japanese learners using {difficulty_desc}.

Recent conversation:
{conversation_text}

Requirements:
1. The topic should be related to what was discussed but introduce a new angle
2. It should be engaging and encourage natural conversation
3. Keep it appropriate for {difficulty} level learners
4. Provide just the topic as a question in Japanese, without explanation

New topic (in Japanese):"""

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