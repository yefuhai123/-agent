#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 可视化界面 —— 企业级智能 Agent 交互控制台
为企业级智能 Agent 提供现代化、友好的 Web 交互体验
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from typing import Dict, Any, List
import tempfile

from agent import create_enterprise_agent
from memory import create_short_term_memory, create_long_term_memory


# ========================== 自定义 CSS 样式 ==========================
CUSTOM_CSS = """
<style>
/* ===== 全局字体与滚动条 ===== */
html, body, [class*="css"] {
    font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}

/* ===== 侧边栏品牌区 ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* ===== 卡片通用样式 ===== */
.card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
    border: 1px solid #f1f5f9;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 1rem;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}
.card-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.card-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
}
.card-delta {
    font-size: 0.75rem;
    color: #10b981;
    font-weight: 500;
    margin-top: 0.25rem;
}

/* ===== 指标卡片彩色条 ===== */
.metric-card {
    border-left: 4px solid #3b82f6;
}
.metric-card.success {
    border-left-color: #10b981;
}
.metric-card.warning {
    border-left-color: #f59e0b;
}
.metric-card.danger {
    border-left-color: #ef4444;
}

/* ===== 脉冲动画（运行中指示器） ===== */
@keyframes pulse-ring {
    0% { transform: scale(0.8); opacity: 1; }
    100% { transform: scale(2.4); opacity: 0; }
}
.pulse-dot {
    position: relative;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
}
.pulse-dot::before {
    content: '';
    position: absolute;
    left: 0; top: 0;
    width: 100%; height: 100%;
    border-radius: 50%;
    background: #10b981;
    animation: pulse-ring 1.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}

/* ===== 聊天消息优化 ===== */
[data-testid="stChatMessage"] {
    padding: 0.75rem 0;
}
[data-testid="stChatMessageContent"] {
    border-radius: 12px;
    padding: 0.75rem 1rem;
}
[data-testid="stChatMessage"][data-testid$="user"] [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
}
[data-testid="stChatMessage"][data-testid$="assistant"] [data-testid="stChatMessageContent"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}

/* ===== 折叠面板优化 ===== */
.stExpander {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
    background: #ffffff;
}

/* ===== 按钮优化 ===== */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

/* ===== 标签页优化 ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.5rem 1rem;
    font-weight: 500;
}

/* ===== 输入框优化 ===== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

/* ===== 文件上传区优化 ===== */
[data-testid="stFileUploader"] > section {
    border: 2px dashed #cbd5e1;
    border-radius: 16px;
    background: #f8fafc;
    transition: all 0.2s ease;
}
[data-testid="stFileUploader"] > section:hover {
    border-color: #3b82f6;
    background: #eff6ff;
}

/* ===== 步骤/时间线样式 ===== */
.step-item {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.step-marker {
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: #e0e7ff;
    color: #4338ca;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.875rem;
    flex-shrink: 0;
}
.step-marker.done {
    background: #d1fae5;
    color: #059669;
}
.step-content {
    flex: 1;
    padding-top: 0.125rem;
}
.step-title {
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.25rem;
}
.step-desc {
    font-size: 0.875rem;
    color: #64748b;
}
.step-line {
    position: absolute;
    left: 1rem;
    top: 2rem;
    bottom: -1.5rem;
    width: 2px;
    background: #e2e8f0;
}

/* ===== 记忆条目卡片 ===== */
.memory-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    transition: all 0.2s ease;
}
.memory-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05);
}
.memory-source {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    color: #3b82f6;
    background: #eff6ff;
    padding: 0.125rem 0.5rem;
    border-radius: 9999px;
    margin-bottom: 0.5rem;
}
.memory-time {
    font-size: 0.75rem;
    color: #94a3b8;
}

/* ===== 工具卡片网格 ===== */
.tool-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.25rem;
    height: 100%;
    transition: all 0.2s ease;
}
.tool-card:hover {
    border-color: #3b82f6;
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}
.tool-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    margin-bottom: 0.75rem;
}
.tool-name {
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
}
.tool-desc {
    font-size: 0.875rem;
    color: #64748b;
    line-height: 1.5;
}

/* ===== 页面切换淡入 ===== */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in {
    animation: fadeIn 0.4s ease-out;
}

/* ===== 顶部标题区 ===== */
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 20px;
    padding: 2rem;
    color: white;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(59,130,246,0.3) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    position: relative;
}
.hero-subtitle {
    font-size: 1rem;
    color: #94a3b8;
    position: relative;
}
</style>
"""


# ==================== 文档处理函数 ====================
def process_uploaded_document(file_content: bytes, file_name: str, file_type: str) -> List[str]:
    """处理上传的文档，提取文本并进行分割"""
    text_chunks = []
    try:
        if file_type in ("txt", "md"):
            text = file_content.decode('utf-8', errors='ignore')
            text_chunks = split_text(text, chunk_size=500, overlap=50)
        elif file_type == "pdf":
            try:
                import PyPDF2
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
                st.warning("PDF 处理需要安装 PyPDF2 库: pip install PyPDF2")
                return []
        elif file_type == "docx":
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
                st.warning("Word 文档处理需要安装 python-docx 库: pip install python-docx")
                return []
        return text_chunks
    except Exception as e:
        st.error(f"文档处理失败: {str(e)}")
        return []


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """文本分割函数"""
    if not text:
        return []
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
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
    """将文档片段添加到长期记忆库"""
    added_count = 0
    for i, chunk in enumerate(text_chunks):
        if chunk:
            metadata = {
                "source": file_name,
                "chunk_index": i,
                "total_chunks": len(text_chunks),
                "type": "document"
            }
            agent.long_term_memory.add_memory(content=chunk, metadata=metadata)
            added_count += 1
    agent.long_term_memory.save_to_disk()
    return added_count


# ==================== 会话状态初始化 ====================
def init_session_state():
    """初始化 Streamlit 会话状态"""
    if "agent" not in st.session_state:
        st.session_state.agent = create_enterprise_agent()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    if "current_task" not in st.session_state:
        st.session_state.current_task = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "仪表盘"
    if "task_plans" not in st.session_state:
        st.session_state.task_plans = []


# ==================== 侧边栏导航 ====================
def render_sidebar():
    """渲染侧边栏导航"""
    with st.sidebar:
        # 品牌区
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🤖</div>
            <div style="font-size:1.25rem; font-weight:700; color:#f8fafc;">企业智能 Agent</div>
            <div style="font-size:0.75rem; color:#94a3b8; margin-top:0.25rem;">Enterprise AI Assistant</div>
        </div>
        """, unsafe_allow_html=True)

        # 导航菜单
        pages = ["仪表盘", "智能对话", "任务中心", "记忆仓库", "工具箱"]
        icons = ["📊", "💬", "📋", "🧠", "🛠️"]

        for page, icon in zip(pages, icons):
            active = st.session_state.current_page == page
            btn_type = "primary" if active else "secondary"
            if st.button(f"{icon} {page}", use_container_width=True, type=btn_type, key=f"nav_{page}"):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("<hr style='border-color:#334155; margin:2rem 0;'>", unsafe_allow_html=True)

        # 状态指示器
        status = st.session_state.agent.get_status()
        st.markdown("""
        <div style="color:#94a3b8; font-size:0.75rem; font-weight:600; margin-bottom:0.75rem;">系统状态</div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 5])
        with col1:
            st.markdown('<div class="pulse-dot"></div>', unsafe_allow_html=True)
        with col2:
            st.markdown("<span style='color:#10b981; font-size:0.875rem; font-weight:500;'>运行中</span>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:1rem; color:#64748b; font-size:0.75rem;">
            <div style="margin-bottom:0.5rem;">模型: <span style="color:#f8fafc;">{status['model_name']}</span></div>
            <div style="margin-bottom:0.5rem;">工具: <span style="color:#f8fafc;">{status['tool_count']}</span></div>
            <div>记忆: <span style="color:#f8fafc;">{status['long_term_memories']}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='flex:1;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="position:fixed; bottom:1.5rem; color:#475569; font-size:0.75rem;">
            v2.0 · Powered by ReAct
        </div>
        """, unsafe_allow_html=True)


# ==================== 仪表盘页面 ====================
def render_dashboard():
    """渲染仪表盘首页"""
    status = st.session_state.agent.get_status()

    # Hero 区域
    st.markdown("""
    <div class="hero">
        <div class="hero-title">👋 欢迎回到企业智能 Agent</div>
        <div class="hero-subtitle">基于 ReAct 框架的多工具协同自主规划办公助手，随时待命为您提供服务。</div>
    </div>
    """, unsafe_allow_html=True)

    # 指标卡片
    cols = st.columns(4)
    metrics = [
        ("🧠 底层模型", status["model_name"], "success"),
        ("🛠️ 可用工具", str(status["tool_count"]), "warning"),
        ("💬 对话消息", str(status["short_term_messages"]), ""),
        ("🧠 长期记忆", str(status["long_term_memories"]), "danger"),
    ]
    for col, (title, value, cls) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="card metric-card {cls}">
                <div class="card-title">{title}</div>
                <div class="card-value">{value}</div>
                <div class="card-delta">实时数据</div>
            </div>
            """, unsafe_allow_html=True)

    # 快捷操作区
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("⚡ 快捷操作")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💬 开始对话", use_container_width=True):
            st.session_state.current_page = "智能对话"
            st.rerun()
    with c2:
        if st.button("📋 规划任务", use_container_width=True):
            st.session_state.current_page = "任务中心"
            st.rerun()
    with c3:
        if st.button("📄 上传文档", use_container_width=True):
            st.session_state.current_page = "记忆仓库"
            st.rerun()
    with c4:
        if st.button("🧹 清空对话", use_container_width=True):
            st.session_state.agent.clear_conversation()
            st.session_state.chat_history = []
            st.success("对话历史已清空")

    # 最近动态
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("📈 最近动态")
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown("""
        <div class="card">
            <div style="font-weight:600; margin-bottom:0.75rem;">💬 最近对话</div>
        """, unsafe_allow_html=True)
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history[-5:]:
                role = "🧑‍💻 用户" if msg["role"] == "user" else "🤖 助手"
                preview = msg["content"][:40] + "..." if len(msg["content"]) > 40 else msg["content"]
                st.markdown(f"<div style='font-size:0.875rem; color:#334155; margin-bottom:0.5rem;'>{role}: {preview}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:0.875rem; color:#94a3b8;'>暂无对话记录</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="card">
            <div style="font-weight:600; margin-bottom:0.75rem;">📋 最近任务</div>
        """, unsafe_allow_html=True)
        if st.session_state.current_task:
            task = st.session_state.current_task
            st.markdown(f"<div style='font-size:0.875rem; color:#334155; margin-bottom:0.5rem;'>任务包含 {task.get('total_subtasks', 0)} 个子任务</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.875rem; color:#334155;'>预估耗时: {task.get('estimated_time_minutes', '-')} 分钟</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:0.875rem; color:#94a3b8;'>暂无进行中的任务</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ==================== 智能对话页面 ====================
def render_chat():
    """渲染沉浸式聊天页面"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)

    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.subheader("💬 智能对话")
        st.caption("与 Agent 进行多轮交互，支持工具调用和推理过程展示")

        # 聊天历史
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user", avatar="🧑‍💻").write(message["content"])
            elif message["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(message["content"])
                    if "thoughts" in message:
                        with st.expander("🧠 查看推理过程"):
                            for thought in message["thoughts"]:
                                step = thought.get("step", "")
                                content = thought.get("content", "")
                                tool_name = thought.get("tool_name")
                                tool_args = thought.get("tool_args", {})
                                st.markdown(f"**步骤 {step}**")
                                st.markdown(f"{content}")
                                if tool_name:
                                    st.markdown(f"<span style='color:#3b82f6; font-size:0.875rem;'>🔧 调用工具: `{tool_name}`</span>", unsafe_allow_html=True)
                                    st.code(f"{tool_args}", language="json")
                                st.markdown("---")
                    if "steps" in message:
                        st.caption(f"⏱️ 推理步骤: {message['steps']} 步")

        # 用户输入
        user_input = st.chat_input("请输入您的问题，Agent 将自主规划并调用工具...")
        if user_input and not st.session_state.is_loading:
            st.session_state.is_loading = True
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("Agent 正在思考与行动..."):
                result = st.session_state.agent.chat(user_input)
            assistant_message = {
                "role": "assistant",
                "content": result["answer"],
                "steps": result["total_steps"]
            }
            if result.get("thought_history"):
                assistant_message["thoughts"] = result["thought_history"]
            st.session_state.chat_history.append(assistant_message)
            st.session_state.is_loading = False
            st.rerun()

    with col_side:
        st.markdown("""
        <div class="card" style="margin-top:2.5rem;">
            <div style="font-weight:600; margin-bottom:0.75rem;">📊 会话信息</div>
            <div style="font-size:0.875rem; color:#64748b; margin-bottom:0.5rem;">消息数: <strong style="color:#0f172a;">{}</strong></div>
            <div style="font-size:0.875rem; color:#64748b; margin-bottom:0.5rem;">状态: <strong style="color:#10b981;">就绪</strong></div>
        </div>
        """.format(len(st.session_state.chat_history)), unsafe_allow_html=True)

        if st.button("🧹 清空对话", use_container_width=True):
            st.session_state.agent.clear_conversation()
            st.session_state.chat_history = []
            st.success("对话已清空")
            st.rerun()

        st.markdown("""
        <div class="card">
            <div style="font-weight:600; margin-bottom:0.75rem;">💡 提示</div>
            <div style="font-size:0.875rem; color:#64748b; line-height:1.6;">
                Agent 支持调用多种工具完成任务。<br><br>
                例如：<br>
                • "搜索最新的行业报告"<br>
                • "分析这份销售数据"<br>
                • "生成项目总结文档"
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 任务中心页面 ====================
def render_task_center():
    """渲染任务规划与执行页面"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.subheader("📋 任务中心")
    st.caption("将复杂任务自主分解为子任务，并逐步执行完成")

    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-weight:600; margin-bottom:0.75rem;'>📝 任务输入</div>", unsafe_allow_html=True)
        task_input = st.text_area("描述您需要完成的任务:", height=120, placeholder="例如：帮我收集最近一周关于人工智能的行业新闻，整理成一份摘要报告...")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 智能规划", use_container_width=True, type="primary"):
                if task_input:
                    with st.spinner("Agent 正在分析并拆解任务..."):
                        plan = st.session_state.agent.plan_task(task_input)
                    st.session_state.current_task = plan
                    st.session_state.task_plans.append(plan)
                    st.success(f"任务已分解为 {plan['total_subtasks']} 个子任务")
                    st.rerun()
                else:
                    st.warning("请先输入任务描述")
        with c2:
            if st.button("▶️ 执行规划", use_container_width=True):
                if st.session_state.current_task:
                    with st.spinner("正在按规划执行任务..."):
                        execution_result = st.session_state.agent.execute_plan(st.session_state.current_task)
                    if execution_result["success"]:
                        st.success(f"任务执行完成！{execution_result['completed_tasks']}/{execution_result['total_tasks']}")
                    else:
                        st.warning(f"部分任务失败，完成 {execution_result['completed_tasks']}/{execution_result['total_tasks']}")
                else:
                    st.warning("请先进行任务规划")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_preview:
        if st.session_state.current_task:
            plan = st.session_state.current_task
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight:600; margin-bottom:0.75rem;'>📋 当前规划 (共 {plan.get('total_subtasks', 0)} 个子任务)</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.875rem; color:#64748b; margin-bottom:1rem;'>⏱️ 预估耗时: <strong>{plan.get('estimated_time_minutes', '-')} 分钟</strong></div>", unsafe_allow_html=True)

            for i, subtask in enumerate(plan.get("subtasks", []), 1):
                status_icon = "⬜"
                status_color = "#64748b"
                st.markdown(f"""
                <div style="display:flex; gap:0.75rem; margin-bottom:1rem; align-items:flex-start;">
                    <div style="min-width:1.5rem; height:1.5rem; border-radius:50%; background:#e2e8f0; color:#64748b; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700;">{i}</div>
                    <div style="flex:1;">
                        <div style="font-weight:600; color:#1e293b; font-size:0.9rem;">{subtask.get('description', '')}</div>
                        <div style="font-size:0.8rem; color:#64748b; margin-top:0.25rem;">
                            优先级: <span style="color:#3b82f6;">{subtask.get('priority', 'medium')}</span>
                            {f"&nbsp;|&nbsp;依赖: {', '.join(subtask['dependencies'])}" if subtask.get('dependencies') else ""}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="text-align:center; padding:3rem 1rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">📋</div>
                <div style="font-weight:600; color:#334155; margin-bottom:0.5rem;">暂无任务规划</div>
                <div style="font-size:0.875rem; color:#94a3b8;">在左侧输入任务描述并点击"智能规划"</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 记忆仓库页面 ====================
def render_memory_center():
    """渲染记忆管理页面"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.subheader("🧠 记忆仓库")
    st.caption("管理 Agent 的短期对话记忆与长期知识库，支持文档上传与向量化存储")

    tab_upload, tab_short, tab_long = st.tabs(["📄 文档上传", "💬 短期记忆", "📚 长期记忆"])

    with tab_upload:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-weight:600; margin-bottom:0.5rem;'>📎 上传文档到长期记忆库</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.875rem; color:#64748b; margin-bottom:1rem;'>支持 PDF、Word、TXT、Markdown 格式，系统将自动提取文本、分块、向量化并存储。</div>", unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "选择文档文件（支持批量上传）",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            help="支持批量上传多个文件"
        )

        if uploaded_files:
            st.markdown(f"<div style='font-size:0.875rem; color:#334155; margin-bottom:0.75rem;'>已选择 <strong>{len(uploaded_files)}</strong> 个文件</div>", unsafe_allow_html=True)
            for f in uploaded_files:
                st.markdown(f"<div style='font-size:0.8rem; color:#64748b;'>• {f.name} ({f.size // 1024} KB)</div>", unsafe_allow_html=True)

            if st.button("🚀 处理并存入记忆库", type="primary"):
                total_chunks_added = 0
                processed_files = []
                progress_bar = st.progress(0)
                for idx, uploaded_file in enumerate(uploaded_files):
                    file_name = uploaded_file.name
                    file_type = file_name.split('.')[-1].lower()
                    file_content = uploaded_file.read()
                    st.info(f"正在处理: {file_name}...")
                    text_chunks = process_uploaded_document(file_content, file_name, file_type)
                    if text_chunks:
                        added_count = add_document_to_memory(st.session_state.agent, text_chunks, file_name)
                        total_chunks_added += added_count
                        processed_files.append({"name": file_name, "chunks": len(text_chunks), "added": added_count})
                        st.success(f"✅ {file_name}: {len(text_chunks)} 个片段 → {added_count} 条记忆")
                    else:
                        st.warning(f"⚠️ {file_name}: 未提取到文本")
                    progress_bar.progress((idx + 1) / len(uploaded_files))

                if total_chunks_added > 0:
                    st.balloons()
                    st.success(f"🎉 全部完成！共处理 {len(processed_files)} 个文件，新增 {total_chunks_added} 条记忆")
                progress_bar.empty()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_short:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-weight:600; margin-bottom:0.75rem;'>💬 近期对话记录</div>", unsafe_allow_html=True)
        messages = st.session_state.agent.short_term_memory.get_messages(format_type="dict")
        if messages:
            for msg in messages[-10:]:
                role_label = "🧑‍💻 用户" if msg["role"] == "user" else "🤖 助手"
                role_color = "#3b82f6" if msg["role"] == "user" else "#10b981"
                content = msg["content"][:120] + "..." if len(msg["content"]) > 120 else msg["content"]
                st.markdown(f"""
                <div style="padding:0.75rem; background:#f8fafc; border-radius:10px; margin-bottom:0.5rem; border-left:3px solid {role_color};">
                    <div style="font-size:0.75rem; font-weight:600; color:{role_color}; margin-bottom:0.25rem;">{role_label}</div>
                    <div style="font-size:0.875rem; color:#334155;">{content}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#94a3b8; font-size:0.875rem;'>暂无对话记录</div>", unsafe_allow_html=True)

        if st.button("🗑️ 清空短期记忆", use_container_width=True):
            st.session_state.agent.clear_conversation()
            st.session_state.chat_history = []
            st.success("短期记忆已清空")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_long:
        memory_count = st.session_state.agent.long_term_memory.get_memory_count()
        col_info, col_action = st.columns([3, 1])
        with col_info:
            st.markdown(f"<div class='card'><div style='font-weight:600; margin-bottom:0.5rem;'>📚 记忆库统计</div><div style='font-size:0.875rem; color:#64748b;'>当前共存储 <strong style='color:#0f172a; font-size:1.25rem;'>{memory_count}</strong> 条长期记忆</div></div>", unsafe_allow_html=True)
        with col_action:
            if st.button("🗑️ 清空记忆库", use_container_width=True):
                st.session_state.agent.long_term_memory.clear()
                st.session_state.agent.long_term_memory.save_to_disk()
                st.success("长期记忆库已清空")
                st.rerun()

        memories = st.session_state.agent.long_term_memory.get_recent_memories(10)
        if memories:
            st.markdown("<div style='font-weight:600; margin:1rem 0 0.75rem;'>📋 最近存入的记忆</div>", unsafe_allow_html=True)
            for entry in memories:
                source_info = entry.metadata.get("source", "对话") if entry.metadata else "对话"
                content_preview = entry.content[:120] + "..." if len(entry.content) > 120 else entry.content
                time_str = entry.timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(entry, 'timestamp') and entry.timestamp else "-"
                st.markdown(f"""
                <div class="memory-card">
                    <span class="memory-source">{source_info}</span>
                    <div style="font-size:0.875rem; color:#334155; margin-bottom:0.5rem; line-height:1.5;">{content_preview}</div>
                    <div class="memory-time">🕒 {time_str}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="text-align:center; padding:3rem 1rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
                <div style="font-weight:600; color:#334155; margin-bottom:0.5rem;">记忆库为空</div>
                <div style="font-size:0.875rem; color:#94a3b8;">在"文档上传"标签页添加知识文档</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 工具箱页面 ====================
def render_toolbox():
    """渲染工具管理页面"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.subheader("🛠️ 工具箱")
    st.caption("查看 Agent 集成的所有工具及其参数定义")

    tools = st.session_state.agent.tool_scheduler.get_all_tools()
    if not tools:
        st.info("暂无已注册的工具")
        return

    cols = st.columns(2)
    for i, tool in enumerate(tools):
        with cols[i % 2]:
            params_html = ""
            for param_name, param_info in tool.parameters.items():
                desc = param_info.get('description', '')
                ptype = param_info.get('type', 'string')
                required = "必填" if param_info.get('required', False) else "可选"
                params_html += f"<div style='margin-bottom:0.5rem; padding:0.5rem; background:#f8fafc; border-radius:8px;'><div style='font-weight:600; font-size:0.8rem; color:#0f172a;'>{param_name} <span style='color:#64748b; font-weight:400;'>({ptype})</span></div><div style='font-size:0.8rem; color:#64748b;'>{desc}</div><div style='font-size:0.75rem; color:#3b82f6; margin-top:0.25rem;'>{required}</div></div>"

            st.markdown(f"""
            <div class="tool-card">
                <div class="tool-icon">🔧</div>
                <div class="tool-name">{tool.name}</div>
                <div class="tool-desc">{tool.description}</div>
                <div style="margin-top:1rem;">
                    <div style="font-size:0.75rem; font-weight:600; color:#64748b; margin-bottom:0.5rem;">参数定义</div>
                    {params_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 主函数 ====================
def main():
    """主函数"""
    st.set_page_config(
        page_title="企业智能 Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 注入自定义 CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    init_session_state()
    render_sidebar()

    # 根据当前页面渲染内容
    page = st.session_state.current_page
    if page == "仪表盘":
        render_dashboard()
    elif page == "智能对话":
        render_chat()
    elif page == "任务中心":
        render_task_center()
    elif page == "记忆仓库":
        render_memory_center()
    elif page == "工具箱":
        render_toolbox()


if __name__ == "__main__":
    main()
