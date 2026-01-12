"""Copy generation utilities using DeepseekClient"""
from __future__ import annotations

from typing import Optional, List, Union

from client import DeepseekClient


DEFAULT_TEMPLATE = (
    "You are an expert copywriter. Given the brief: \"{brief}\", write a {length} {tone} marketing copy suitable for {audience}. "
    "Keep it concise and persuasive."
)


class CopyGenerator:
    def __init__(self, client: DeepseekClient, default_tone: str = "friendly", default_length: str = "short"):
        self.client = client
        self.default_tone = default_tone
        self.default_length = default_length

    def build_prompt(self, brief: str, tone: Optional[str] = None, length: Optional[str] = None, audience: str = "general") -> str:
        tone = tone or self.default_tone
        length = length or self.default_length
        
        # 构建更详细的提示词
        prompt_parts = [
            "## 任务描述",
            f"你是一位专业的营销文案专家。请根据以下要求生成完整的营销视频内容里的所有要主持人说的文案：",
            "",
            "## 产品/服务描述",
            f"{brief}",
            "",
            "## 具体要求",
            f"1. 语气风格：{tone}",
            f"2. 视频长度：{length}",
            f"3. 目标受众：{audience}",
            "",
            "## 输出要求",
            "请生成高质量、有吸引力的营销文案。每个时间段的内容要求多一点细节和说辞，要求150-200字每分钟。",
        ]
        
        # 如果需要多个变体，在提示词中说明
        return "\n".join(prompt_parts)

    def generate(
        self, 
        brief: str, 
        tone: Optional[str] = None, 
        length: Optional[str] = None, 
        audience: str = "general", 
        n: int = 1, 
        **kwargs
    ) -> List[str]:
        prompt = self.build_prompt(brief, tone=tone, length=length, audience=audience)
        
        # ✅ 关键修改：一次性生成n个结果，而不是循环n次
        try:
            # 调用client.generate，传入n参数
            result = self.client.generate(prompt, n=n, **kwargs)
            
            # 处理返回结果
            if isinstance(result, list):
                # client返回的是列表
                results = [r.strip() for r in result]
            elif isinstance(result, str):
                # client返回的是单个字符串（当n=1时）
                results = [result.strip()]
            else:
                # 其他情况
                results = [str(result).strip()]
            
            # 确保返回列表长度与n一致
            if len(results) < n:
                # 如果数量不足，重复最后一个结果
                results.extend([results[-1]] * (n - len(results)))
            elif len(results) > n:
                # 如果数量过多，截取前n个
                results = results[:n]
                
            return results
            
        except Exception as e:
            # 如果批量生成失败，回退到循环调用
            print(f"批量生成失败，回退到循环调用: {e}")
            results = []
            for i in range(n):
                try:
                    text = self.client.generate(prompt, n=1, **kwargs)
                    if isinstance(text, list):
                        text = text[0] if text else f"变体 {i+1}"
                    results.append(str(text).strip())
                except Exception as inner_e:
                    results.append(f"[生成失败: {inner_e}]")
            return results


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
        ]
        return "\n".join(prompt_parts)

    def generate(self, brief: str, platform: str = "short-video", fmt: str = "script", tone: Optional[str] = None, length: Optional[str] = None, audience: str = "general", n: int = 1, **kwargs) -> List[str]:
        prompt = self.build_prompt(brief, platform=platform, fmt=fmt, tone=tone, length=length, audience=audience)
        results = []
        for _ in range(n):
            text = self.client.generate(prompt, **kwargs)
            results.append(text.strip())
        return results