#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整Agent集成模块
将核心推理引擎、工具层、记忆层整合为统一的Agent接口
"""

import os
import sys
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    DeepSeekChatModel,
    ReactEngine,
    TaskPlanner,
    ToolScheduler,
    create_deepseek_agent,
    create_react_engine,
    create_task_planner,
    create_tool_scheduler
)

from tools import (
    WebSearchTool,
    RAGKnowledgeTool,
    PythonExecutorTool,
    ReportGeneratorTool,
    create_web_search_tool,
    create_rag_knowledge_tool,
    create_python_executor_tool,
    create_report_generator_tool
)

from memory import (
    ShortTermMemory,
    LongTermMemory,
    create_short_term_memory,
    create_long_term_memory
)


class EnterpriseAgent:
    """
    企业级智能Agent
    整合ReAct推理引擎、工具层、记忆层的完整智能体
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Agent
        :param config: 配置字典
        """
        config = config or {}
        
        # 初始化模型
        self.model = DeepSeekChatModel(
            api_key=config.get("api_key"),
            api_base=config.get("api_base"),
            model_name=config.get("model_name", "deepseek-chat")
        )
        
        # 初始化工具调度器
        self.tool_scheduler = create_tool_scheduler()
        
        # 注册所有工具
        self._register_tools()
        
        # 获取工具信息用于ReAct引擎
        self.tools_info = self._get_tools_info()
        
        # 初始化ReAct引擎
        self.react_engine = create_react_engine(self.tools_info)
        self.react_engine.set_tool_executor(self._tool_executor)
        
        # 初始化任务规划器
        self.task_planner = create_task_planner()
        
        # 初始化记忆层
        self.short_term_memory = create_short_term_memory(
            max_messages=config.get("max_messages", 50),
            system_prompt=self._build_system_prompt()
        )
        
        self.long_term_memory = create_long_term_memory(
            storage_path=config.get("memory_path", "memory_store")
        )
        
        # 加载长期记忆
        self.long_term_memory.load_from_disk()
        
        self.conversation_history: List[Dict[str, Any]] = []
        print("[Agent] 企业级智能Agent初始化完成")
    
    def _register_tools(self):
        """注册所有企业工具"""
        self.tool_scheduler.register_tool(create_web_search_tool())
        self.tool_scheduler.register_tool(create_rag_knowledge_tool("knowledge_base"))
        self.tool_scheduler.register_tool(create_python_executor_tool())
        self.tool_scheduler.register_tool(create_report_generator_tool("reports"))
        print(f"[Agent] 已注册 {len(self.tool_scheduler.get_all_tools())} 个工具")
    
    def _get_tools_info(self) -> List[Dict[str, Any]]:
        """获取工具信息列表"""
        tools_info = []
        for tool in self.tool_scheduler.get_all_tools():
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        return tools_info
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        prompt = """你是一个轻量化企业多工具协同自主规划办公智能Agent，采用ReAct推理框架进行思考和行动。

核心能力：
1. 联网检索：获取最新信息和数据
2. 文档知识库：检索企业文档和知识库
3. Python代码执行：进行数据分析和计算
4. 报告生成：生成Excel和Markdown格式的报告

工作流程：
1. 分析用户需求，判断需要使用哪些工具
2. 使用任务规划器分解复杂任务
3. 通过ReAct推理循环逐步执行
4. 整合结果，给出完整回答

推理格式要求：
[THOUGHT]
你的思考内容

[ACTION]
action_type: 工具名称或"finish"
parameters: 参数（JSON格式）

注意事项：
- 始终使用中文回复
- 保持回答简洁明了
- 如果需要调用工具，按照指定格式输出
- 如果直接回答用户，action_type设为"finish"
"""
        return prompt
    
    def _tool_executor(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        工具执行器
        :param tool_name: 工具名称
        :param parameters: 工具参数
        :return: 执行结果
        """
        result = self.tool_scheduler.execute_tool(tool_name, parameters)
        
        if result.success:
            return str(result.result)
        else:
            return f"工具执行失败 [{tool_name}]: {result.error}"
    
    def _retrieve_long_term_memory(self, query: str) -> str:
        """
        检索长期记忆
        :param query: 查询文本
        :return: 相关记忆内容
        """
        results = self.long_term_memory.search(query, top_k=3)
        
        if not results:
            return ""
        
        memory_content = "\n[相关记忆]\n"
        for i, result in enumerate(results, 1):
            entry = result["entry"]
            memory_content += f"{i}. {entry.content[:150]}... (相似度: {result['similarity']:.2f})\n"
        
        return memory_content
    
    def _save_to_long_term_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        保存内容到长期记忆
        :param content: 内容
        :param metadata: 元数据
        """
        self.long_term_memory.add_memory(content, metadata)
    
    def chat(self, user_input: str) -> Dict[str, Any]:
        """
        核心聊天接口
        :param user_input: 用户输入
        :return: 聊天结果
        """
        print(f"\n[Agent] 用户输入: {user_input}")
        
        # 添加用户消息到短期记忆
        self.short_term_memory.add_user_message(user_input)
        
        # 检索长期记忆
        memory_context = self._retrieve_long_term_memory(user_input)
        
        # 如果有长期记忆，添加到上下文中
        if memory_context:
            print("[Agent] 检索到相关长期记忆")
        
        # 执行ReAct推理
        enhanced_input = user_input + "\n\n" + memory_context if memory_context else user_input
        result = self.react_engine.run(enhanced_input)
        
        # 添加助手回复到短期记忆
        self.short_term_memory.add_assistant_message(result["final_answer"])
        
        # 保存关键信息到长期记忆
        if result["success"]:
            self._save_to_long_term_memory(
                content=f"用户问: {user_input[:50]}...\n回答: {result['final_answer'][:100]}...",
                metadata={"type": "chat", "steps": result["total_steps"]}
            )
        
        # 保存长期记忆到磁盘
        self.long_term_memory.save_to_disk()
        
        # 记录对话历史
        self.conversation_history.append({
            "user": user_input,
            "assistant": result["final_answer"],
            "steps": result["total_steps"],
            "thoughts": result.get("thought_history", [])
        })
        
        print(f"[Agent] 回复成功，共 {result['total_steps']} 步")
        
        return {
            "success": result["success"],
            "answer": result["final_answer"],
            "total_steps": result["total_steps"],
            "thought_history": result.get("thought_history", []),
            "tool_results": result.get("tool_results", []),
            "memory_retrieved": bool(memory_context)
        }
    
    def plan_task(self, task_description: str) -> Dict[str, Any]:
        """
        任务规划接口
        :param task_description: 任务描述
        :return: 规划结果
        """
        print(f"\n[Agent] 任务规划: {task_description}")
        
        plan = self.task_planner.plan(task_description, self.tools_info)
        sorted_plan = self.task_planner.sort_by_dependencies(plan)
        estimated_time = self.task_planner.estimate_total_time(plan)
        
        return {
            "success": True,
            "original_task": task_description,
            "subtasks": [subtask.to_dict() for subtask in sorted_plan.subtasks],
            "total_subtasks": len(sorted_plan.subtasks),
            "estimated_time_minutes": estimated_time
        }
    
    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务规划
        :param plan: 任务规划
        :return: 执行结果
        """
        print(f"\n[Agent] 执行任务规划，共 {plan['total_subtasks']} 个子任务")
        
        results = []
        
        for i, subtask in enumerate(plan["subtasks"], 1):
            print(f"  [步骤{i}] {subtask['description']}")
            
            result = self.chat(subtask["description"])
            results.append({
                "subtask_id": subtask["task_id"],
                "description": subtask["description"],
                "success": result["success"],
                "answer": result["answer"]
            })
        
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "results": results,
            "completed_tasks": len([r for r in results if r["success"]]),
            "total_tasks": len(results)
        }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history
    
    def clear_conversation(self):
        """清空对话"""
        self.short_term_memory.clear()
        self.conversation_history = []
        print("[Agent] 对话已清空")
    
    def reset(self):
        """完全重置Agent"""
        self.short_term_memory.reset()
        self.long_term_memory.clear()
        self.conversation_history = []
        print("[Agent] Agent已重置")
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "model_name": self.model.model_name,
            "tool_count": len(self.tool_scheduler.get_all_tools()),
            "short_term_messages": self.short_term_memory.get_message_count(),
            "long_term_memories": self.long_term_memory.get_memory_count(),
            "conversation_history_length": len(self.conversation_history)
        }


def create_enterprise_agent(config: Optional[Dict[str, Any]] = None) -> EnterpriseAgent:
    """
    工厂函数：创建企业级Agent实例
    :param config: 配置字典
    :return: EnterpriseAgent实例
    """
    return EnterpriseAgent(config)


def create_default_agent() -> EnterpriseAgent:
    """
    创建默认配置的Agent
    :return: EnterpriseAgent实例
    """
    return EnterpriseAgent()