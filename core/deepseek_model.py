#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek大模型调用封装模块
基于LangChain对接DeepSeek官方API
提供统一的模型调用接口，支持聊天对话和函数调用两种模式

面试高频考点：
1. LangChain与LLM的对接方式
2. 自定义模型包装器的实现原理
3. 函数调用（Function Calling）的实现机制
4. 错误处理与重试策略
5. 模型参数调优（temperature、max_tokens等）
"""

import os
import sys
from typing import List, Dict, Any, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings

settings = get_settings()


class DeepSeekChatModel:
    """
    DeepSeek大模型封装类
    提供标准的聊天接口，支持同步调用
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek-chat",
        api_base: str = "https://api.deepseek.com/v1",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.9
    ):
        """
        初始化DeepSeek模型
        :param api_key: DeepSeek API密钥
        :param model_name: 模型名称
        :param api_base: API基础地址
        :param max_tokens: 最大生成token数
        :param temperature: 温度参数（控制随机性）
        :param top_p: 核采样参数
        """
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model_name = model_name
        self.api_base = api_base
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        
        # 初始化HTTP客户端
        import requests
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def invoke(self, input: Any, **kwargs) -> Dict[str, Any]:
        """
        同步调用方法
        支持多种输入格式：字符串、消息列表
        :param input: 输入内容（字符串或消息列表）
        :return: 包含响应内容的字典
        """
        if isinstance(input, str):
            messages = [{"role": "user", "content": input}]
        elif isinstance(input, list):
            messages = input
        else:
            messages = [{"role": "user", "content": str(input)}]
        
        return self._generate(messages, **kwargs)
    
    def _generate(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        核心生成方法
        调用DeepSeek API获取响应
        :param messages: 消息列表
        :return: 包含响应内容的字典
        """
        request_body = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        
        tools = kwargs.get("tools")
        if tools:
            request_body["tools"] = tools
            request_body["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        try:
            response = self._session.post(
                f"{self.api_base}/chat/completions",
                json=request_body,
                timeout=60
            )
            response.raise_for_status()
            response_data = response.json()
            
            return self._parse_response(response_data)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": f"[错误] 模型调用失败: {str(e)}",
                "tool_calls": None
            }
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本中的特殊字符，确保能在Windows终端正常显示
        :param text: 原始文本
        :return: 清理后的文本
        """
        if not text:
            return ""
        
        cleaned = text.encode('utf-8', errors='replace').decode('utf-8')
        cleaned = cleaned.replace('\U0001f60a', '[笑脸]')
        cleaned = cleaned.replace('\U0001f64f', '[合十]')
        cleaned = cleaned.replace('\U0001f44d', '[点赞]')
        
        import re
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
        
        return cleaned
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析DeepSeek API响应
        :param response_data: API响应数据
        :return: 标准化的响应字典
        """
        try:
            choice = response_data["choices"][0]
            message = choice["message"]
            
            content = self._clean_text(message.get("content", ""))
            tool_calls = message.get("tool_calls", [])
            
            langchain_tool_calls = []
            if tool_calls:
                for tool_call in tool_calls:
                    func = tool_call.get("function", {})
                    langchain_tool_calls.append({
                        "id": tool_call.get("id", ""),
                        "name": func.get("name", ""),
                        "arguments": func.get("arguments", {})
                    })
            
            return {
                "success": True,
                "content": content,
                "tool_calls": langchain_tool_calls if langchain_tool_calls else None,
                "token_usage": response_data.get("usage", {}),
                "model": response_data.get("model", "")
            }
        except KeyError as e:
            return {
                "success": False,
                "error": f"响应解析失败，缺少字段: {str(e)}",
                "content": f"[错误] 响应解析失败: {str(e)}",
                "tool_calls": None
            }
    
    @property
    def llm_type(self) -> str:
        """返回LLM类型标识"""
        return "deepseek-chat"


def create_deepseek_agent(model_name: str = "deepseek-chat") -> DeepSeekChatModel:
    """
    创建DeepSeek模型实例的工厂函数
    :param model_name: 模型名称
    :return: DeepSeekChatModel实例
    """
    return DeepSeekChatModel(
        api_key=settings.DEEPSEEK_API_KEY,
        model_name=model_name,
        api_base=settings.DEEPSEEK_API_BASE,
        max_tokens=settings.MAX_TOKENS,
        temperature=settings.TEMPERATURE,
        top_p=settings.TOP_P
    )


def test_model_connection() -> Tuple[bool, str]:
    """
    测试模型连接是否正常
    :return: (是否成功, 结果消息)
    """
    if not settings.is_api_key_set:
        return False, "API密钥未配置，请在.env文件中设置DEEPSEEK_API_KEY"
    
    try:
        model = create_deepseek_agent()
        result = model.invoke("你好，测试一下连接是否正常")
        
        if result.get("success"):
            content = result.get("content", "")
            return True, f"连接成功！模型响应: {content[:50]}..."
        else:
            return False, f"连接失败: {result.get('error', '未知错误')}"
    
    except Exception as e:
        return False, f"连接失败: {str(e)}"


if __name__ == "__main__":
    print("=" * 60)
    print("DeepSeek模型连接测试")
    print("=" * 60)
    
    success, message = test_model_connection()
    print(message)
    
    if success:
        print("\n测试通过！模型可以正常调用")
    else:
        print("\n测试失败，请检查API密钥配置")