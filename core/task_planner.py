#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务拆解与规划器
实现复杂任务的自动拆解、优先级排序、步骤规划

面试高频考点：
1. 任务拆解的算法策略（递归拆解、启发式搜索）
2. 任务优先级评估模型
3. 依赖关系分析与拓扑排序
4. 规划结果的可执行性验证
5. 动态规划调整策略
"""

import os
import sys
from typing import List, Dict, Any, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings
from .deepseek_model import create_deepseek_agent

settings = get_settings()


class TaskPriority(Enum):
    """
    任务优先级枚举
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """
    任务状态枚举
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class SubTask:
    """
    子任务封装
    """
    
    def __init__(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        estimated_time: Optional[int] = None,
        tool_required: Optional[str] = None,
        status: TaskStatus = TaskStatus.PENDING
    ):
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.dependencies = dependencies or []
        self.estimated_time = estimated_time
        self.tool_required = tool_required
        self.status = status
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "estimated_time": self.estimated_time,
            "tool_required": self.tool_required,
            "status": self.status.value,
            "result": str(self.result) if self.result else None,
            "error": self.error
        }


class TaskPlan:
    """
    任务规划结果封装
    """
    
    def __init__(self, main_task: str, subtasks: List[SubTask]):
        self.main_task = main_task
        self.subtasks = subtasks
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "main_task": self.main_task,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "total_tasks": len(self.subtasks),
            "pending_tasks": sum(1 for t in self.subtasks if t.status == TaskStatus.PENDING),
            "completed_tasks": sum(1 for t in self.subtasks if t.status == TaskStatus.COMPLETED)
        }


class TaskPlanner:
    """
    任务拆解与规划器
    将复杂任务拆解为可执行的子任务序列
    """
    
    def __init__(self):
        """
        初始化任务规划器
        """
        self.model = create_deepseek_agent()
    
    def _build_prompt(self, task_description: str, tools: List[Dict[str, Any]] = None) -> str:
        """
        构建任务拆解提示词
        :param task_description: 任务描述
        :param tools: 可用工具列表
        :return: 提示词
        """
        tools_desc = ""
        if tools:
            tools_desc = "\n可用工具列表（拆解时考虑是否需要调用）：\n"
            for tool in tools:
                tools_desc += f"- {tool['name']}: {tool['description']}\n"
        
        return f"""你是一个任务规划专家，请将用户的复杂任务拆解为一系列可执行的子任务。

任务：{task_description}

{tools_desc}

拆解要求：
1. 将任务拆解为3-10个子任务
2. 每个子任务必须是独立的、可执行的
3. 明确子任务之间的依赖关系
4. 评估每个子任务的优先级（critical/high/medium/low）
5. 判断每个子任务是否需要调用工具，如果需要，指出工具名称
6. 估算每个子任务的执行时间（分钟）

输出格式（JSON）：
{{
  "analysis": "对任务的分析和拆解思路",
  "subtasks": [
    {{
      "task_id": "T001",
      "description": "子任务描述",
      "priority": "critical",
      "dependencies": ["T002"],
      "estimated_time": 5,
      "tool_required": "weather"
    }}
  ]
}}

注意：dependencies为空数组表示无依赖，可以最先执行。
"""
    
    def _parse_plan(self, response: str) -> Dict[str, Any]:
        """
        解析模型返回的任务规划
        :param response: 模型响应
        :return: 解析后的规划数据
        """
        try:
            import json
            
            # 尝试提取JSON部分
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            # 如果没有找到JSON，返回默认格式
            return {
                "analysis": response,
                "subtasks": []
            }
        except Exception as e:
            return {
                "analysis": f"解析失败: {str(e)}",
                "subtasks": []
            }
    
    def plan(self, task_description: str, tools: List[Dict[str, Any]] = None) -> TaskPlan:
        """
        执行任务拆解与规划
        :param task_description: 任务描述
        :param tools: 可用工具列表
        :return: TaskPlan对象
        """
        print("\n【任务规划】开始拆解任务")
        print(f"  原始任务: {task_description}")
        
        prompt = self._build_prompt(task_description, tools)
        response = self.model.invoke(prompt)
        
        if not response.get("success"):
            print(f"  [ERR] 模型调用失败: {response.get('error')}")
            return TaskPlan(task_description, [])
        
        content = response.get("content", "")
        parsed_plan = self._parse_plan(content)
        
        print(f"  [分析] {parsed_plan.get('analysis', '')[:100]}...")
        
        subtasks = []
        for i, subtask_data in enumerate(parsed_plan.get("subtasks", []), 1):
            priority = TaskPriority(subtask_data.get("priority", "medium"))
            status = TaskStatus.PENDING
            
            subtask = SubTask(
                task_id=subtask_data.get("task_id", f"T{i:03d}"),
                description=subtask_data.get("description", ""),
                priority=priority,
                dependencies=subtask_data.get("dependencies", []),
                estimated_time=subtask_data.get("estimated_time"),
                tool_required=subtask_data.get("tool_required"),
                status=status
            )
            
            subtasks.append(subtask)
            print(f"  [子任务 {subtask.task_id}] {subtask.description} (优先级: {subtask.priority.value})")
        
        print(f"  [完成] 共拆解为 {len(subtasks)} 个子任务")
        
        return TaskPlan(task_description, subtasks)
    
    def sort_by_dependencies(self, plan: TaskPlan) -> TaskPlan:
        """
        根据依赖关系对任务进行拓扑排序
        :param plan: 任务规划
        :return: 排序后的任务规划
        """
        subtasks_dict = {t.task_id: t for t in plan.subtasks}
        sorted_tasks = []
        visited = set()
        
        def dfs(task_id):
            """深度优先搜索处理依赖"""
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = subtasks_dict.get(task_id)
            if not task:
                return
            
            # 先处理依赖的任务
            for dep_id in task.dependencies:
                dfs(dep_id)
            
            sorted_tasks.append(task)
        
        # 按优先级排序后进行拓扑排序
        priority_order = [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
        
        for priority in priority_order:
            for task in plan.subtasks:
                if task.priority == priority and task.task_id not in visited:
                    dfs(task.task_id)
        
        return TaskPlan(plan.main_task, sorted_tasks)
    
    def estimate_total_time(self, plan: TaskPlan) -> int:
        """
        估算总执行时间
        :param plan: 任务规划
        :return: 总时间（分钟）
        """
        total_time = 0
        for task in plan.subtasks:
            if task.estimated_time:
                total_time += task.estimated_time
        
        return total_time


def create_task_planner() -> TaskPlanner:
    """
    创建任务规划器实例的工厂函数
    :return: TaskPlanner实例
    """
    return TaskPlanner()


if __name__ == "__main__":
    """
    模块自测入口
    """
    print("=" * 60)
    print("任务规划器测试")
    print("=" * 60)
    
    planner = create_task_planner()
    
    test_tools = [
        {"name": "web_search", "description": "联网搜索信息"},
        {"name": "calculator", "description": "数学计算"},
        {"name": "file_read", "description": "读取文件内容"}
    ]
    
    task = "分析2024年AI行业发展趋势，生成一份详细报告"
    plan = planner.plan(task, test_tools)
    
    print(f"\n任务分析: {plan.subtasks[0].to_dict()}")
    print(f"\n总任务数: {len(plan.subtasks)}")
    print(f"总预估时间: {planner.estimate_total_time(plan)} 分钟")
    
    sorted_plan = planner.sort_by_dependencies(plan)
    print("\n排序后的执行顺序:")
    for task in sorted_plan.subtasks:
        print(f"  {task.task_id}: {task.description}")