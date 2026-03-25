# -*- coding: utf-8 -*-
"""Score tab component for pronunciation evaluation."""

import gradio as gr
from typing import Optional
from ...services.evaluation import EvaluationService
from ...utils.encoding_fix import safe_str


class ScoreTab:
    """Score interface component for pronunciation evaluation."""

    def __init__(self, evaluation_service: EvaluationService):
        """Initialize score tab with evaluation service."""
        self.evaluation_service = evaluation_service

    def create_interface(self) -> gr.Tab:
        """Create the score tab interface."""
        with gr.Tab("Score") as tab:
            gr.Markdown(
                """
                ## 📊 发音评分系统
                
                基于AI的智能发音评价系统，帮助您提升日语发音质量。
                
                **评估维度：**
                - 🎯 **发音准确性**：与标准发音的匹配度
                - 🗣️ **语法正确性**：句子结构和语法使用
                - 📚 **词汇使用**：词汇选择的恰当性
                - 🌊 **流畅度**：语音的连贯性和自然度
                
                **使用方法：**
                1. 在文本框中输入要练习的英文句子
                2. 录制您的发音
                3. 点击"进行评价"获得详细反馈和评分
                """
            )

            # Input section
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        label="📝 练习文本",
                        placeholder="请输入您想要练习的英文句子...",
                        lines=3,
                        info="输入标准的英文文本，系统将基于此文本评估您的发音",
                    )

                    audio_input = gr.Microphone(
                        label="🎤 录制发音", info="请清晰地朗读上方的文本内容"
                    )

                    evaluate_btn = gr.Button(
                        value="🎯 开始评价", variant="primary", size="lg"
                    )

            # Output section
            with gr.Row():
                with gr.Column():
                    evaluation_output = gr.Textbox(
                        label="📊 评价结果", lines=15, info="详细的发音评价和改进建议"
                    )

            # Additional info section
            with gr.Accordion("💡 评分说明", open=False):
                gr.Markdown(
                    """
                    ### 评分标准 (满分10分)
                    
                    **9-10分 (优秀)**
                    - 发音清晰准确，接近母语水平
                    - 语法完全正确，词汇使用恰当
                    - 语调自然，流畅度极佳
                    
                    **7-8分 (良好)**
                    - 发音基本准确，偶有小错误
                    - 语法正确，词汇使用合适
                    - 语调较自然，流畅度良好
                    
                    **5-6分 (中等)**
                    - 发音可理解，但有明显错误
                    - 语法基本正确，词汇使用一般
                    - 语调略显生硬，流畅度一般
                    
                    **3-4分 (需改进)**
                    - 发音错误较多，影响理解
                    - 语法有错误，词汇使用不当
                    - 语调不自然，流畅度较差
                    
                    **1-2分 (需大幅改进)**
                    - 发音错误严重，难以理解
                    - 语法错误较多，词汇使用混乱
                    - 语调生硬，流畅度很差
                    """
                )

            # Event handler
            evaluate_btn.click(
                fn=self._evaluate_pronunciation,
                inputs=[text_input, audio_input],
                outputs=evaluation_output,
            )

        return tab

    def _evaluate_pronunciation(self, text_input: str, audio_input) -> str:
        """Evaluate pronunciation based on text and audio input."""
        try:
            # Validate inputs
            if not text_input or not text_input.strip():
                return "❌ 请先输入要练习的文本内容"

            if audio_input is None:
                return "❌ 请录制您的发音"

            # Process evaluation
            result = self.evaluation_service.evaluate_pronunciation(
                text_input=text_input.strip(), audio_input=audio_input
            )

            return result

        except Exception as e:
            return f"❌ 评价过程出错: {safe_str(e)}\n\n请检查输入内容并重试。"
