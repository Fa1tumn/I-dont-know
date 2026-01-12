"""Copy generation utilities using DeepseekClient"""
from __future__ import annotations

from typing import Optional, List, Union

from client import DeepseekClient



# ---------------- VideoGenerator ----------------
VIDEO_TEMPLATE = (
    "You are an expert video copywriter. Given the brief: \"{brief}\", write a {length} {tone} {fmt} for {platform} aimed at {audience}. "
    "Include a short hook (first 5 seconds), three main points, and a call-to-action. Keep it concise and tailored for the platform."
)


class VideoGenerator:
    def __init__(self, client: "DeepseekClient", default_tone: str = "energetic", default_length: str = "short"):
        self.client = client
        self.default_tone = default_tone
        self.default_length = default_length

    def build_prompt(self, brief: str, platform: str = "short-video", fmt: str = "script", tone: Optional[str] = None, length: Optional[str] = None, audience: str = "general") -> str:
        tone = tone or self.default_tone
        length = length or self.default_length
        prompt_parts = [
            "## 任务描述",
            "你是一位专业的视频文案撰写专家。请根据以下要求生成视频文案：",
            "",
            "## 视频/平台信息",
            f"平台: {platform}",
            f"形式: {fmt}",
            "",
            "## 产品/服务描述",
            f"{brief}",
            "",
            "## 具体要求",
            f"1. 语气风格：{tone}",
            f"2. 文案长度：{length}",
            f"3. 目标受众：{audience}",
            "",
            "## 输出要求",
            "- 提供一个抓人开头（前5秒），给出3个要点，并以明确的CTA结尾。",
            "- 如果 format 是 caption，则输出简短有力的标题和若干标签。",
            "- 保持贴合平台规范。",
            "- 要求每个时间段的字数在150-200字每分钟。",
        ]
        return "\n".join(prompt_parts)

    def generate(self, brief: str, platform: str = "short-video", fmt: str = "script", tone: Optional[str] = None, length: Optional[str] = None, audience: str = "general", n: int = 1, similarity: int = 100, **kwargs) -> List[str]:
        if similarity == 100:
            prompt = self.build_prompt(brief, platform=platform, fmt=fmt, tone=tone, length=length, audience=audience)
            prompt += f"- 按照{similarity}%的相似度生成不同版本的文案。\n"
            prompt += "确保与原文案在结构和内容上有明显区别，但仍然传达相同的信息和情感。\n"
        else:
            prompt = self.build_prompt(brief, platform=platform, fmt=fmt, tone=tone, length=length, audience=audience)
        
        results = []
        for _ in range(n):
            text = self.client.generate(prompt, **kwargs)
            results.append(text.strip())
        return results