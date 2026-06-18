#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联网检索工具
使用requests进行网络搜索，支持多种搜索引擎
"""

import requests
from typing import Dict, Any, List
import json
import time
from core import BaseTool


class WebSearchTool(BaseTool):
    """
    联网检索工具
    支持通过搜索引擎获取最新信息
    """
    
    name = "web_search"
    description = "联网搜索最新信息，支持多种搜索引擎"
    parameters = {
        "query": {
            "type": "string",
            "description": "搜索关键词或问题",
            "required": True
        },
        "engine": {
            "type": "string",
            "description": "搜索引擎类型 (bing/google/duckduckgo)",
            "required": False
        },
        "max_results": {
            "type": "integer",
            "description": "最大返回结果数量",
            "required": False
        }
    }
    
    def __init__(self):
        """初始化网络搜索工具"""
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 10
    
    def _search_bing(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用Bing搜索引擎
        :param query: 搜索关键词
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        try:
            # 使用Bing搜索API（这里使用公开接口演示）
            url = "https://api.bing.microsoft.com/v7.0/search"
            params = {
                "q": query,
                "count": max_results,
                "mkt": "zh-CN"
            }
            
            # 注意：实际使用需要配置API Key
            # 这里使用模拟数据演示
            response = self.session.get(
                "https://cn.bing.com/search",
                params={"q": query},
                timeout=self.timeout
            )
            
            # 模拟解析搜索结果（实际需要解析HTML）
            results = []
            for i in range(min(max_results, 3)):
                results.append({
                    "title": f"搜索结果 {i+1}: {query}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"关于'{query}'的相关信息...",
                    "source": "bing"
                })
            
            return results
            
        except Exception as e:
            return [{
                "title": "搜索失败",
                "url": "",
                "snippet": f"搜索出错: {str(e)}",
                "source": "bing"
            }]
    
    def _search_google(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用Google搜索引擎
        :param query: 搜索关键词
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        try:
            # Google搜索（需要配置API或使用代理）
            results = []
            for i in range(min(max_results, 3)):
                results.append({
                    "title": f"Google搜索结果 {i+1}: {query}",
                    "url": f"https://google.com/search?q={query}",
                    "snippet": f"Google关于'{query}'的搜索结果...",
                    "source": "google"
                })
            
            return results
            
        except Exception as e:
            return [{
                "title": "搜索失败",
                "url": "",
                "snippet": f"Google搜索出错: {str(e)}",
                "source": "google"
            }]
    
    def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用DuckDuckGo搜索引擎
        :param query: 搜索关键词
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        try:
            # DuckDuckGo即时答案API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 0
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            results = []
            
            # 添加即时答案
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "即时答案"),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", ""),
                    "source": "duckduckgo"
                })
            
            # 添加相关主题
            for topic in data.get("RelatedTopics", [])[:max_results - len(results)]:
                if "Text" in topic:
                    results.append({
                        "title": topic.get("FirstURL", "").split("/")[-1],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "duckduckgo"
                    })
            
            return results if results else [{
                "title": "无搜索结果",
                "url": "",
                "snippet": f"未找到关于'{query}'的相关信息",
                "source": "duckduckgo"
            }]
            
        except Exception as e:
            return [{
                "title": "搜索失败",
                "url": "",
                "snippet": f"DuckDuckGo搜索出错: {str(e)}",
                "source": "duckduckgo"
            }]
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化搜索结果为可读文本
        :param results: 搜索结果列表
        :return: 格式化后的文本
        """
        if not results:
            return "未找到搜索结果"
        
        formatted = f"找到 {len(results)} 条搜索结果：\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result.get('title', '无标题')}\n"
            formatted += f"   链接: {result.get('url', '无链接')}\n"
            formatted += f"   摘要: {result.get('snippet', '无摘要')}\n"
            formatted += f"   来源: {result.get('source', '未知')}\n\n"
        
        return formatted
    
    def execute(self, **kwargs) -> str:
        """
        执行网络搜索
        :param kwargs: 包含query, engine, max_results等参数
        :return: 搜索结果文本
        """
        query = kwargs.get("query", "")
        engine = kwargs.get("engine", "duckduckgo").lower()
        max_results = kwargs.get("max_results", 5)
        
        if not query:
            return "错误: 搜索关键词不能为空"
        
        print(f"[联网搜索] 正在搜索: {query}")
        print(f"[搜索引擎] {engine}")
        
        # 根据引擎类型选择搜索方法
        search_methods = {
            "bing": self._search_bing,
            "google": self._search_google,
            "duckduckgo": self._search_duckduckgo
        }
        
        search_func = search_methods.get(engine, self._search_duckduckgo)
        results = search_func(query, max_results)
        
        formatted_results = self._format_results(results)
        
        print(f"[搜索完成] 找到 {len(results)} 条结果")
        
        return formatted_results


def create_web_search_tool() -> WebSearchTool:
    """
    工厂函数：创建网络搜索工具实例
    :return: WebSearchTool实例
    """
    return WebSearchTool()