#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短期记忆模块 - 对话上下文管理
管理当前对话的上下文历史，支持消息存储、检索和清理
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class Message:
    """
    消息对象
    封装对话中的单条消息
    """
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """
        初始化消息
        :param role: 消息角色 (user/assistant/system/tool)
        :param content: 消息内容
        :param timestamp: 时间戳
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息"""
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp
        )


class ShortTermMemory:
    """
    短期记忆 - 对话上下文管理
    管理当前对话的消息历史，支持最大长度限制和摘要压缩
    """
    
    def __init__(
        self,
        max_messages: int = 50,
        max_tokens: int = 8192,
        system_prompt: str = ""
    ):
        """
        初始化短期记忆
        :param max_messages: 最大消息数量
        :param max_tokens: 最大token数量
        :param system_prompt: 系统提示词
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.messages: List[Message] = []
        self.conversation_id = None
        
        if system_prompt:
            self.add_system_message(system_prompt)
    
    def add_message(self, role: str, content: str) -> Message:
        """
        添加消息
        :param role: 消息角色
        :param content: 消息内容
        :return: 添加的消息对象
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self._trim_messages()
        return message
    
    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        return self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        return self.add_message("assistant", content)
    
    def add_system_message(self, content: str) -> Message:
        """添加系统消息"""
        return self.add_message("system", content)
    
    def add_tool_message(self, content: str) -> Message:
        """添加工具消息"""
        return self.add_message("tool", content)
    
    def _trim_messages(self):
        """
        修剪消息列表，确保不超过限制
        优先保留最近的消息，系统消息始终保留
        """
        # 分离系统消息和普通消息
        system_messages = [m for m in self.messages if m.role == "system"]
        regular_messages = [m for m in self.messages if m.role != "system"]
        
        # 按消息数量限制修剪
        if len(regular_messages) > self.max_messages:
            regular_messages = regular_messages[-self.max_messages:]
        
        # 重新组合
        self.messages = system_messages + regular_messages
    
    def get_messages(self, format_type: str = "list") -> Any:
        """
        获取消息列表
        :param format_type: 返回格式 (list/dict/openai)
        :return: 消息列表
        """
        if format_type == "list":
            return self.messages
        elif format_type == "dict":
            return [m.to_dict() for m in self.messages]
        elif format_type == "openai":
            return [
                {"role": m.role, "content": m.content}
                for m in self.messages
            ]
        return self.messages
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """
        获取最近的N条消息
        :param count: 消息数量
        :return: 消息列表
        """
        return self.messages[-count:]
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self.messages)
    
    def clear(self):
        """清空所有消息（保留系统消息）"""
        system_messages = [m for m in self.messages if m.role == "system"]
        self.messages = system_messages
    
    def reset(self):
        """完全重置记忆"""
        self.messages = []
        if self.system_prompt:
            self.add_system_message(self.system_prompt)
    
    def save_to_file(self, filepath: str):
        """
        保存对话到文件
        :param filepath: 文件路径
        """
        data = {
            "conversation_id": self.conversation_id,
            "max_messages": self.max_messages,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "messages": [m.to_dict() for m in self.messages]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """
        从文件加载对话
        :param filepath: 文件路径
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.conversation_id = data.get("conversation_id")
        self.max_messages = data.get("max_messages", self.max_messages)
        self.max_tokens = data.get("max_tokens", self.max_tokens)
        self.system_prompt = data.get("system_prompt", "")
        
        self.messages = [
            Message.from_dict(m) for m in data.get("messages", [])
        ]
    
    def get_context_summary(self) -> str:
        """
        获取对话上下文摘要
        :return: 摘要文本
        """
        if len(self.messages) == 0:
            return "无对话历史"
        
        recent_messages = self.get_recent_messages(5)
        summary_lines = []
        
        for msg in recent_messages:
            role_name = {
                "user": "用户",
                "assistant": "助手",
                "system": "系统",
                "tool": "工具"
            }.get(msg.role, msg.role)
            
            summary_lines.append(f"{role_name}: {msg.content[:100]}")
        
        return "\n".join(summary_lines)
    
    def contains_topic(self, topic: str) -> bool:
        """
        检查对话中是否包含某个主题
        :param topic: 主题关键词
        :return: 是否包含
        """
        topic_lower = topic.lower()
        for msg in self.messages:
            if topic_lower in msg.content.lower():
                return True
        return False
    
    def get_last_user_message(self) -> Optional[Message]:
        """获取最后一条用户消息"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """获取最后一条助手消息"""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg
        return None


def create_short_term_memory(
    max_messages: int = 50,
    max_tokens: int = 8192,
    system_prompt: str = ""
) -> ShortTermMemory:
    """
    工厂函数：创建短期记忆实例
    :param max_messages: 最大消息数量
    :param max_tokens: 最大token数量
    :param system_prompt: 系统提示词
    :return: ShortTermMemory实例
    """
    return ShortTermMemory(max_messages, max_tokens, system_prompt)