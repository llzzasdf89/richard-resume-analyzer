# rag.py
from dotenv import load_dotenv
import os
from db import get_conn
import requests
import numpy as np
from FlagEmbedding import FlagReranker



load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DASHSCOPE_API_KEY = os.getenv("API_KEY")
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

# ── Embedding ─────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    """调用 DashScope Embedding API"""
    res = requests.post(
        "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
        headers={
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "text-embedding-v3",
            "input": {"texts": [text]},
            "parameters": {"dimension": 1024}
        }
    )
    return res.json()["output"]["embeddings"][0]["embedding"]

# ── 写入 JD ────────────────────────────────────────────────

def add_jd_to_knowledge(title: str, content: str):
    embedding = get_embedding(content)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO jd_knowledge (title, content, embedding) VALUES (%s, %s, %s)",
        (title, content, np.array(embedding))  # 转成 numpy array
    )
    conn.commit()
    cur.close()
    conn.close()
    return "添加成功"

def rerank_documents(query: str, documents: list[str], top_n: int = 3) -> list[int]:
    """对RAG查询出的结果进行二次过滤，返回最有关联的top_n个结果"""
    scores = []
    for index,doc in enumerate(documents):
        scores.append({
            "score": reranker.compute_score([query, doc]),
            "index":index
        })
    scores.sort(key=lambda x: x["score"], reverse=True)
    return [item["index"] for item in scores[:top_n]]


def search_similar_jds(query: str, k: int = 3) -> str:
    embedding = get_embedding(query)
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM jd_knowledge")
        count = cur.fetchone()[0]
        print(f"知识库总数据量：{count}")

        # 向量召回：多取候选，再 Rerank 精排
        candidate_k = min(k * 3, count)
        cur.execute(
            f"""
            SELECT title, content
            FROM jd_knowledge
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT {candidate_k}
            """
        )
        rows = cur.fetchall()
        print(f"向量召回候选数：{len(rows)}")

    except Exception as e:
        import traceback
        print(f"SQL 执行错误：{traceback.format_exc()}")
        rows = []

    finally:
        cur.close()
        conn.close()

    if not rows:
        return "知识库暂无相似岗位数据"

    # Rerank 精排
    documents = [content for _, content in rows]
    try:
        top_indices = rerank_documents(query, documents, top_n=k)
        reranked_rows = [rows[i] for i in top_indices]
        print(f"Rerank 后 Top {k}：{[rows[i][0] for i in top_indices]}")
    except Exception as e:
        print(f"Rerank 失败，回退到向量召回结果：{e}")
        reranked_rows = rows[:k]

    results = []
    for title, content in reranked_rows:
        results.append(f"【{title}】\n{content}")
    return "\n\n---\n\n".join(results)