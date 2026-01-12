"""Client wrapper for Zhipu (BigModel) API

This file provides a compatible client interface used by the rest of the project.
It will read API keys from `ZHIPU_API_KEY` or `BIGMODEL_API_KEY` (falling back to `DEEPSEEK_API_KEY` for compatibility).
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional, Dict, Any, List, Union

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://open.bigmodel.cn"
CHAT_PATH = "/api/paas/v4/chat/completions"
MODELS_PATH = "/api/paas/v4/models"


class ZhipuClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: int = 30):
        # Prefer ZHIPU or BIGMODEL env vars, fall back to DEEPSEEK_API_KEY for compatibility
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY") or os.getenv("BIGMODEL_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key not set. Set ZHIPU_API_KEY or BIGMODEL_API_KEY environment variable.")
        self.base_url = base_url or os.getenv("BIGMODEL_BASE_URL", DEFAULT_BASE_URL)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})

    def _post(self, path: str, payload: Dict[str, Any], stream: bool = False, max_retries: int = 3) -> Union[Dict[str, Any], requests.Response]:
        url = self.base_url.rstrip("/") + path
        backoff = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                if stream:
                    resp = self.session.post(url, json=payload, timeout=self.timeout, stream=True)
                    resp.raise_for_status()
                    return resp
                resp = self.session.post(url, json=payload, timeout=self.timeout)
                if resp.status_code == 429:
                    logger.warning("Rate limited, retrying in %s seconds", backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as exc:
                logger.exception("Request failed (attempt %s/%s): %s", attempt, max_retries, exc)
                if attempt == max_retries:
                    raise
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError("Failed to make request")

    def generate(self, prompt: str, model: str = "glm-4.5-flash", temperature: float = 1.0, n: int = 1, system: Optional[str] = None, max_tokens: Optional[int] = None, stream: bool = False, **kwargs) -> Union[str, List[str]]:
        """Generate text using Zhipu chat completions endpoint.

        Args:
            prompt: user prompt string
            model: model name (e.g., glm-4.7)
            temperature: sampling temperature
            n: number of variants to return (if supported by provider)
            system: optional system prompt
            max_tokens: optional token limit
            stream: whether to use streaming (returns Response object)
            **kwargs: extra params
        Returns:
            string (if n==1) or list of strings
        """
        messages = []
        if system is None:
            system = "你是一个有用的AI助手。"
        messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature, "stream": stream}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if n is not None:
            payload["n"] = n
        payload.update(kwargs)

        if stream:
            return self._post(CHAT_PATH, payload, stream=True)

        data = self._post(CHAT_PATH, payload)

        # Parse response defensively
        if isinstance(data, dict):
            if "choices" in data and data["choices"]:
                choices = data["choices"]
                if n == 1:
                    first = choices[0]
                    # try several common fields
                    if "message" in first and isinstance(first["message"], dict):
                        return first["message"].get("content", "")
                    if "content" in first:
                        return first.get("content", "")
                    if "text" in first:
                        return first.get("text", "")
                else:
                    results: List[str] = []
                    for c in choices:
                        if "message" in c and isinstance(c["message"], dict):
                            results.append(c["message"].get("content", ""))
                        else:
                            results.append(c.get("content", c.get("text", "")))
                    return results
            # fallback: try 'data' or 'result'
            if "data" in data and isinstance(data["data"], list):
                return [str(x) for x in data["data"]]
        return str(data)

    def list_models(self) -> List[str]:
        try:
            data = self._post(MODELS_PATH, {})
            if isinstance(data, dict) and "data" in data:
                return [m.get("id", m.get("model", "")) for m in data["data"]]
            return []
        except Exception as e:
            logger.error("Failed to list models: %s", e)
            return []


# Backwards compatibility: keep name DeepseekClient used by other modules
DeepseekClient = ZhipuClient


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = ZhipuClient()

    print("测试生成...")
    print(client.generate("请为一款面向中小企业的社交媒体管理工具写一句抓人开头", n=1))

    print("获取模型列表...")
    print(client.list_models())