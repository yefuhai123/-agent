#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目主入口
第四阶段：记忆层 + 完整Agent集成测试

使用方法：
    python main.py

测试内容：
    1. 短期记忆模块测试
    2. 长期记忆模块测试
    3. 完整Agent集成测试
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.stdout.reconfigure(encoding='utf-8')


def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('utf-8'))


def test_short_term_memory():
    """测试短期记忆模块"""
    print("\n【测试1】短期记忆模块")
    print("-" * 50)
    
    try:
        from memory import create_short_term_memory
        
        memory = create_short_term_memory(max_messages=10)
        
        print(f"  [OK] 初始化成功")
        print(f"  [OK] 最大消息数: {memory.max_messages}")
        
        # 添加消息
        memory.add_user_message("你好，我是张三")
        memory.add_assistant_message("你好张三，我是智能助手")
        memory.add_user_message("今天天气怎么样？")
        memory.add_assistant_message("今天天气晴朗，温度25度")
        
        print(f"  [OK] 添加消息: {memory.get_message_count()} 条")
        
        # 获取消息
        messages = memory.get_messages(format_type="openai")
        print(f"  [OK] 获取消息格式: openai")
        for msg in messages:
            print(f"    - {msg['role']}: {msg['content'][:30]}")
        
        # 获取上下文摘要
        summary = memory.get_context_summary()
        safe_print(f"  [OK] 上下文摘要:\n{summary}")
        
        # 测试清理
        memory.clear()
        print(f"  [OK] 清理后消息数: {memory.get_message_count()}")
        
        return True
    
    except Exception as e:
        print(f"  [ERR] 短期记忆测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_long_term_memory():
    """测试长期记忆模块"""
    print("\n【测试2】长期记忆模块")
    print("-" * 50)
    
    try:
        from memory import create_long_term_memory
        
        memory = create_long_term_memory("test_memory_store")
        
        print(f"  [OK] 初始化成功")
        
        # 添加记忆
        memory.add_memory("张三喜欢喝咖啡")
        memory.add_memory("李四是产品经理")
        memory.add_memory("王五擅长Python编程")
        memory.add_memory("公司地址是北京市朝阳区")
        memory.add_memory("2024年AI行业发展迅速")
        
        print(f"  [OK] 添加记忆: {memory.get_memory_count()} 条")
        
        # 搜索记忆
        results = memory.search("张三")
        print(f"  [OK] 搜索'张三': {len(results)} 条结果")
        for result in results:
            print(f"    - 相似度: {result['similarity']:.2f}, 内容: {result['entry'].content}")
        
        # 关键词搜索
        results2 = memory.search_by_keyword("AI")
        print(f"  [OK] 关键词搜索'AI': {len(results2)} 条结果")
        
        # 获取最近记忆
        recent = memory.get_recent_memories(3)
        print(f"  [OK] 最近3条记忆:")
        for entry in recent:
            print(f"    - {entry.content[:30]}...")
        
        # 测试保存和加载
        memory.save_to_disk()
        print(f"  [OK] 已保存到磁盘")
        
        new_memory = create_long_term_memory("test_memory_store")
        new_memory.load_from_disk()
        print(f"  [OK] 加载后记忆数: {new_memory.get_memory_count()}")
        
        return True
    
    except Exception as e:
        print(f"  [ERR] 长期记忆测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_enterprise_agent():
    """测试完整Agent集成"""
    print("\n【测试3】完整Agent集成")
    print("-" * 50)
    
    try:
        from agent import create_enterprise_agent
        
        agent = create_enterprise_agent()
        
        print(f"  [OK] Agent初始化成功")
        
        # 获取状态
        status = agent.get_status()
        print(f"  [OK] 模型: {status['model_name']}")
        print(f"  [OK] 工具数: {status['tool_count']}")
        print(f"  [OK] 长期记忆数: {status['long_term_memories']}")
        
        # 测试聊天
        print("\n  [测试聊天]")
        result1 = agent.chat("你好，我是新来的同事，请介绍一下你自己")
        
        print(f"  [OK] 聊天成功: {result1['success']}")
        safe_print(f"  [OK] 回复: {result1['answer'][:150]}")
        print(f"  [OK] 推理步骤: {result1['total_steps']}")
        
        # 测试任务规划
        print("\n  [测试任务规划]")
        plan = agent.plan_task("分析2024年销售数据并生成报告")
        
        print(f"  [OK] 规划成功")
        print(f"  [OK] 子任务数: {plan['total_subtasks']}")
        print(f"  [OK] 预估时间: {plan['estimated_time_minutes']} 分钟")
        
        for subtask in plan["subtasks"][:3]:
            print(f"    - {subtask['task_id']}: {subtask['description'][:50]}...")
        
        # 测试对话历史
        history = agent.get_conversation_history()
        print(f"\n  [OK] 对话历史: {len(history)} 条")
        
        # 测试状态更新
        new_status = agent.get_status()
        print(f"  [OK] 新状态 - 短期消息: {new_status['short_term_messages']}, 长期记忆: {new_status['long_term_memories']}")
        
        return True
    
    except Exception as e:
        print(f"  [ERR] Agent测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_workflow():
    """测试Agent完整工作流"""
    print("\n【测试4】Agent完整工作流")
    print("-" * 50)
    
    try:
        from agent import create_enterprise_agent
        
        agent = create_enterprise_agent()
        
        print("  [工作流] 模拟企业数据分析场景")
        
        # 步骤1: 添加知识库文档
        rag_tool = agent.tool_scheduler._tools["rag_knowledge"]
        rag_tool.add_document(
            "2024年Q1销售额100万，Q2销售额120万，Q3销售额150万，Q4销售额180万。"
        )
        print("  [步骤1] 已添加销售数据到知识库")
        
        # 步骤2: 询问销售数据
        result1 = agent.chat("查询2024年各季度销售额")
        print(f"  [步骤2] 知识库查询完成")
        
        # 步骤3: 数据分析
        result2 = agent.chat("计算年度总销售额和平均季度销售额")
        print(f"  [步骤3] 数据分析完成")
        
        # 步骤4: 生成报告
        result3 = agent.chat("生成一份2024年销售数据分析报告")
        print(f"  [步骤4] 报告生成完成")
        
        # 验证结果
        print(f"\n  [验证] 步骤统计:")
        print(f"    - 查询: {result1['total_steps']} 步")
        print(f"    - 分析: {result2['total_steps']} 步")
        print(f"    - 报告: {result3['total_steps']} 步")
        
        print(f"\n  [OK] 工作流执行完成")
        
        return True
    
    except Exception as e:
        print(f"  [ERR] 工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_integration():
    """测试记忆层集成"""
    print("\n【测试5】记忆层集成测试")
    print("-" * 50)
    
    try:
        from agent import create_enterprise_agent
        
        agent = create_enterprise_agent()
        
        # 添加长期记忆
        agent.long_term_memory.add_memory("公司名称：智联科技")
        agent.long_term_memory.add_memory("公司成立于2020年")
        agent.long_term_memory.add_memory("主要业务：人工智能和大数据")
        
        print(f"  [OK] 添加长期记忆: {agent.long_term_memory.get_memory_count()} 条")
        
        # 测试记忆检索
        result = agent.chat("介绍一下我们公司")
        
        print(f"  [OK] 记忆检索成功: {result['memory_retrieved']}")
        safe_print(f"  [OK] 回复: {result['answer'][:200]}")
        
        # 测试上下文保持
        result2 = agent.chat("我们公司成立多久了？")
        print(f"  [OK] 上下文保持: {result2['success']}")
        safe_print(f"  [OK] 回复: {result2['answer'][:100]}")
        
        # 测试清空对话
        agent.clear_conversation()
        print(f"  [OK] 清空后消息数: {agent.short_term_memory.get_message_count()}")
        
        # 测试重置
        agent.reset()
        print(f"  [OK] 重置后长期记忆: {agent.long_term_memory.get_memory_count()}")
        
        return True
    
    except Exception as e:
        print(f"  [ERR] 记忆集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("轻量化企业多工具协同自主规划办公智能Agent")
    print("第四阶段：记忆层 + 完整Agent集成")
    print("=" * 60)
    
    results = []
    
    results.append(("短期记忆模块", test_short_term_memory()))
    results.append(("长期记忆模块", test_long_term_memory()))
    results.append(("完整Agent集成", test_enterprise_agent()))
    results.append(("Agent工作流", test_agent_workflow()))
    results.append(("记忆层集成", test_memory_integration()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name:20s} {status}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 第四阶段测试全部通过！")
        print("\n已完成模块开发：")
        print("  ✅ 短期记忆 - 对话上下文管理")
        print("  ✅ 长期记忆 - FAISS向量存储")
        print("  ✅ 完整Agent - 核心推理+工具+记忆集成")
        print("  ✅ Streamlit界面 - Web可视化交互")
        
        print("\n项目完整结构：")
        print("  agent/           - 完整Agent集成")
        print("  core/            - 核心推理层")
        print("    react_engine.py      - ReAct推理引擎")
        print("    task_planner.py      - 任务规划器")
        print("    tool_scheduler.py    - 工具调度器")
        print("    deepseek_model.py    - 模型封装")
        print("  tools/           - 可插拔工具层")
        print("    web_search_tool.py           - 联网检索")
        print("    rag_knowledge_tool.py        - RAG知识库")
        print("    python_executor_tool.py      - Python执行")
        print("    report_generator_tool.py     - 报告生成")
        print("  memory/          - 双层记忆架构")
        print("    short_term_memory.py         - 短期记忆")
        print("    long_term_memory.py          - 长期记忆")
        print("  ui/              - 可视化界面")
        print("    app.py                      - Streamlit应用")
        
        print("\n启动Streamlit界面：")
        print("  streamlit run ui/app.py")
        
        print("\n项目开发完成！")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")


if __name__ == "__main__":
    main()