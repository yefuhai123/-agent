#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit可视化界面
为企业级智能Agent提供友好的Web交互界面
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from typing import Dict, Any, List

from agent import create_enterprise_agent
from memory import create_short_term_memory, create_long_term_memory


def init_session_state():
    """初始化Streamlit会话状态"""
    if "agent" not in st.session_state:
        st.session_state.agent = create_enterprise_agent()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    
    if "current_task" not in st.session_state:
        st.session_state.current_task = None


def render_header():
    """渲染页面头部"""
    st.set_page_config(
        page_title="企业智能Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 轻量化企业多工具协同自主规划办公智能Agent")
    st.subheader("基于ReAct框架的企业级智能助手")
    
    # Agent状态信息
    status = st.session_state.agent.get_status()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("模型", status["model_name"])
    with col2:
        st.metric("工具数量", status["tool_count"])
    with col3:
        st.metric("对话消息", status["short_term_messages"])
    with col4:
        st.metric("长期记忆", status["long_term_memories"])


def render_chat_area():
    """渲染聊天区域"""
    # 聊天历史
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(message["content"])
                
                # 显示思考过程
                if "thoughts" in message:
                    with st.expander("查看思考过程"):
                        for thought in message["thoughts"]:
                            st.markdown(f"**思考 {thought.get('step', '')}:** {thought.get('content', '')}")
                            if thought.get("tool_name"):
                                st.markdown(f"**工具:** {thought.get('tool_name')}")
                                st.markdown(f"**参数:** {thought.get('tool_args', {})}")
                
                # 显示步骤信息
                if "steps" in message:
                    st.caption(f"推理步骤: {message['steps']}")
    
    # 用户输入
    user_input = st.chat_input("请输入您的问题...")
    
    if user_input and not st.session_state.is_loading:
        st.session_state.is_loading = True
        
        # 添加用户消息到历史
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # 调用Agent
        with st.spinner("Agent正在思考..."):
            result = st.session_state.agent.chat(user_input)
        
        # 添加助手回复到历史
        assistant_message = {
            "role": "assistant",
            "content": result["answer"],
            "steps": result["total_steps"]
        }
        
        if result.get("thought_history"):
            assistant_message["thoughts"] = [t.to_dict() for t in result["thought_history"]]
        
        st.session_state.chat_history.append(assistant_message)
        
        st.session_state.is_loading = False
        
        # 刷新页面显示最新消息
        st.rerun()


def render_task_planner():
    """渲染任务规划面板"""
    st.header("📋 任务规划")
    
    task_input = st.text_area("请输入任务描述:", height=100)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("规划任务"):
            if task_input:
                with st.spinner("正在规划任务..."):
                    plan = st.session_state.agent.plan_task(task_input)
                
                st.success(f"任务已分解为 {plan['total_subtasks']} 个子任务")
                
                # 显示子任务
                for subtask in plan["subtasks"]:
                    st.markdown(f"**{subtask['task_id']}:** {subtask['description']}")
                    st.markdown(f"   优先级: {subtask['priority']}")
                    if subtask["dependencies"]:
                        st.markdown(f"   依赖: {', '.join(subtask['dependencies'])}")
                
                st.info(f"预估总时间: {plan['estimated_time_minutes']} 分钟")
                
                # 保存规划
                st.session_state.current_task = plan
    
    with col2:
        if st.button("执行规划") and st.session_state.current_task:
            with st.spinner("正在执行任务..."):
                execution_result = st.session_state.agent.execute_plan(st.session_state.current_task)
            
            if execution_result["success"]:
                st.success(f"任务执行完成！完成 {execution_result['completed_tasks']}/{execution_result['total_tasks']}")
            else:
                st.warning(f"部分任务执行失败，完成 {execution_result['completed_tasks']}/{execution_result['total_tasks']}")


def render_memory_panel():
    """渲染记忆管理面板"""
    st.header("🧠 记忆管理")
    
    tab1, tab2 = st.tabs(["短期记忆", "长期记忆"])
    
    with tab1:
        st.subheader("对话历史")
        messages = st.session_state.agent.short_term_memory.get_messages(format_type="dict")
        
        if messages:
            for i, msg in enumerate(messages[-10:], 1):
                role_color = "blue" if msg["role"] == "user" else "green"
                st.markdown(f"<span style='color:{role_color}'>{msg['role']}:</span> {msg['content'][:100]}...", unsafe_allow_html=True)
        
        if st.button("清空对话"):
            st.session_state.agent.clear_conversation()
            st.session_state.chat_history = []
            st.success("对话已清空")
    
    with tab2:
        st.subheader("长期记忆")
        memories = st.session_state.agent.long_term_memory.get_recent_memories(10)
        
        if memories:
            for i, entry in enumerate(memories, 1):
                st.markdown(f"**记忆 {i}:** {entry.content[:150]}...")
                st.markdown(f"   时间: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")
        
        st.metric("长期记忆总数", st.session_state.agent.long_term_memory.get_memory_count())


def render_tool_panel():
    """渲染工具管理面板"""
    st.header("🛠️ 工具管理")
    
    tools = st.session_state.agent.tool_scheduler.get_all_tools()
    
    for tool in tools:
        with st.expander(f"{tool.name} - {tool.description}"):
            st.markdown("**参数:**")
            for param_name, param_info in tool.parameters.items():
                st.markdown(f"- {param_name}: {param_info.get('description', '')}")
                st.markdown(f"   类型: {param_info.get('type', 'string')}")
                st.markdown(f"   必填: {param_info.get('required', False)}")


def main():
    """主函数"""
    init_session_state()
    
    render_header()
    
    # 主布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_chat_area()
    
    with col2:
        render_task_planner()
        render_memory_panel()
        render_tool_panel()


if __name__ == "__main__":
    main()