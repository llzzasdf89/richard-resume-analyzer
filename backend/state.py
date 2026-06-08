# state.py
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ResumeAnalysisState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # 输入
    resume_text: str           # 解析后的简历文本
    jd_text: str               # JD 文本

    # JD 分析 Agent 输出
    jd_requirements: str       # JD 核心要求
    jd_must_skills: list[str]  # 必备技能
    jd_nice_skills: list[str]  # 加分技能

    # RAG 检索结果
    rag_context: str           # 检索到的相似岗位参考

    # 匹配分析 Agent 输出
    match_score: int           # 匹配度 0-100
    matched_skills: list[str]  # 匹配的技能
    missing_skills: list[str]  # 缺失的技能

    # Supervisor 输出
    agents_to_run: list[str]   # supervisor 决定启动哪些子 Agent

    # 子 Agent 并行输出（operator.add 确保并行写入时追加而不是覆盖）
    sub_suggestions: Annotated[list[str], operator.add]

    # 聚合后的优化建议
    suggestions: str           # 汇总后的针对性优化建议

    # 简历重写 Agent 输出
    rewritten_resume: str      # 重写后的简历段落

    # 错误处理
    error: str