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

# Embedding

def get_embedding(text: str) -> list[float]:
    """Call the DashScope embedding API."""
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

# Insert job description knowledge

def add_jd_to_knowledge(title: str, content: str):
    embedding = get_embedding(content)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO jd_knowledge (title, content, embedding) VALUES (%s, %s, %s)",
        (title, content, np.array(embedding))
    )
    conn.commit()
    cur.close()
    conn.close()
    return "Knowledge added"

def rerank_documents(query: str, documents: list[str], top_n: int = 3) -> list[int]:
    """Rerank retrieved RAG documents and return the top document indexes."""
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
        print(f"Knowledge base row count: {count}")

        # Retrieve extra vector candidates, then rerank them.
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
        print(f"Vector retrieval candidates: {len(rows)}")

    except Exception as e:
        import traceback
        print(f"SQL execution error: {traceback.format_exc()}")
        rows = []

    finally:
        cur.close()
        conn.close()

    if not rows:
        return "No similar job descriptions found in the knowledge base"

    # Rerank candidates.
    documents = [content for _, content in rows]
    try:
        top_indices = rerank_documents(query, documents, top_n=k)
        reranked_rows = [rows[i] for i in top_indices]
        print(f"Reranked top {k}: {[rows[i][0] for i in top_indices]}")
    except Exception as e:
        print(f"Rerank failed; falling back to vector results: {e}")
        reranked_rows = rows[:k]

    results = []
    for title, content in reranked_rows:
        results.append(f"{title}\n{content}")
    return "\n\n---\n\n".join(results)
