#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReAct推理循环引擎
基于ReAct（Reasoning + Acting）思想实现自主思考循环
核心流程：思考(Thought) → 行动(Action) → 观察(Observation) → 思考(Thought)...

面试高频考点：
1. ReAct推理框架的核心原理
2. 自主思考循环的实现机制
3. 工具调用的决策逻辑
4. 失败重试与错误恢复策略
5. 思考过程的可解释性设计
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings
from .deepseek_model import DeepSeekChatModel, create_deepseek_agent

settings = get_settings()


class ReactStatus(Enum):
    """
    ReAct循环状态枚举
    """
    THINKING = "thinking"
    ACTION = "action"
    OBSERVATION = "observation"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolResult:
    """
    工具执行结果封装
    """
    
    def __init__(
        self,
        tool_name: str,
        success: bool,
        result: Any,
        error: Optional[str] = None
    ):
        self.tool_name = tool_name
        self.success = success
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "result": str(self.result) if not isinstance(self.result, str) else self.result,
            "error": self.error
        }


class Thought:
    """
    思考过程封装
    """
    
    def __init__(
        self,
        step: int,
        content: str,
        next_action: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None
    ):
        self.step = step
        self.content = content
        self.next_action = next_action
        self.tool_name = tool_name
        self.tool_args = tool_args
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "content": self.content,
            "next_action": self.next_action,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args
        }


class ReactEngine:
    """
    ReAct推理循环引擎
    实现自主思考、工具调用、观察反馈的完整循环
    """
    
    def __init__(
        self,
        model: Optional[DeepSeekChatModel] = None,
        max_steps: int = 10,
        retry_limit: int = 3,
        tools: Optional[List[Dict[str, Any]]] = None
    ):
        """
        初始化ReAct引擎
        :param model: DeepSeek模型实例
        :param max_steps: 最大思考步数
        :param retry_limit: 单步骤重试次数
        :param tools: 可用工具列表
        """
        self.model = model or create_deepseek_agent()
        self.max_steps = max_steps
        self.retry_limit = retry_limit
        self.tools = tools or []
        
        # 思考历史记录
        self.thought_history: List[Thought] = []
        self.tool_results: List[ToolResult] = []
        self.observation_history: List[str] = []
        
        # 当前状态
        self.current_step = 0
        self.status = ReactStatus.THINKING
        
        # 工具执行器（通过回调注入）
        self._tool_executor: Optional[Callable] = None
    
    def set_tool_executor(self, executor: Callable):
        """
        设置工具执行器
        :param executor: 工具执行回调函数
        """
        self._tool_executor = executor
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词，指导模型进行ReAct推理
        :return: 系统提示词
        """
        tools_desc = ""
        if self.tools:
            tools_desc = "\n可用工具列表：\n"
            for tool in self.tools:
                tools_desc += f"- {tool['name']}: {tool['description']}\n"
                tools_desc += f"  参数: {tool['parameters']}\n"
        
        return f"""你是一个智能Agent，采用ReAct推理框架进行思考和行动。

核心指令：
1. 仔细分析用户的任务，判断是否需要调用工具
2. 每次思考后，决定下一步行动：调用工具 或 直接回答用户
3. 如果调用工具失败，分析原因并尝试修复或换用其他工具
4. 最终给出完整、准确的答案

推理格式要求：
你的回复必须包含以下两个部分，用特定标记分隔：

[THOUGHT]
你的思考内容：分析当前状态、计划下一步行动

[ACTION]
action_type: 工具名称或"finish"
parameters: 参数（JSON格式，调用工具时必填，finish时可省略）

{tools_desc}

示例：
[THOUGHT]
用户需要查询天气，我需要调用weather工具获取北京的天气信息。

[ACTION]
action_type: weather
parameters: {{"city": "北京"}}
"""
    
    def _parse_model_response(self, response: str) -> Dict[str, Any]:
        """
        解析模型响应，提取思考和行动
        :param response: 模型原始响应
        :return: 包含thought和action的字典
        """
        import re
        
        thought = response.strip()
        action_content = ""
        action_type = ""
        parameters = {}
        
        if "[THOUGHT]" in response:
            thought_start = response.find("[THOUGHT]") + len("[THOUGHT]")
            thought_end = response.find("[ACTION]")
            
            if thought_end == -1:
                thought_end = response.find("[/THOUGHT]")
            
            if thought_end == -1:
                thought_end = len(response)
            
            thought = response[thought_start:thought_end].strip()
            
            if "[ACTION]" in response:
                action_start = response.find("[ACTION]") + len("[ACTION]")
                action_end = response.find("[OBSERVATION]")
                
                if action_end == -1:
                    action_end = response.find("[/ACTION]")
                
                if action_end == -1:
                    action_end = len(response)
                
                action_content = response[action_start:action_end].strip()
        
        thought = re.sub(r'\[/?(THOUGHT|ACTION|OBSERVATION)\]', '', thought).strip()
        
        if action_content:
            type_match = re.search(r'action_type:\s*(.+?)(?:\n|$)', action_content)
            action_type = type_match.group(1).strip() if type_match else ""
            
            params_match = re.search(r'parameters:\s*(.+?)(?:\n|$)', action_content)
            if params_match:
                params_str = params_match.group(1).strip()
                try:
                    import json
                    parameters = json.loads(params_str)
                except json.JSONDecodeError:
                    parameters = {}
        
        return {
            "thought": thought,
            "action_type": action_type,
            "parameters": parameters
        }
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        执行工具调用
        :param tool_name: 工具名称
        :param parameters: 工具参数
        :return: 工具执行结果
        """
        if not self._tool_executor:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error="工具执行器未设置"
            )
        
        try:
            result = self._tool_executor(tool_name, parameters)
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e)
            )
    
    def _build_messages(self, user_query: str, step_results: List[str] = None) -> List[Dict[str, Any]]:
        """
        构建模型输入消息
        :param user_query: 用户原始查询
        :param step_results: 之前步骤的结果
        :return: 消息列表
        """
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_query}
        ]
        
        # 添加之前步骤的结果作为上下文
        if step_results:
            for i, result in enumerate(step_results):
                messages.append({"role": "assistant", "content": result})
        
        return messages
    
    def run(self, user_query: str) -> Dict[str, Any]:
        """
        执行ReAct推理循环
        :param user_query: 用户查询
        :return: 推理结果
        """
        print("\n" + "=" * 60)
        print("ReAct推理循环开始")
        print("=" * 60)
        
        self.thought_history = []
        self.tool_results = []
        self.observation_history = []
        self.current_step = 0
        self.status = ReactStatus.THINKING
        
        step_results = []
        final_answer = ""
        
        while self.current_step < self.max_steps and self.status != ReactStatus.COMPLETED:
            self.current_step += 1
            print(f"\n【步骤 {self.current_step}/{self.max_steps}】")
            
            # 构建消息并调用模型
            messages = self._build_messages(user_query, step_results)
            
            retry_count = 0
            parsed_response = None
            
            while retry_count < self.retry_limit:
                try:
                    response = self.model.invoke(messages)
                    if not response.get("success"):
                        raise Exception(response.get("error", "模型调用失败"))
                    
                    content = response.get("content", "")
                    parsed_response = self._parse_model_response(content)
                    break
                except Exception as e:
                    retry_count += 1
                    print(f"  [WARN] 第 {retry_count} 次重试: {str(e)}")
                    if retry_count >= self.retry_limit:
                        return {
                            "success": False,
                            "error": f"模型调用失败，重试{self.retry_limit}次后仍失败",
                            "thought_history": [t.to_dict() for t in self.thought_history],
                            "tool_results": [r.to_dict() for r in self.tool_results],
                            "final_answer": ""
                        }
            
            if not parsed_response:
                return {
                    "success": False,
                    "error": "无法解析模型响应",
                    "thought_history": [t.to_dict() for t in self.thought_history],
                    "tool_results": [r.to_dict() for r in self.tool_results],
                    "final_answer": ""
                }
            
            thought_content = parsed_response["thought"]
            action_type = parsed_response["action_type"]
            parameters = parsed_response["parameters"]
            
            # 记录思考
            thought = Thought(
                step=self.current_step,
                content=thought_content,
                next_action=action_type,
                tool_name=action_type if action_type != "finish" else None,
                tool_args=parameters if action_type != "finish" else None
            )
            self.thought_history.append(thought)
            
            print(f"  [思考] {thought_content[:80]}...")
            print(f"  [行动] {action_type}")
            if parameters:
                print(f"  [参数] {parameters}")
            
            # 判断行动类型
            if action_type.lower() == "finish":
                # 直接回答用户
                final_answer = thought_content
                self.status = ReactStatus.COMPLETED
                print(f"  [完成] 直接回答用户")
                break
            
            elif action_type in [t["name"] for t in self.tools]:
                # 调用工具
                self.status = ReactStatus.ACTION
                
                tool_result = self._execute_tool(action_type, parameters)
                self.tool_results.append(tool_result)
                
                # 记录观察
                observation = f"工具 {action_type} 执行结果: {tool_result.result}"
                if not tool_result.success:
                    observation = f"工具 {action_type} 执行失败: {tool_result.error}"
                
                self.observation_history.append(observation)
                
                print(f"  [观察] {observation[:100]}...")
                
                # 将结果添加到上下文
                step_results.append(f"[THOUGHT]{thought_content}[/THOUGHT][ACTION]{action_type}[/ACTION][OBSERVATION]{observation}[/OBSERVATION]")
                
                # 如果工具执行失败，尝试重试或调整策略
                if not tool_result.success:
                    print(f"  [WARN] 工具执行失败，尝试下一步...")
            
            else:
                # 未知行动，尝试直接回答
                final_answer = thought_content
                self.status = ReactStatus.COMPLETED
                print(f"  [完成] 未知行动，直接回答")
                break
            
            time.sleep(0.5)
        
        if self.status == ReactStatus.COMPLETED:
            print(f"\n【推理完成】")
            print(f"  总步数: {self.current_step}")
            print(f"  最终答案: {final_answer[:100]}...")
            
            return {
                "success": True,
                "final_answer": final_answer,
                "thought_history": [t.to_dict() for t in self.thought_history],
                "tool_results": [r.to_dict() for r in self.tool_results],
                "observation_history": self.observation_history,
                "total_steps": self.current_step
            }
        else:
            print(f"\n【推理超时】")
            print(f"  已达到最大步数: {self.max_steps}")
            
            return {
                "success": False,
                "error": f"推理超时，已达到最大步数{self.max_steps}",
                "thought_history": [t.to_dict() for t in self.thought_history],
                "tool_results": [r.to_dict() for r in self.tool_results],
                "observation_history": self.observation_history,
                "total_steps": self.current_step,
                "final_answer": final_answer if final_answer else "推理未完成"
            }


def create_react_engine(tools: Optional[List[Dict[str, Any]]] = None) -> ReactEngine:
    """
    创建ReAct引擎实例的工厂函数
    :param tools: 可用工具列表
    :return: ReactEngine实例
    """
    return ReactEngine(
        model=create_deepseek_agent(),
        max_steps=settings.MAX_TOKENS // 500,
        retry_limit=3,
        tools=tools or []
    )


if __name__ == "__main__":
    """
    模块自测入口
    """
    print("=" * 60)
    print("ReAct推理引擎测试")
    print("=" * 60)
    
    # 创建测试工具列表
    test_tools = [
        {
            "name": "weather",
            "description": "查询指定城市的天气",
            "parameters": {"city": "城市名称"}
        },
        {
            "name": "calculator",
            "description": "执行数学计算",
            "parameters": {"expression": "数学表达式"}
        }
    ]
    
    engine = create_react_engine(test_tools)
    
    def mock_tool_executor(tool_name, parameters):
        """模拟工具执行"""
        if tool_name == "weather":
            return f"{parameters.get('city')} 今天天气晴朗，温度25度"
        elif tool_name == "calculator":
            try:
                return eval(parameters.get('expression', '0'))
            except:
                return "计算错误"
        return "未知工具"
    
    engine.set_tool_executor(mock_tool_executor)
    
    # 测试推理
    result = engine.run("北京今天天气怎么样？")
    print(f"\n测试结果: {result['success']}")
    print(f"最终答案: {result['final_answer']}")
    print(f"总步数: {result['total_steps']}")