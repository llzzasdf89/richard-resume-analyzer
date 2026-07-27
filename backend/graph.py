# graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from langfuse.decorators import observe
from state import ResumeAnalysisState
from rag import search_similar_jds
from tools import search_similar_jobs, get_skill_market_demand
from model_content import extract_json_object, extract_model_text
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatAnthropic(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

# Model bound to tools for the match_analysis ReAct agent.
_tools = [search_similar_jobs, get_skill_market_demand]
_tool_map = {t.name: t for t in _tools}
model_with_tools = model.bind_tools(_tools)

MATCH_ANALYSIS_SYSTEM_PROMPT = """You are a resume-to-job match analysis expert.

You can use two tools:
- search_similar_jobs: retrieve similar job descriptions from the knowledge base for market reference.
- get_skill_market_demand: check how important a skill is in the hiring market.

Current job description priority:
- The current job description is the source of truth.
- Retrieved RAG context is only secondary market reference.
- Do not add skills from RAG context unless they are clearly relevant to the current job description.

Analysis steps:
1. Read the resume and current job description, then identify the most important role-fit signals and skill gaps.
2. For skills with uncertain importance, call get_skill_market_demand up to 3 times. Prioritize the most critical gaps from the current job description.
3. If more market context is needed, call search_similar_jobs.
4. After tool use is complete, return a valid JSON object with exactly these fields:
   - match_score: an integer from 0 to 100.
   - matched_skills: an array of skills that are explicitly shown in the resume AND directly relevant to the current job description requirements.
   - missing_skills: an array of important current-job-description skills or tools that are required or useful but not shown in the resume.

Rules for matched_skills:
- Do not include resume-only skills that are unrelated to the current job description.
- Do not include frontend, backend, cloud, or AI engineering skills unless the current job description asks for them.
- For example, do not include React for an ecology, biology, environmental science, or statistical-analysis role unless the job description explicitly asks for frontend development.
- If a resume skill is impressive but unrelated to the current job description, leave it out of matched_skills.

Scoring guide:
- 90-100: Highly aligned and satisfies nearly all requirements.
- 70-89: Core skills match, with a few gaps.
- 40-69: Partial match with clear gaps.
- 10-39: Low relevance and major skill mismatch.
- 1-9: Almost no relevant skills, but the candidate has some transferable foundation.
- Use 0 only when the candidate has no relevant background.

Return only the JSON object. Do not include explanations."""

# Graph nodes

@observe(name="jd_analysis")
def jd_analysis_node(state: ResumeAnalysisState) -> dict:
    """Extract core requirements, required skills, and nice-to-have skills."""
    response = model.invoke([
        SystemMessage("""You are a job description analysis expert.
Analyze the given job description and return the following information as JSON:
{
  "requirements": "A concise description of the core role requirements",
  "must_skills": ["required skill 1", "required skill 2"],
  "nice_skills": ["nice-to-have skill 1", "nice-to-have skill 2"]
}
Return JSON only. Do not include any extra text."""),
        HumanMessage(f"Analyze this job description:\n\n{state['jd_text']}")
    ])

    try:
        data = extract_json_object(response.content)
        return {
            "jd_requirements": data.get("requirements", ""),
            "jd_must_skills": data.get("must_skills", []),
            "jd_nice_skills": data.get("nice_skills", []),
        }
    except Exception:
        return {
            "jd_requirements": extract_model_text(response.content),
            "jd_must_skills": [],
            "jd_nice_skills": [],
        }

@observe(name="rag_retrieval")
def rag_retrieval_node(state: ResumeAnalysisState) -> dict:
    """Retrieve similar historical job descriptions from the RAG store."""
    query = f"{state['jd_requirements']} {' '.join(state['jd_must_skills'])}"
    print(f"RAG query: {query}")
    context = search_similar_jds(query)
    print(f"RAG retrieval result:\n{context[:300]}")
    return {"rag_context": context}

@observe(name="match_analysis")
def match_analysis_node(state: ResumeAnalysisState) -> dict:
    """Run ReAct match analysis and decide whether market tools are needed."""

    messages = [
        SystemMessage(MATCH_ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(f"""Resume:
{state['resume_text']}

Core job requirements:
{state['jd_requirements']}

Required skills:
{', '.join(state['jd_must_skills'])}

Nice-to-have skills:
{', '.join(state['jd_nice_skills'])}

Retrieved RAG context:
{state['rag_context']}

Use the current job description as the source of truth. The retrieved RAG context is only supporting market context.

Start the analysis."""),
    ]

    # ReAct loop.
    MAX_ITERATIONS = 5
    for i in range(MAX_ITERATIONS):
        response = model_with_tools.invoke(messages)
        messages.append(response)

        print(f"[DEBUG] match_analysis round {i+1}, tool_calls: {[tc['name'] for tc in response.tool_calls]}")

        # No tool calls means the model considers the reasoning complete.
        if not response.tool_calls:
            break

        # Execute every tool call and return the result to the model.
        for tool_call in response.tool_calls:
            tool_fn = _tool_map.get(tool_call["name"])
            if tool_fn is None:
                result = f"Unknown tool: {tool_call['name']}"
            else:
                result = tool_fn.invoke(tool_call["args"])
                print(f"[DEBUG] Tool {tool_call['name']} returned: {str(result)[:200]}")

            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            ))
        # Continue so the model can decide the next step after seeing tool results.

    # Parse final output.
    final_content = extract_model_text(response.content)
    print(f"[DEBUG] match_analysis final output: {final_content[:500]}")

    try:
        data = extract_json_object(final_content)

        matched = data.get("matched_skills", [])
        missing = data.get("missing_skills", [])

        # Treat placeholder outputs as parse failures.
        placeholder_keywords = {"skill 1", "skill 2", "missing skill 1", "missing skill 2"}
        if set(matched) & placeholder_keywords or set(missing) & placeholder_keywords:
            print("[DEBUG] Placeholder output detected; falling back")
            raise ValueError("Model returned template placeholders")

        return {
            "match_score": data.get("match_score", 0),
            "matched_skills": matched,
            "missing_skills": missing,
        }
    except Exception as e:
        print(f"[DEBUG] match_analysis parse failed: {e}")
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
        }

@observe(name="supervisor")
def supervisor_node(state: ResumeAnalysisState) -> dict:
    """Decide which specialist agents should run."""
    response = model.invoke([
        SystemMessage("""You are a task routing expert. Decide which optimization directions are needed based on the resume match result.

You can route to three specialist agents:
- skill_gap: use when the candidate has meaningful skill gaps and needs a learning path.
- expression: use when resume phrasing, metrics, or STAR structure can be improved.
- strategy: use when application strategy guidance is needed.

Return the needed agents as JSON:
{"agents": ["skill_gap", "expression", "strategy"]}

You can choose 1-3 agents. Do not select all unless all are useful."""),
        HumanMessage(f"""Match score: {state['match_score']}
Matched skills: {', '.join(state['matched_skills'])}
Missing skills: {', '.join(state['missing_skills'])}
Core job requirements: {state['jd_requirements']}"""),
    ])

    try:
        data = extract_json_object(response.content)
        agents = data.get("agents", ["skill_gap", "expression", "strategy"])
    except Exception:
        agents = ["skill_gap", "expression", "strategy"]

    print(f"[DEBUG] Supervisor selected specialist agents: {agents}")
    return {"agents_to_run": agents}


def supervisor_fan_out(state: ResumeAnalysisState) -> list[Send]:
    """Fan out to specialist agents selected by the supervisor."""
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
    """Provide learning paths and gap-closing suggestions for missing skills."""
    response = model.invoke([
        SystemMessage("You are a skill growth advisor who gives practical learning paths for job seekers."),
        HumanMessage(f"""The candidate is missing these skills: {', '.join(state['missing_skills'])}

Core target role requirements: {state['jd_requirements']}

For each missing skill, provide:
1. Importance level (must-have or nice-to-have).
2. Shortest practical learning path.
3. Estimated time to close the gap.

Keep the format concise. Use one paragraph per skill."""),
    ])
    print(f"[DEBUG] skill_gap_agent completed")
    return {
        "sub_suggestions": [
            f"Skill Gap Recommendations\n{extract_model_text(response.content)}"
        ]
    }


@observe(name="expression_agent")
def expression_agent_node(state: ResumeAnalysisState) -> dict:
    """Improve resume wording, impact framing, and role alignment."""
    response = model.invoke([
        SystemMessage("You are a resume writing expert who turns plain work descriptions into strong outcome-oriented bullets."),
        HumanMessage(f"""Resume excerpt:
{state['resume_text'][:1500]}

Target job keywords: {', '.join(state['jd_must_skills'])}

Provide 2-3 specific expression improvements:
- Point to the specific sentence or section that can be improved.
- Provide a rewritten example.
- Explain the principle, such as metrics, STAR structure, or keyword alignment."""),
    ])
    print(f"[DEBUG] expression_agent completed")
    return {
        "sub_suggestions": [
            f"Resume Expression Recommendations\n{extract_model_text(response.content)}"
        ]
    }


@observe(name="strategy_agent")
def strategy_agent_node(state: ResumeAnalysisState) -> dict:
    """Provide practical application strategy guidance."""
    response = model.invoke([
        SystemMessage("You are a job search strategy advisor who gives practical application and positioning advice."),
        HumanMessage(f"""Current match score: {state['match_score']}
Matched skills: {', '.join(state['matched_skills'])}
Missing skills: {', '.join(state['missing_skills'])}
Similar job context from the knowledge base:
{state['rag_context'][:500]}

The candidate's target role requirements are:
{state['jd_requirements']}

Give 2-3 application strategy recommendations, including:
- Whether the role is worth applying to at the current match level.
- How to position strengths and gaps in a cover letter or recruiter conversation.
- Whether adjacent roles may be a better fit."""),
    ])
    print(f"[DEBUG] strategy_agent completed")
    return {
        "sub_suggestions": [
            f"Application Strategy Recommendations\n{extract_model_text(response.content)}"
        ]
    }


@observe(name="aggregate_suggestions")
def aggregate_suggestions_node(state: ResumeAnalysisState) -> dict:
    """Combine all specialist agent outputs."""
    combined = "\n\n---\n\n".join(state.get("sub_suggestions", []))
    print(f"[DEBUG] Aggregating {len(state.get('sub_suggestions', []))} specialist results")
    return {"suggestions": combined}

@observe(name="rewrite")
def rewrite_node(state: ResumeAnalysisState) -> dict:
    """Rewrite key resume sections for the target job description."""
    response = model.invoke([
        SystemMessage("You are a resume writing expert who optimizes resume content for a specific job description."),
        HumanMessage(f"""Original resume:
{state['resume_text']}

Target job requirements:
{state['jd_requirements']}

Required skills: {', '.join(state['jd_must_skills'])}

Missing skills to strengthen or honestly address: {', '.join(state['missing_skills'])}

Rewrite the Work Experience and Skills sections so they better align with the target job description.
Do not fabricate experience. Only improve framing, wording, structure, and emphasis.""")
    ])
    return {"rewritten_resume": extract_model_text(response.content)}

# Conditional routing

def route_after_match(state: ResumeAnalysisState) -> str:
    """Decide the next node based on match score.

    - High match (>=75): rewrite directly and skip supervisor.
    - Lower match (<75): supervisor, specialist agents, aggregate, then rewrite.
    """
    score = state.get("match_score", 0)
    route = "rewrite" if score >= 75 else "supervisor"
    print(f"[DEBUG] Match score: {score}; route: {route}")
    return route


# Build graph

graph = StateGraph(ResumeAnalysisState)

graph.add_node("jd_analysis", jd_analysis_node)
graph.add_node("rag_retrieval", rag_retrieval_node)
graph.add_node("match_analysis", match_analysis_node)

# Multi-agent nodes
graph.add_node("supervisor", supervisor_node)
graph.add_node("skill_gap_agent", skill_gap_agent_node)
graph.add_node("expression_agent", expression_agent_node)
graph.add_node("strategy_agent", strategy_agent_node)
graph.add_node("aggregate_suggestions", aggregate_suggestions_node)

graph.add_node("rewrite", rewrite_node)

graph.set_entry_point("jd_analysis")
graph.add_edge("jd_analysis", "rag_retrieval")
graph.add_edge("rag_retrieval", "match_analysis")

# Conditional route after match analysis.
graph.add_conditional_edges(
    "match_analysis",
    route_after_match
)

# Parallel fan-out after supervisor routing.
graph.add_conditional_edges("supervisor", supervisor_fan_out)

# All specialist agents merge into the aggregation node.
graph.add_edge("skill_gap_agent", "aggregate_suggestions")
graph.add_edge("expression_agent", "aggregate_suggestions")
graph.add_edge("strategy_agent", "aggregate_suggestions")

graph.add_edge("aggregate_suggestions", "rewrite")
graph.add_edge("rewrite", END)

app = graph.compile()
