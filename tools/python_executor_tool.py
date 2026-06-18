#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python代码执行工具
提供安全的代码沙箱执行环境，支持数据分析和计算
"""

import sys
import io
import traceback
import time
from typing import Dict, Any, List
from contextlib import redirect_stdout, redirect_stderr
from core import BaseTool


class PythonExecutorTool(BaseTool):
    """
    Python代码执行工具
    提供安全的代码执行环境，支持数据分析、计算等任务
    """
    
    name = "python_executor"
    description = "执行Python代码，支持数据分析、计算和可视化"
    parameters = {
        "code": {
            "type": "string",
            "description": "要执行的Python代码",
            "required": True
        },
        "timeout": {
            "type": "integer",
            "description": "执行超时时间（秒）",
            "required": False
        },
        "libraries": {
            "type": "array",
            "description": "需要导入的库列表",
            "required": False
        }
    }
    
    def __init__(self, timeout: int = 30):
        """
        初始化Python执行器
        :param timeout: 默认超时时间
        """
        super().__init__()
        self.default_timeout = timeout
        self.global_vars = {}
        self.local_vars = {}
        
        # 预导入常用库
        self._setup_environment()
    
    def _setup_environment(self):
        """设置执行环境，预导入常用库"""
        try:
            import numpy as np
            self.global_vars['np'] = np
        except ImportError:
            pass
        
        try:
            import pandas as pd
            self.global_vars['pd'] = pd
        except ImportError:
            pass
        
        try:
            import math
            self.global_vars['math'] = math
        except ImportError:
            pass
        
        try:
            import json
            self.global_vars['json'] = json
        except ImportError:
            pass
        
        try:
            import re
            self.global_vars['re'] = re
        except ImportError:
            pass
        
        # 添加常用函数
        self.global_vars['print'] = self._safe_print
        self.global_vars['len'] = len
        self.global_vars['range'] = range
        self.global_vars['sum'] = sum
        self.global_vars['max'] = max
        self.global_vars['min'] = min
        self.global_vars['abs'] = abs
        self.global_vars['round'] = round
    
    def _safe_print(self, *args, **kwargs):
        """安全的print函数，将输出重定向到字符串"""
        output = io.StringIO()
        with redirect_stdout(output):
            print(*args, **kwargs)
        return output.getvalue()
    
    def _check_code_safety(self, code: str) -> tuple[bool, str]:
        """
        检查代码安全性
        :param code: 要检查的代码
        :return: (是否安全, 错误信息)
        """
        # 危险操作黑名单
        dangerous_patterns = [
            '__import__',
            'eval(',
            'exec(',
            'compile(',
            'open(',
            'file(',
            'input(',
            'raw_input(',
            'globals(',
            'locals(',
            'vars(',
            'dir(',
            'hasattr(',
            'getattr(',
            'setattr(',
            'delattr(',
            'property(',
            'super(',
            'type(',
            'isinstance(',
            'issubclass(',
            '__class__',
            '__bases__',
            '__mro__',
            '__subclasses__',
            '__code__',
            '__func__',
            '__self__',
            '__closure__',
            '__globals__',
            '__builtins__',
            'import os',
            'import sys',
            'import subprocess',
            'import socket',
            'import urllib',
            'import http',
            'import ftplib',
            'import smtplib',
            'import poplib',
            'import imaplib',
            'import telnetlib',
            'from os import',
            'from sys import',
            'from subprocess import',
            'from socket import',
            'from urllib import',
            'from http import',
            'from ftplib import',
            'from smtplib import',
            'from poplib import',
            'from imaplib import',
            'from telnetlib import',
        ]
        
        code_lower = code.lower()
        
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return False, f"代码包含危险操作: {pattern}"
        
        return True, ""
    
    def _execute_code(self, code: str, timeout: int) -> Dict[str, Any]:
        """
        执行Python代码
        :param code: 要执行的代码
        :param timeout: 超时时间
        :return: 执行结果字典
        """
        # 捕获输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result = {
            "success": False,
            "output": "",
            "error": "",
            "execution_time": 0,
            "variables": {}
        }
        
        start_time = time.time()
        
        try:
            # 重定向输出
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # 执行代码
                exec(code, self.global_vars, self.local_vars)
            
            # 获取输出
            stdout_value = stdout_capture.getvalue()
            stderr_value = stderr_capture.getvalue()
            
            # 计算执行时间
            execution_time = time.time() - start_time
            result["execution_time"] = round(execution_time, 3)
            
            # 组合输出
            output_parts = []
            if stdout_value:
                output_parts.append(stdout_value)
            if stderr_value:
                output_parts.append(f"警告: {stderr_value}")
            
            result["output"] = "\n".join(output_parts)
            result["success"] = True
            
            # 获取变量值（仅限基本类型）
            for key, value in self.local_vars.items():
                if not key.startswith('_'):
                    try:
                        # 只序列化简单类型
                        if isinstance(value, (int, float, str, bool, list, dict, tuple)):
                            result["variables"][key] = value
                    except:
                        pass
            
        except Exception as e:
            execution_time = time.time() - start_time
            result["execution_time"] = round(execution_time, 3)
            result["error"] = f"{type(e).__name__}: {str(e)}"
            result["output"] = stdout_capture.getvalue()
            
            # 添加堆栈跟踪
            tb_str = traceback.format_exc()
            result["error"] += f"\n\n堆栈跟踪:\n{tb_str}"
        
        return result
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """
        格式化执行结果
        :param result: 执行结果字典
        :return: 格式化文本
        """
        formatted = ""
        
        if result["success"]:
            formatted += "✅ 代码执行成功\n"
            formatted += f"⏱️ 执行时间: {result['execution_time']}秒\n\n"
            
            if result["output"]:
                formatted += "📤 输出结果:\n"
                formatted += "-" * 40 + "\n"
                formatted += result["output"]
                formatted += "\n" + "-" * 40 + "\n\n"
            
            if result["variables"]:
                formatted += "📊 定义的变量:\n"
                for key, value in result["variables"].items():
                    formatted += f"  {key} = {value}\n"
        else:
            formatted += "❌ 代码执行失败\n"
            formatted += f"⏱️ 执行时间: {result['execution_time']}秒\n\n"
            
            if result["output"]:
                formatted += "📤 部分输出:\n"
                formatted += result["output"] + "\n\n"
            
            formatted += "⚠️ 错误信息:\n"
            formatted += "-" * 40 + "\n"
            formatted += result["error"]
            formatted += "\n" + "-" * 40 + "\n"
        
        return formatted
    
    def execute(self, **kwargs) -> str:
        """
        执行Python代码
        :param kwargs: 包含code, timeout, libraries等参数
        :return: 执行结果文本
        """
        code = kwargs.get("code", "")
        timeout = kwargs.get("timeout", self.default_timeout)
        libraries = kwargs.get("libraries", [])
        
        if not code:
            return "错误: 代码内容不能为空"
        
        print(f"[代码执行] 准备执行代码 ({len(code)} 字符)")
        
        # 安全检查
        is_safe, safety_error = self._check_code_safety(code)
        if not is_safe:
            print(f"[代码执行] 安全检查失败: {safety_error}")
            return f"安全检查失败: {safety_error}"
        
        # 导入额外库
        for lib in libraries:
            try:
                exec(f"import {lib}", self.global_vars)
                print(f"[代码执行] 已导入库: {lib}")
            except ImportError as e:
                print(f"[代码执行] 导入库失败: {lib} - {str(e)}")
                return f"无法导入库 {lib}: {str(e)}"
        
        print(f"[代码执行] 开始执行 (超时: {timeout}秒)")
        
        # 执行代码
        result = self._execute_code(code, timeout)
        
        formatted_result = self._format_result(result)
        
        if result["success"]:
            print(f"[代码执行] 执行成功，耗时 {result['execution_time']}秒")
        else:
            print(f"[代码执行] 执行失败: {result['error'][:50]}...")
        
        return formatted_result
    
    def reset_environment(self):
        """重置执行环境"""
        self.global_vars = {}
        self.local_vars = {}
        self._setup_environment()
        print("[代码执行] 环境已重置")


def create_python_executor_tool(timeout: int = 30) -> PythonExecutorTool:
    """
    工厂函数：创建Python执行器工具实例
    :param timeout: 默认超时时间
    :return: PythonExecutorTool实例
    """
    return PythonExecutorTool(timeout)