# graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.types import Send
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
2. 对不确定重要性的技能调用 get_skill_market_demand 查询，最多查 3 次，优先查最关键的
3. 如果需要更多市场参考，调用 search_similar_jobs 检索相似岗位
4. 工具调用完毕后，输出一个合法的 JSON 对象，包含以下三个字段：
   - match_score：0-100 的整数，表示匹配度
   - matched_skills：字符串数组，列出简历中已具备的匹配技能（填真实技能名，不要用占位符）
   - missing_skills：字符串数组，列出简历中缺失的关键技能（填真实技能名，不要用占位符）

评分规则：
- 90-100：技能高度匹配，几乎满足所有要求
- 70-89：核心技能匹配，少量缺口
- 40-69：部分匹配，有明显缺口
- 10-39：相关性低，主要技能不符
- 1-9：几乎无相关技能，但候选人有基础工程能力
- 只有候选人完全没有任何技术背景时才给 0 分

最终只输出 JSON 对象本身，不要包含任何解释文字。"""),
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
    if isinstance(response.content, str):
        final_content = response.content
    elif isinstance(response.content, list):
        # model_with_tools returns content as a list of blocks; extract text blocks
        final_content = "".join(
            block["text"] for block in response.content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        final_content = ""
    print(f"[DEBUG] match_analysis 最终输出: {final_content[:500]}")

    try:
        # 兼容模型在 JSON 前后附带说明文字的情况
        start = final_content.find("{")
        end = final_content.rfind("}") + 1
        data = json.loads(final_content[start:end])

        matched = data.get("matched_skills", [])
        missing = data.get("missing_skills", [])

        # 兜底：如果模型输出了示例占位符而非真实结果，视为解析失败
        placeholder_keywords = {"技能1", "技能2", "缺失技能1", "缺失技能2"}
        if set(matched) & placeholder_keywords or set(missing) & placeholder_keywords:
            print("[DEBUG] 检测到占位符输出，解析失败回退")
            raise ValueError("模型输出了模板占位符")

        return {
            "match_score": data.get("match_score", 0),
            "matched_skills": matched,
            "missing_skills": missing,
        }
    except Exception as e:
        print(f"[DEBUG] match_analysis 解析失败: {e}")
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
        }

@observe(name="supervisor")
def supervisor_node(state: ResumeAnalysisState) -> dict:
    """Supervisor Agent：分析当前匹配情况，决定启动哪些子 Agent"""
    response = model.invoke([
        SystemMessage("""你是一个任务分配专家，负责根据简历匹配情况决定启动哪些优化方向。

你有三个子 Agent 可以调度：
- skill_gap：当候选人有明显技能缺口时，专门给出学习路径和补足建议
- expression：当简历表达可以优化时（措辞、量化数据、STAR 结构），给出具体改写建议
- strategy：当需要投递策略建议时（投递时机、岗位选择、谈判策略），给出指导

请根据以下情况，返回需要启动的子 Agent 列表（JSON 格式）：
{"agents": ["skill_gap", "expression", "strategy"]}

说明：可以选择 1-3 个，根据实际需要决定，不必全选。"""),
        HumanMessage(f"""匹配度：{state['match_score']}分
已匹配技能：{', '.join(state['matched_skills'])}
缺失技能：{', '.join(state['missing_skills'])}
JD 核心要求：{state['jd_requirements']}"""),
    ])

    try:
        data = json.loads(response.content)
        agents = data.get("agents", ["skill_gap", "expression", "strategy"])
    except Exception:
        agents = ["skill_gap", "expression", "strategy"]

    print(f"[DEBUG] Supervisor 决定启动子 Agent：{agents}")
    return {"agents_to_run": agents}


def supervisor_fan_out(state: ResumeAnalysisState) -> list[Send]:
    """根据 supervisor 的决策，用 Send 并行分发到各子 Agent"""
    agent_map = {
        "skill_gap": "skill_gap_agent",
        "expression": "expression_agent",
        "strategy": "strategy_agent",
    }
    return [
        Send(agent_map[agent], state)
        for agent in state["agents_to_run"]
        if agent in agent_map
    ]


@observe(name="skill_gap_agent")
def skill_gap_agent_node(state: ResumeAnalysisState) -> dict:
    """子 Agent：专门针对技能缺口给出学习路径和补足建议"""
    response = model.invoke([
        SystemMessage("你是一个技能成长顾问，专门帮助求职者分析技能缺口并给出可执行的学习路径。"),
        HumanMessage(f"""候选人缺失以下技能：{', '.join(state['missing_skills'])}

目标岗位核心要求：{state['jd_requirements']}

请针对每个缺失技能，给出：
1. 该技能的重要程度（必须补 / 加分项）
2. 最短学习路径（具体资源或方式）
3. 预计补足时间

格式简洁，每个技能一段。"""),
    ])
    print(f"[DEBUG] skill_gap_agent 完成")
    return {"sub_suggestions": [f"【技能缺口补足建议】\n{response.content}"]}


@observe(name="expression_agent")
def expression_agent_node(state: ResumeAnalysisState) -> dict:
    """子 Agent：专门优化简历表达方式"""
    response = model.invoke([
        SystemMessage("你是一个简历表达优化专家，擅长将平淡的工作描述改写成有力的成果导向表达。"),
        HumanMessage(f"""简历内容（节选关键部分）：
{state['resume_text'][:1500]}

目标 JD 关键词：{', '.join(state['jd_must_skills'])}

请给出 2-3 条具体的表达优化建议，要求：
- 指出原文中具体可以改进的句子或段落
- 给出改写示例
- 说明改写原则（量化数据 / STAR 结构 / 关键词匹配）"""),
    ])
    print(f"[DEBUG] expression_agent 完成")
    return {"sub_suggestions": [f"【简历表达优化建议】\n{response.content}"]}


@observe(name="strategy_agent")
def strategy_agent_node(state: ResumeAnalysisState) -> dict:
    """子 Agent：专门给出投递策略建议"""
    response = model.invoke([
        SystemMessage("你是一个求职策略顾问，擅长根据候选人现状给出务实的投递和谈判建议。"),
        HumanMessage(f"""当前匹配度：{state['match_score']}分
已匹配技能：{', '.join(state['matched_skills'])}
缺失技能：{', '.join(state['missing_skills'])}
以下是知识库中相似岗位的参考数据（仅供参考，不是候选人要投的岗位）：
{state['rag_context'][:500]}

候选人当前要投递的目标岗位要求是：
{state['jd_requirements']}

请给出 2-3 条投递策略建议，包括：
- 当前匹配度下是否值得投递
- 投递时如何在 cover letter 或沟通中扬长避短
- 是否有更适合的相近岗位方向"""),
    ])
    print(f"[DEBUG] strategy_agent 完成")
    return {"sub_suggestions": [f"【投递策略建议】\n{response.content}"]}


@observe(name="aggregate_suggestions")
def aggregate_suggestions_node(state: ResumeAnalysisState) -> dict:
    """聚合节点：汇总所有子 Agent 的输出"""
    combined = "\n\n---\n\n".join(state.get("sub_suggestions", []))
    print(f"[DEBUG] 聚合 {len(state.get('sub_suggestions', []))} 个子 Agent 结果")
    return {"suggestions": combined}

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
    - 高匹配（>=75）：直接重写简历，跳过 Supervisor 流程
    - 低匹配（<75）：走 Supervisor → 子 Agent 并行 → 聚合 → 重写
    """
    score = state.get("match_score", 0)
    route = "rewrite" if score >= 75 else "supervisor"
    print(f"[DEBUG] 匹配分数: {score}，路由至: {route}")
    return route


# ── 构建图 ────────────────────────────────────────────────

graph = StateGraph(ResumeAnalysisState)

graph.add_node("jd_analysis", jd_analysis_node)
graph.add_node("rag_retrieval", rag_retrieval_node)
graph.add_node("match_analysis", match_analysis_node)

# Multi-Agent 节点
graph.add_node("supervisor", supervisor_node)
graph.add_node("skill_gap_agent", skill_gap_agent_node)
graph.add_node("expression_agent", expression_agent_node)
graph.add_node("strategy_agent", strategy_agent_node)
graph.add_node("aggregate_suggestions", aggregate_suggestions_node)

graph.add_node("rewrite", rewrite_node)

graph.set_entry_point("jd_analysis")
graph.add_edge("jd_analysis", "rag_retrieval")
graph.add_edge("rag_retrieval", "match_analysis")

# match_analysis 后条件路由
graph.add_conditional_edges(
    "match_analysis",
    route_after_match
)

# Supervisor 决策后并行 fan-out（Send API）
graph.add_conditional_edges("supervisor", supervisor_fan_out)

# 三个子 Agent 都汇入聚合节点
graph.add_edge("skill_gap_agent", "aggregate_suggestions")
graph.add_edge("expression_agent", "aggregate_suggestions")
graph.add_edge("strategy_agent", "aggregate_suggestions")

graph.add_edge("aggregate_suggestions", "rewrite")
graph.add_edge("rewrite", END)

app = graph.compile()