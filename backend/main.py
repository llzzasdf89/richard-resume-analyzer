# main.py
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from dotenv import load_dotenv
import json
from db import init_db
import os
from langfuse.decorators import langfuse_context
from langfuse import Langfuse
from middleware.access_log import AccessLogMiddleware
from middleware.request_id import RequestIdMiddleware
from routers.analyses import router as analyses_router
from routers.auth import router as auth_router
from routers.health import router as health_router
from routers.reports import router as reports_router
from routers.resumes import router as resumes_router

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
    # Initialize the database on startup.
    init_db()
    yield

server = FastAPI(title="Resume Analyzer API", lifespan = lifespan)

server.add_middleware(AccessLogMiddleware)
server.add_middleware(RequestIdMiddleware)

server.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

server.include_router(health_router, tags=["health"])
server.include_router(auth_router, prefix="/api/v1", tags=["auth"])
server.include_router(analyses_router, prefix="/api/v1", tags=["analyses"])
server.include_router(resumes_router, prefix="/api/v1", tags=["resumes"])
server.include_router(reports_router, prefix="/api/v1", tags=["reports"])

@server.post("/api/analyze")
async def analyze(
    resume: UploadFile,
    jd: str = Form(...),
):
    file_bytes = await resume.read()

    async def generate():
        try:
            from graph import app as analysis_graph
            from tools import parse_pdf

            # Parse the PDF before starting the graph stream.
            yield f"data: {json.dumps({'type': 'progress', 'step': 'parsing', 'message': 'Parsing resume'}, ensure_ascii=False)}\n\n"
            resume_text = parse_pdf(file_bytes)
            yield f"data: {json.dumps({'type': 'step', 'step': 'parsing', 'message': 'Resume parsed'}, ensure_ascii=False)}\n\n"

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

            # Node name to frontend processing label.
            NODE_LABELS = {
                "jd_analysis":           "Analyzing job description",
                "rag_retrieval":         "Retrieving similar job context",
                "match_analysis":        "Calculating match score",
                "supervisor":            "Selecting specialist agents",
                "skill_gap_agent":       "Analyzing skill gaps",
                "expression_agent":      "Reviewing resume expression",
                "strategy_agent":        "Preparing application strategy",
                "aggregate_suggestions": "Combining recommendations",
                "rewrite":               "Optimizing resume content",
            }
            TRACKED_NODES = set(NODE_LABELS.keys())

            # astream_events(version="v2"):
            #   on_chain_start pushes a processing label.
            #   on_chain_end pushes the node output.
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
                        yield f"data: {json.dumps({'type': 'step', 'step': 'jd_analysis', 'message': 'Job description analysis completed', 'content': {'requirements': output.get('jd_requirements', ''), 'must_skills': output.get('jd_must_skills', []), 'nice_skills': output.get('jd_nice_skills', [])}}, ensure_ascii=False)}\n\n"

                    elif node_name == "rag_retrieval":
                        yield f"data: {json.dumps({'type': 'step', 'step': 'rag_retrieval', 'message': 'RAG retrieval completed'}, ensure_ascii=False)}\n\n"

                    elif node_name == "match_analysis":
                        yield f"data: {json.dumps({'type': 'step', 'step': 'match_score', 'message': 'Match analysis completed', 'content': {'score': output.get('match_score', 0), 'matched': output.get('matched_skills', []), 'missing': output.get('missing_skills', [])}}, ensure_ascii=False)}\n\n"

                    elif node_name == "supervisor":
                        agents = output.get('agents_to_run', [])
                        yield f"data: {json.dumps({'type': 'step', 'step': 'supervisor', 'message': f'Starting specialist agents: {agents}'}, ensure_ascii=False)}\n\n"

                    elif node_name in ("skill_gap_agent", "expression_agent", "strategy_agent"):
                        sub = output.get("sub_suggestions", [])
                        if sub:
                            yield f"data: {json.dumps({'type': 'step', 'step': node_name, 'content': sub[-1], "message":f'{node_name} completed'}, ensure_ascii=False)}\n\n"

                    elif node_name == "aggregate_suggestions":
                        yield f"data: {json.dumps({'type': 'step', 'step': 'suggestions', 'content': output.get('suggestions', ''), "message":"All specialist recommendations combined"}, ensure_ascii=False)}\n\n"

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
        from rag import add_jd_to_knowledge

        add_jd_to_knowledge(request.title, request.content)
        return {"success": True, "message": "Knowledge added"}
    except Exception as e:
        return {"success": False, "message": str(e)}
