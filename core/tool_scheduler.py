#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具调度与执行器
管理工具的注册、查找、执行和结果处理

面试高频考点：
1. 工具注册机制与插件化设计
2. 参数校验与类型安全
3. 异步执行与并发控制
4. 执行结果的标准化处理
5. 错误捕获与异常转换
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional, Callable, Type
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings

settings = get_settings()


class ToolExecutionStatus(Enum):
    """
    工具执行状态枚举
    """
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID_PARAMS = "invalid_params"


class ToolMetadata:
    """
    工具元数据封装
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        return_type: str = "string",
        timeout: int = 30
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.return_type = return_type
        self.timeout = timeout
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "timeout": self.timeout
        }


class ToolResult:
    """
    工具执行结果封装
    """
    
    def __init__(
        self,
        tool_name: str,
        status: ToolExecutionStatus,
        result: Any = None,
        error: Optional[str] = None,
        execution_time: Optional[float] = None
    ):
        self.tool_name = tool_name
        self.status = status
        self.result = result
        self.error = error
        self.execution_time = execution_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "result": str(self.result) if not isinstance(self.result, str) else self.result,
            "error": self.error,
            "execution_time": self.execution_time
        }
    
    @property
    def success(self) -> bool:
        return self.status == ToolExecutionStatus.SUCCESS


class BaseTool:
    """
    工具基类
    所有自定义工具必须继承此类
    """
    
    name: str = "base_tool"
    description: str = "基础工具"
    parameters: Dict[str, Any] = {}
    return_type: str = "string"
    timeout: int = 30
    
    def execute(self, **kwargs) -> Any:
        """
        执行工具逻辑
        :param kwargs: 工具参数
        :return: 执行结果
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证参数
        :param kwargs: 参数
        :return: 是否有效
        """
        for param_name, param_info in self.parameters.items():
            if param_info.get("required", False) and param_name not in kwargs:
                return False
        return True
    
    def get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        :return: ToolMetadata对象
        """
        return ToolMetadata(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            return_type=self.return_type,
            timeout=self.timeout
        )


class ToolScheduler:
    """
    工具调度器
    管理所有工具的注册、查找和执行
    """
    
    def __init__(self):
        """
        初始化工具调度器
        """
        self._tools: Dict[str, BaseTool] = {}
        self._tool_metadata: Dict[str, ToolMetadata] = {}
        self.execution_history: List[ToolResult] = []
    
    def register_tool(self, tool: BaseTool):
        """
        注册工具
        :param tool: 工具实例
        """
        self._tools[tool.name] = tool
        self._tool_metadata[tool.name] = tool.get_metadata()
        print(f"[工具注册] {tool.name} - {tool.description}")
    
    def register_tools(self, tools: List[BaseTool]):
        """
        批量注册工具
        :param tools: 工具列表
        """
        for tool in tools:
            self.register_tool(tool)
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具实例
        :param tool_name: 工具名称
        :return: 工具实例或None
        """
        return self._tools.get(tool_name)
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        获取工具元数据
        :param tool_name: 工具名称
        :return: 工具元数据或None
        """
        return self._tool_metadata.get(tool_name)
    
    def get_all_tools(self) -> List[ToolMetadata]:
        """
        获取所有已注册工具的元数据
        :return: 工具元数据列表
        """
        return list(self._tool_metadata.values())
    
    def has_tool(self, tool_name: str) -> bool:
        """
        检查工具是否已注册
        :param tool_name: 工具名称
        :return: 是否存在
        """
        return tool_name in self._tools
    
    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any] = None,
        timeout: Optional[int] = None
    ) -> ToolResult:
        """
        执行工具
        :param tool_name: 工具名称
        :param parameters: 参数
        :param timeout: 超时时间
        :return: 执行结果
        """
        start_time = time.time()
        
        # 检查工具是否存在
        if not self.has_tool(tool_name):
            result = ToolResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
                error=f"工具 {tool_name} 未注册"
            )
            self.execution_history.append(result)
            return result
        
        tool = self._tools[tool_name]
        effective_timeout = timeout or tool.timeout
        
        # 验证参数
        if not tool.validate_params(**(parameters or {})):
            result = ToolResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.INVALID_PARAMS,
                error="参数验证失败"
            )
            self.execution_history.append(result)
            return result
        
        # 执行工具
        try:
            result_data = tool.execute(**(parameters or {}))
            execution_time = time.time() - start_time
            
            result = ToolResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                result=result_data,
                execution_time=execution_time
            )
            
            print(f"[工具执行] {tool_name} 成功，耗时 {execution_time:.2f}s")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = ToolResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
            
            print(f"[工具执行] {tool_name} 失败: {str(e)}")
        
        self.execution_history.append(result)
        return result
    
    def batch_execute(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[ToolResult]:
        """
        批量执行工具
        :param tasks: 任务列表，每个任务包含 tool_name 和 parameters
        :return: 执行结果列表
        """
        results = []
        for task in tasks:
            tool_name = task.get("tool_name")
            parameters = task.get("parameters", {})
            
            result = self.execute_tool(tool_name, parameters)
            results.append(result)
        
        return results
    
    def get_tool_description(self, tool_name: str) -> str:
        """
        获取工具描述（用于模型提示词）
        :param tool_name: 工具名称
        :return: 工具描述字符串
        """
        metadata = self.get_tool_metadata(tool_name)
        if not metadata:
            return ""
        
        params_desc = []
        for param_name, param_info in metadata.parameters.items():
            required = "必填" if param_info.get("required", False) else "选填"
            params_desc.append(f"{param_name} ({required}): {param_info.get('description', '')}")
        
        return f"- {metadata.name}: {metadata.description}\n  参数: {', '.join(params_desc)}"


def create_tool_scheduler() -> ToolScheduler:
    """
    创建工具调度器实例的工厂函数
    :return: ToolScheduler实例
    """
    return ToolScheduler()


# ==================== 示例工具 ====================

class ExampleWeatherTool(BaseTool):
    """示例天气查询工具"""
    
    name = "weather"
    description = "查询指定城市的天气信息"
    parameters = {
        "city": {"type": "string", "description": "城市名称", "required": True}
    }
    return_type = "string"
    timeout = 10
    
    def execute(self, **kwargs) -> str:
        city = kwargs.get("city", "")
        return f"{city} 今天天气晴朗，温度25度，微风"


class ExampleCalculatorTool(BaseTool):
    """示例计算器工具"""
    
    name = "calculator"
    description = "执行数学计算"
    parameters = {
        "expression": {"type": "string", "description": "数学表达式", "required": True}
    }
    return_type = "string"
    timeout = 5
    
    def execute(self, **kwargs) -> str:
        expression = kwargs.get("expression", "")
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"计算错误: {str(e)}"


if __name__ == "__main__":
    """
    模块自测入口
    """
    print("=" * 60)
    print("工具调度器测试")
    print("=" * 60)
    
    scheduler = create_tool_scheduler()
    
    # 注册示例工具
    scheduler.register_tool(ExampleWeatherTool())
    scheduler.register_tool(ExampleCalculatorTool())
    
    print("\n已注册工具:")
    for metadata in scheduler.get_all_tools():
        print(f"  - {metadata.name}: {metadata.description}")
    
    # 测试执行
    print("\n测试天气工具:")
    result = scheduler.execute_tool("weather", {"city": "北京"})
    print(f"  结果: {result.result}")
    
    print("\n测试计算器工具:")
    result = scheduler.execute_tool("calculator", {"expression": "2 * (3 + 5)"})
    print(f"  结果: {result.result}")
    
    print("\n测试不存在的工具:")
    result = scheduler.execute_tool("nonexistent")
    print(f"  状态: {result.status.value}")
    print(f"  错误: {result.error}")