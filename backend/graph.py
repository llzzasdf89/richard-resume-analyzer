# graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from state import ResumeAnalysisState
from rag import search_similar_jds
from dotenv import load_dotenv
import os
import json

load_dotenv()

model = ChatAnthropic(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

# ── 节点定义 ────────────────────────────────────────────────

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

def rag_retrieval_node(state: ResumeAnalysisState) -> dict:
    """RAG 检索节点：检索相似岗位历史数据"""
    query = f"{state['jd_requirements']} {' '.join(state['jd_must_skills'])}"
    context = search_similar_jds(query)
    return {"rag_context": context}

def match_analysis_node(state: ResumeAnalysisState) -> dict:
    """匹配分析 Agent：评分 + 匹配点 + 技能缺口"""
    response = model.invoke([
        SystemMessage("""你是一个简历匹配分析专家。
根据简历和 JD 要求，分析匹配情况，以 JSON 格式返回：
{
  "match_score": 75,
  "matched_skills": ["技能1", "技能2"],
  "missing_skills": ["缺失技能1", "缺失技能2"]
}
只返回 JSON，不要其他内容。"""),
        HumanMessage(f"""简历内容：
{state['resume_text']}

JD 核心要求：
{state['jd_requirements']}

必备技能：
{', '.join(state['jd_must_skills'])}

加分技能：
{', '.join(state['jd_nice_skills'])}

参考相似岗位：
{state['rag_context']}""")
    ])

    try:
        data = json.loads(response.content)
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
graph.add_edge("match_analysis", "suggestions")
graph.add_edge("suggestions", "rewrite")
graph.add_edge("rewrite", END)

app = graph.compile()