# main.py
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from graph import app as analysis_graph
from tools import parse_pdf
from rag import add_jd_to_knowledge
from dotenv import load_dotenv
import json
from db import init_db
import os
from langfuse.decorators import langfuse_context
from langfuse import Langfuse

load_dotenv()

lf = Langfuse()
langfuse_context.configure(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://jp.cloud.langfuse.com"),
    debug=False,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    yield

server = FastAPI(title="Resume Analyzer API", lifespan = lifespan)

server.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

@server.post("/api/analyze")
async def analyze(
    resume: UploadFile,
    jd: str = Form(...),
):
    file_bytes = await resume.read()

    async def generate():
        try:
            # 解析 PDF（同步，速度快，不需要 astream）
            yield f"data: {json.dumps({'type': 'progress', 'step': 'parsing', 'message': '简历解析中'}, ensure_ascii=False)}\n\n"
            resume_text = parse_pdf(file_bytes)
            yield f"data: {json.dumps({'type': 'step', 'step': 'parsing', 'message': '简历解析完成'}, ensure_ascii=False)}\n\n"

            initial_state = {
                "messages": [],
                "resume_text": resume_text,
                "jd_text": jd,
                "jd_requirements": "",
                "jd_must_skills": [],
                "jd_nice_skills": [],
                "rag_context": "",
                "match_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "agents_to_run": [],
                "sub_suggestions": [],
                "suggestions": "",
                "rewritten_resume": "",
                "error": "",
            }

            # 节点名 → 前端展示的"处理中"文案
            NODE_LABELS = {
                "jd_analysis":           "JD 分析中",
                "rag_retrieval":         "RAG 检索中",
                "match_analysis":        "匹配度分析中",
                "supervisor":            "正在启用技能缺口分析agent，表达优化agent，投递策略分析agent",
                "skill_gap_agent":       "技能缺口分析中",
                "expression_agent":      "表达优化分析中",
                "strategy_agent":        "投递策略分析中",
                "aggregate_suggestions": "汇总建议中",
                "rewrite":               "简历重写中",
            }
            TRACKED_NODES = set(NODE_LABELS.keys())

            # astream_events(version="v2")：
            #   on_chain_start → 节点刚开始，推"处理中"
            #   on_chain_end   → 节点完成，推实际结果
            async for event in analysis_graph.astream_events(initial_state, version="v2"):
                kind      = event["event"]
                node_name = event.get("name", "")

                if node_name not in TRACKED_NODES:
                    continue

                if kind == "on_chain_start":
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': NODE_LABELS[node_name]}, ensure_ascii=False)}\n\n"

                elif kind == "on_chain_end":
                    output = event["data"].get("output") or {}

                    if node_name == "jd_analysis":
                        yield f"data: {json.dumps({'type': 'step', 'step': 'jd_analysis', 'message': 'JD 分析完成', 'content': {'requirements': output.get('jd_requirements', ''), 'must_skills': output.get('jd_must_skills', []), 'nice_skills': output.get('jd_nice_skills', [])}}, ensure_ascii=False)}\n\n"

                    elif node_name == "rag_retrieval":
                        yield f"data: {json.dumps({'type': 'step', 'step': 'rag_retrieval', 'message': 'RAG 检索完成'}, ensure_ascii=False)}\n\n"

                    elif node_name == "match_analysis":
                        yield f"data: {json.dumps({'type': 'step', 'step': 'match_score', 'message': '匹配分析完成', 'content': {'score': output.get('match_score', 0), 'matched': output.get('matched_skills', []), 'missing': output.get('missing_skills', [])}}, ensure_ascii=False)}\n\n"

                    elif node_name == "supervisor":
                        agents = output.get('agents_to_run', [])
                        yield f"data: {json.dumps({'type': 'step', 'step': 'supervisor', 'message': f'启动子任务：{agents}'}, ensure_ascii=False)}\n\n"

                    elif node_name in ("skill_gap_agent", "expression_agent", "strategy_agent"):
                        sub = output.get("sub_suggestions", [])
                        if sub:
                            yield f"data: {json.dumps({'type': 'step', 'step': node_name, 'content': sub[-1], "message":f'{node_name} 分析完成'}, ensure_ascii=False)}\n\n"

                    elif node_name == "aggregate_suggestions":
                        yield f"data: {json.dumps({'type': 'step', 'step': 'suggestions', 'content': output.get('suggestions', ''), "message":"所有子agent结果汇总完成"}, ensure_ascii=False)}\n\n"

                    elif node_name == "rewrite":
                        yield f"data: {json.dumps({'type': 'done', 'content': output.get('rewritten_resume', '')}, ensure_ascii=False)}\n\n"

            langfuse_context.flush()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


class KnowledgeRequest(BaseModel):
    title: str
    content: str

@server.post("/api/knowledge")
async def add_knowledge(request: KnowledgeRequest):
    try:
        add_jd_to_knowledge(request.title, request.content)
        return {"success": True, "message": "添加成功"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@server.get("/health")
async def health():
    return {"status": "ok"}