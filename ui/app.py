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
import tempfile

from agent import create_enterprise_agent
from memory import create_short_term_memory, create_long_term_memory


# ==================== 新增：文档处理函数 ====================
def process_uploaded_document(file_content: bytes, file_name: str, file_type: str) -> List[str]:
    """
    处理上传的文档，提取文本并进行分割
    :param file_content: 文件内容（字节）
    :param file_name: 文件名
    :param file_type: 文件类型
    :return: 分割后的文本片段列表
    """
    text_chunks = []
    
    try:
        # 根据文件类型提取文本
        if file_type == "txt" or file_type == "md":
            # 直接读取文本文件
            text = file_content.decode('utf-8', errors='ignore')
            text_chunks = split_text(text, chunk_size=500, overlap=50)
        
        elif file_type == "pdf":
            # PDF文件处理
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(tempfile.NamedTemporaryFile(delete=False, suffix='.pdf'))
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(file_content)
                temp_file.close()
                
                pdf_reader = PyPDF2.PdfReader(temp_file.name)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                text_chunks = split_text(text, chunk_size=500, overlap=50)
                os.unlink(temp_file.name)
            except ImportError:
                st.warning("PDF处理需要安装PyPDF2库: pip install PyPDF2")
                return []
        
        elif file_type == "docx":
            # Word文档处理
            try:
                import docx
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
                temp_file.write(file_content)
                temp_file.close()
                
                doc = docx.Document(temp_file.name)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                
                text_chunks = split_text(text, chunk_size=500, overlap=50)
                os.unlink(temp_file.name)
            except ImportError:
                st.warning("Word文档处理需要安装python-docx库: pip install python-docx")
                return []
        
        return text_chunks
    
    except Exception as e:
        st.error(f"文档处理失败: {str(e)}")
        return []


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    文本分割函数
    :param text: 原始文本
    :param chunk_size: 每个片段的大小
    :param overlap: 片段之间的重叠
    :return: 分割后的文本片段列表
    """
    if not text:
        return []
    
    # 清理文本
    text = text.strip()
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 尝试在句子边界分割
        if end < len(text):
            # 寻找最近的句子结束符
            for i in range(end, max(start, end - 100), -1):
                if text[i] in ['。', '！', '？', '.', '!', '?', '\n']:
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def add_document_to_memory(agent, text_chunks: List[str], file_name: str) -> int:
    """
    将文档片段添加到长期记忆库
    :param agent: Agent实例
    :param text_chunks: 文本片段列表
    :param file_name: 源文件名
    :return: 成功添加的记忆数量
    """
    added_count = 0
    
    for i, chunk in enumerate(text_chunks):
        if chunk:
            # 添加元数据
            metadata = {
                "source": file_name,
                "chunk_index": i,
                "total_chunks": len(text_chunks),
                "type": "document"
            }
            
            # 添加到长期记忆（自动进行向量化）
            agent.long_term_memory.add_memory(
                content=chunk,
                metadata=metadata
            )
            added_count += 1
    
    # 保存到磁盘
    agent.long_term_memory.save_to_disk()
    
    return added_count
# ==================== 新增代码块结束 ====================


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
            assistant_message["thoughts"] = result["thought_history"]
        
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
        
        # ==================== 新增：文档上传功能 ====================
        st.markdown("---")
        st.markdown("### 📄 文档上传")
        st.markdown("上传文档自动提取文本、分割、向量化并存入长期记忆库")
        
        # 文件上传组件（支持批量多选）
        uploaded_files = st.file_uploader(
            "选择文档文件",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            help="支持PDF、Word文档、文本文件和Markdown文件，可批量上传"
        )
        
        # 处理上传的文件
        if uploaded_files:
            process_button = st.button("处理并存入记忆库", type="primary")
            
            if process_button:
                total_chunks_added = 0
                processed_files = []
                
                with st.spinner("正在处理文档..."):
                    for uploaded_file in uploaded_files:
                        # 获取文件信息
                        file_name = uploaded_file.name
                        file_type = file_name.split('.')[-1].lower()
                        file_content = uploaded_file.read()
                        
                        # 处理文档
                        st.info(f"正在处理: {file_name}")
                        text_chunks = process_uploaded_document(file_content, file_name, file_type)
                        
                        if text_chunks:
                            # 添加到长期记忆库
                            added_count = add_document_to_memory(
                                st.session_state.agent,
                                text_chunks,
                                file_name
                            )
                            total_chunks_added += added_count
                            processed_files.append({
                                "name": file_name,
                                "chunks": len(text_chunks),
                                "added": added_count
                            })
                            st.success(f"✅ {file_name}: 提取 {len(text_chunks)} 个片段，已存入记忆库")
                        else:
                            st.warning(f"⚠️ {file_name}: 未提取到文本内容")
                
                # 显示处理结果汇总
                if total_chunks_added > 0:
                    st.markdown("---")
                    st.success(f"🎉 文档处理完成！共处理 {len(processed_files)} 个文件，新增 {total_chunks_added} 条记忆")
                    
                    # 显示详细处理结果
                    with st.expander("查看处理详情"):
                        for file_info in processed_files:
                            st.markdown(f"- **{file_info['name']}**: {file_info['chunks']} 个片段 → {file_info['added']} 条记忆")
                    
                    # 刷新页面以更新长期记忆计数
                    st.rerun()
        # ==================== 新增代码块结束 ====================
        
        st.markdown("---")
        st.markdown("### 📚 记忆库内容")
        
        # 显示长期记忆统计
        memory_count = st.session_state.agent.long_term_memory.get_memory_count()
        st.metric("长期记忆总数", memory_count)
        
        # 显示最近的记忆
        memories = st.session_state.agent.long_term_memory.get_recent_memories(10)
        
        if memories:
            st.markdown("**最近的记忆条目：**")
            for i, entry in enumerate(memories, 1):
                source_info = entry.metadata.get("source", "对话") if entry.metadata else "对话"
                with st.expander(f"记忆 {i}: {entry.content[:50]}..."):
                    st.markdown(f"**内容:** {entry.content[:200]}...")
                    st.markdown(f"**来源:** {source_info}")
                    st.markdown(f"**时间:** {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")
                    if entry.metadata:
                        st.markdown(f"**元数据:** {entry.metadata}")
        
        # 清空长期记忆按钮
        if st.button("清空长期记忆库"):
            st.session_state.agent.long_term_memory.clear()
            st.session_state.agent.long_term_memory.save_to_disk()
            st.success("长期记忆库已清空")
            st.rerun()


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