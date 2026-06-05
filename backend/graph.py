# graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langfuse.decorators import observe
from state import ResumeAnalysisState
from rag import search_similar_jds
from tools import search_similar_jobs, get_skill_market_demand
from dotenv import load_dotenv
import os
import json

load_dotenv()

model = ChatAnthropic(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

# 绑定工具的模型，专用于 match_analysis ReAct Agent
_tools = [search_similar_jobs, get_skill_market_demand]
_tool_map = {t.name: t for t in _tools}
model_with_tools = model.bind_tools(_tools)

# ── 节点定义 ────────────────────────────────────────────────

@observe(name="jd_analysis")
def jd_analysis_node(state: ResumeAnalysisState) -> dict:
    """JD 分析 Agent：提取核心要求、必备技能、加分项"""
    response = model.invoke([
        SystemMessage("""你是一个 JD 分析专家。
分析给定的职位描述，提取以下信息，以 JSON 格式返回：
{
  "requirements": "岗位核心要求描述",
  "must_skills": ["必备技能1", "必备技能2"],
  "nice_skills": ["加分技能1", "加分技能2"]
}
只返回 JSON，不要其他内容。"""),
        HumanMessage(f"请分析这个 JD：\n\n{state['jd_text']}")
    ])

    try:
        data = json.loads(response.content)
        return {
            "jd_requirements": data.get("requirements", ""),
            "jd_must_skills": data.get("must_skills", []),
            "jd_nice_skills": data.get("nice_skills", []),
        }
    except Exception:
        return {
            "jd_requirements": response.content,
            "jd_must_skills": [],
            "jd_nice_skills": [],
        }

@observe(name="rag_retrieval")
def rag_retrieval_node(state: ResumeAnalysisState) -> dict:
    """RAG 检索节点：检索相似岗位历史数据"""
    query = f"{state['jd_requirements']} {' '.join(state['jd_must_skills'])}"
    print(f"RAG 查询词：{query}")  # 加这行
    context = search_similar_jds(query)
    print(f"RAG 检索结果：\n{context[:300]}")
    return {"rag_context": context}

@observe(name="match_analysis")
def match_analysis_node(state: ResumeAnalysisState) -> dict:
    """匹配分析 Agent：ReAct 循环，自主决定是否调用工具查询市场信息，再给出评分"""

    messages = [
        SystemMessage("""你是一个简历匹配分析专家。

你有两个工具可以调用：
- search_similar_jobs：根据技能/岗位关键词检索知识库中相似的岗位JD，用于参考市场要求
- get_skill_market_demand：查询某个技能的市场需求程度，用于判断缺失技能的严重性

分析步骤：
1. 先阅读简历和JD，初步判断哪些缺失技能是关键缺口
2. 对你不确定重要性的技能，调用 get_skill_market_demand 查询
3. 如果需要更多市场参考，调用 search_similar_jobs 检索相似岗位
4. 综合所有信息后，以 JSON 格式输出最终结果：
{
  "match_score": 75,
  "matched_skills": ["技能1", "技能2"],
  "missing_skills": ["缺失技能1", "缺失技能2"]
}

评分规则：
- 90-100：技能高度匹配，几乎满足所有要求
- 70-89：核心技能匹配，少量缺口
- 40-69：部分匹配，有明显缺口
- 10-39：相关性低，主要技能不符
- 1-9：几乎无相关技能，但候选人有基础工程能力
- 只有候选人完全没有任何技术背景时才给 0 分

完成工具调用后，只返回 JSON，不要其他内容。"""),
        HumanMessage(f"""简历内容：
{state['resume_text']}

JD 核心要求：
{state['jd_requirements']}

必备技能：
{', '.join(state['jd_must_skills'])}

加分技能：
{', '.join(state['jd_nice_skills'])}

RAG 参考（已检索）：
{state['rag_context']}

请开始分析。"""),
    ]

    # ── ReAct 循环 ────────────────────────────────────────────
    MAX_ITERATIONS = 5  # 防止无限循环
    for i in range(MAX_ITERATIONS):
        response = model_with_tools.invoke(messages)
        messages.append(response)

        print(f"[DEBUG] match_analysis 第{i+1}轮，tool_calls: {[tc['name'] for tc in response.tool_calls]}")

        # 没有工具调用 → 模型认为推理完成，退出循环
        if not response.tool_calls:
            break

        # 执行所有工具调用，把结果还给模型
        for tool_call in response.tool_calls:
            tool_fn = _tool_map.get(tool_call["name"])
            if tool_fn is None:
                result = f"未知工具：{tool_call['name']}"
            else:
                result = tool_fn.invoke(tool_call["args"])
                print(f"[DEBUG] 工具 {tool_call['name']} 返回: {str(result)[:200]}")

            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            ))
        # 继续循环，让模型看到工具结果后决定下一步

    # ── 解析最终输出 ──────────────────────────────────────────
    final_content = response.content if isinstance(response.content, str) else ""
    print(f"[DEBUG] match_analysis 最终输出: {final_content[:500]}")

    try:
        # 兼容模型在 JSON 前后附带说明文字的情况
        start = final_content.find("{")
        end = final_content.rfind("}") + 1
        data = json.loads(final_content[start:end])
        return {
            "match_score": data.get("match_score", 0),
            "matched_skills": data.get("matched_skills", []),
            "missing_skills": data.get("missing_skills", []),
        }
    except Exception:
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
        }

@observe(name="suggestions")
def suggestions_node(state: ResumeAnalysisState) -> dict:
    """优化建议 Agent：生成针对性建议"""
    response = model.invoke([
        SystemMessage("你是一个简历优化专家，根据匹配分析结果给出具体可执行的优化建议。"),
        HumanMessage(f"""匹配度：{state['match_score']}分

已匹配技能：{', '.join(state['matched_skills'])}

缺失技能：{', '.join(state['missing_skills'])}

参考相似岗位建议：
{state['rag_context']}

请给出 3-5 条具体的简历优化建议，每条建议要有可执行的行动项。""")
    ])
    return {"suggestions": response.content}

@observe(name="rewrite")
def rewrite_node(state: ResumeAnalysisState) -> dict:
    """简历重写 Agent：针对 JD 重写简历关键段落"""
    response = model.invoke([
        SystemMessage("你是一个简历写作专家，擅长针对特定 JD 优化简历表达。"),
        HumanMessage(f"""原始简历：
{state['resume_text']}

目标 JD 要求：
{state['jd_requirements']}

必备技能：{', '.join(state['jd_must_skills'])}

缺失技能（需要在简历中补强或诚实说明）：{', '.join(state['missing_skills'])}

请重写简历中的「工作经历」和「技能」部分，使其更符合目标 JD 的要求。
注意：只重写表达方式，不要捏造不存在的经历。""")
    ])
    return {"rewritten_resume": response.content}

# ── 条件路由 ──────────────────────────────────────────────

def route_after_match(state: ResumeAnalysisState) -> str:
    """根据匹配分数决定下一个节点：
    - 高匹配（>=75）：直接重写简历，跳过通用建议
    - 低匹配（<75）：先给出针对性优化建议，再重写
    """
    score = state.get("match_score", 0)
    print(f"[DEBUG] 匹配分数: {score}，路由至: {'rewrite' if score >= 75 else 'suggestions'}")
    if score >= 75:
        return "rewrite"
    return "suggestions"


# ── 构建图 ────────────────────────────────────────────────

graph = StateGraph(ResumeAnalysisState)

graph.add_node("jd_analysis", jd_analysis_node)
graph.add_node("rag_retrieval", rag_retrieval_node)
graph.add_node("match_analysis", match_analysis_node)
graph.add_node("suggestions", suggestions_node)
graph.add_node("rewrite", rewrite_node)

graph.set_entry_point("jd_analysis")
graph.add_edge("jd_analysis", "rag_retrieval")
graph.add_edge("rag_retrieval", "match_analysis")

# 条件路由：高匹配直接重写，低匹配先给建议
graph.add_conditional_edges(
    "match_analysis",
    route_after_match,
    {
        "rewrite": "rewrite",
        "suggestions": "suggestions",
    }
)

graph.add_edge("suggestions", "rewrite")
graph.add_edge("rewrite", END)

app = graph.compile()