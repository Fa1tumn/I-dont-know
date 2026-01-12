"""Deepseek API client wrapper

Configurable to support different Deepseek endpoints. Reads API key from env var `DEEPSEEK_API_KEY`.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional, Dict, Any, List, Union

import requests

logger = logging.getLogger(__name__)

# ✅ 确认正确的API端点
DEFAULT_BASE_URL = "https://api.deepseek.com"  # 或 "https://api.deepseek.ai"


class DeepseekClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not set. Provide api_key or set DEEPSEEK_API_KEY env var.")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def _post(self, path: str, payload: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        backoff = 1.0
        
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.post(url, json=payload, timeout=self.timeout)
                
                # 详细的调试信息
                logger.debug(f"请求URL: {url}")
                logger.debug(f"请求数据: {payload}")
                logger.debug(f"状态码: {resp.status_code}")
                
                if resp.status_code == 429:
                    logger.warning(f"请求频率限制，等待 {backoff} 秒后重试")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                
                resp.raise_for_status()
                return resp.json()
                
            except requests.RequestException as exc:
                logger.error(f"请求失败 (尝试 {attempt}/{max_retries}): {exc}")
                if attempt == max_retries:
                    raise
                time.sleep(backoff)
                backoff *= 2
        
        raise RuntimeError("请求失败")
    
    def generate(
        self, 
        prompt: str, 
        model: str = "deepseek-chat", 
        max_tokens: int = 1000, 
        temperature: float = 0.7,
        n: int = 1,  # 新增：生成多个结果
        **kwargs
    ) -> Union[str, List[str]]:
        """调用DeepSeek文本生成端点
        
        参数:
            prompt: 用户输入的提示词
            model: 使用的模型
            max_tokens: 最大生成token数
            temperature: 生成温度
            n: 生成多少个结果
            **kwargs: 其他API参数
        
        返回:
            当 n=1 时返回字符串，当 n>1 时返回字符串列表
        """
        # ✅ 正确的端点路径
        path = "/v1/chat/completions"
        
        # ✅ 正确的请求格式
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "n": n,  # 生成n个结果
        }
        
        # 添加其他可选参数
        payload.update(kwargs)
        
        data = self._post(path, payload)
        
        # ✅ 正确的响应解析
        if isinstance(data, dict) and "choices" in data:
            choices = data["choices"]
            
            if n == 1:
                # 返回单个结果
                if choices and "message" in choices[0]:
                    return choices[0]["message"]["content"]
            else:
                # 返回多个结果
                results = []
                for choice in choices:
                    if "message" in choice:
                        results.append(choice["message"]["content"])
                return results
        
        # 备用解析逻辑
        logger.warning(f"无法解析响应: {data}")
        if isinstance(data, dict) and "choices" in data:
            return str([choice.get("text", choice.get("message", "")) for choice in data["choices"]])
        
        return str(data)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """更通用的聊天补全接口
        
        参数:
            messages: 消息历史，格式为 [{"role": "user", "content": "..."}, ...]
            model: 模型名称
            max_tokens: 最大生成token数
            temperature: 生成温度
            stream: 是否使用流式输出
            **kwargs: 其他API参数
        
        返回:
            完整的API响应
        """
        path = "/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        payload.update(kwargs)
        
        return self._post(path, payload)
    
    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        path = "/v1/models"
        
        try:
            data = self._post(path, {})
            if isinstance(data, dict) and "data" in data:
                return [model["id"] for model in data["data"]]
            return []
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []


# 使用示例
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 从环境变量读取API Key
    client = DeepseekClient()
    
    # 测试单个生成
    print("测试单个生成...")
    result = client.generate(
        prompt="一款面向中小企业的社交媒体管理工具，请生成3个品牌名称",
        max_tokens=300,
        temperature=0.8
    )
    print(f"结果: {result}")
    
    # 测试多个生成
    print("\n测试多个生成 (n=3)...")
    results = client.generate(
        prompt="一款面向中小企业的社交媒体管理工具，请生成3个品牌名称",
        n=3,
        max_tokens=200,
        temperature=0.7
    )
    
    if isinstance(results, list):
        for i, r in enumerate(results, 1):
            print(f"选项 {i}: {r}")
    else:
        print(f"单个结果: {results}")
    
    # 测试获取模型列表
    print("\n获取可用模型...")
    models = client.list_models()
    print(f"可用模型: {models}")