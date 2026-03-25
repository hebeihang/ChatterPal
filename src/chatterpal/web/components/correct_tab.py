# -*- coding: utf-8 -*-
"""Correct tab component for professional pronunciation assessment."""

import gradio as gr
from typing import Tuple, Optional
from ...services.correction import CorrectionService
from ...utils.encoding_fix import safe_str


class CorrectTab:
    """Correction interface component for professional pronunciation assessment."""

    def __init__(self, correction_service: CorrectionService):
        """Initialize correct tab with correction service."""
        self.correction_service = correction_service

    def create_interface(self) -> gr.Tab:
        """Create the correction tab interface."""
        with gr.Tab("Correct") as tab:
            gr.Markdown(
                """
                # 🎯 专业发音评估系统
                
                本系统采用先进的音频韵律特征分析技术，对您的发音进行全方位的专业评估。
                
                ## 🔬 技术特色：
                - **音频信号分析**：直接分析音频波形，而非仅依赖文本识别
                - **韵律特征提取**：分析语速、音调、停顿、语调等关键特征
                - **多维度评估**：流畅度、发音准确性、韵律表现、内容准确性
                - **专业评分**：基于语音学原理的客观评分系统
                
                ## 📊 评估维度：
                - **流畅度**：语速控制、停顿合理性、语音连贯性
                - **发音准确性**：元音发音、辅音清晰度、音素准确性
                - **韵律表现**：音调变化、重音位置、语调自然度
                - **内容准确性**：与目标文本的匹配程度
                
                ## 🚀 使用方法：
                1. **输入目标文本**（可选）：想要练习的句子或段落
                2. **录制发音**：清晰地朗读内容
                3. **获取评估**：系统将提供详细的发音分析报告
                
                **注意**：本系统基于音频信号进行分析，能够检测真实的发音质量。
                """
            )

            # Input section
            with gr.Row():
                with gr.Column():
                    target_text_input = gr.Textbox(
                        label="🎯 目标文本",
                        placeholder="输入您想要练习的句子（如：I love you），留空则进行通用发音分析",
                        lines=2,
                        info="可选：输入标准文本进行对比分析",
                    )

                    audio_input = gr.Microphone(
                        label="🎤 录制您的发音", info="请清晰地朗读内容，确保音质清晰"
                    )

                    assess_btn = gr.Button(
                        value="🔬 开始专业评估", variant="primary", size="lg"
                    )

            # Output section - Main results
            with gr.Row():
                with gr.Column(scale=1):
                    asr_result = gr.Textbox(
                        label="🔊 语音识别结果", lines=3, info="系统识别出的语音内容"
                    )

                    overall_feedback = gr.Textbox(
                        label="📋 综合评价与指导建议",
                        lines=8,
                        info="基于专业语音学分析的综合评价",
                    )

                with gr.Column(scale=1):
                    word_analysis = gr.Textbox(
                        label="📝 单词级别分析", lines=8, info="每个单词的详细发音分析"
                    )

                    phoneme_analysis = gr.Textbox(
                        label="🔬 音素级别分析", lines=8, info="音素层面的深度分析"
                    )

            # Practice suggestions
            with gr.Row():
                practice_suggestions = gr.Textbox(
                    label="💡 练习建议", lines=5, info="针对性的发音练习建议和方法"
                )

            # Technical information
            with gr.Accordion("🔧 技术说明", open=False):
                gr.Markdown(
                    """
                    ### 分析技术详情
                    
                    **音频特征分析：**
                    - 基频(F0)分析：检测音调变化和语调模式
                    - 共振峰分析：识别元音发音准确性
                    - 能量分析：评估语音清晰度和音量控制
                    - 时长分析：检测语速和停顿模式
                    
                    **韵律特征提取：**
                    - 语速变化检测
                    - 重音位置识别
                    - 语调曲线分析
                    - 停顿模式评估
                    
                    **评估算法：**
                    - 基于语音学原理的多维度评分
                    - 机器学习辅助的模式识别
                    - 统计学方法的置信度计算
                    - 个性化的改进建议生成
                    
                    **适用场景：**
                    - 日语发音练习和纠正
                    - 语言学习者发音质量评估
                    - 口语表达能力提升训练
                    - 语音清晰度专业训练
                    """
                )

            # Event handler
            assess_btn.click(
                fn=self._assess_pronunciation,
                inputs=[audio_input, target_text_input],
                outputs=[
                    asr_result,
                    overall_feedback,
                    word_analysis,
                    phoneme_analysis,
                    practice_suggestions,
                ],
            )

        return tab

    def _assess_pronunciation(
        self, audio_input, target_text: Optional[str] = ""
    ) -> Tuple[str, str, str, str, str]:
        """Perform professional pronunciation assessment."""
        try:
            # Validate audio input
            if audio_input is None:
                error_msg = "❌ 请录制音频进行分析"
                return error_msg, error_msg, "", "", ""

            # Process assessment
            result = self.correction_service.assess_pronunciation(
                audio_input=audio_input,
                target_text=target_text.strip() if target_text else "",
            )

            return result

        except Exception as e:
            error_msg = f"❌ 评估过程出错: {safe_str(e)}"
            return error_msg, error_msg, "", "", ""
