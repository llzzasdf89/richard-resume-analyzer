# main.py
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import app as analysis_graph
from tools import parse_pdf
from rag import add_jd_to_knowledge
from dotenv import load_dotenv
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

load_dotenv()

server = FastAPI(title="Resume Analyzer API")
executor = ThreadPoolExecutor()

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
            # 解析 PDF
            resume_text = parse_pdf(file_bytes)
            yield f"data: {json.dumps({'type': 'step', 'step': 'parsing', 'content': '简历解析完成'}, ensure_ascii=False)}\n\n"

            # 运行 Multi-Agent 分析
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                lambda: analysis_graph.invoke({
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
                    "suggestions": "",
                    "rewritten_resume": "",
                    "error": "",
                })
            )

            # 逐步返回各阶段结果
            yield f"data: {json.dumps({'type': 'step', 'step': 'jd_analysis', 'content': {'requirements': result['jd_requirements'], 'must_skills': result['jd_must_skills'], 'nice_skills': result['jd_nice_skills']}}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'match_score', 'content': {'score': result['match_score'], 'matched': result['matched_skills'], 'missing': result['missing_skills']}}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'suggestions', 'content': result['suggestions']}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'content': result['rewritten_resume']}, ensure_ascii=False)}\n\n"

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