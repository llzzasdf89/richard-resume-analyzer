# rag.py
from dotenv import load_dotenv
import os
from db import get_conn
import requests
import numpy as np

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DASHSCOPE_API_KEY = os.getenv("API_KEY")

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

def search_similar_jds(query: str, k: int = 3) -> str:
    embedding = get_embedding(query)
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    print(f"embedding_str 前50字符：{embedding_str[:50]}")
    print(f"embedding_str 长度：{len(embedding_str)}")

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM jd_knowledge")
        count = cur.fetchone()[0]
        print(f"知识库总数据量：{count}")

        cur.execute(
            f"""
            SELECT title, content
            FROM jd_knowledge
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT {k}
            """
        )
        rows = cur.fetchall()
        print(f"检索到的行数：{len(rows)}")
        if rows:
            for row in rows:
                print(f"  标题：{row[0]}")

    except Exception as e:
        import traceback
        print(f"SQL 执行错误：{traceback.format_exc()}")
        rows = []

    finally:
        cur.close()
        conn.close()

    if not rows:
        return "知识库暂无相似岗位数据"

    results = []
    for title, content in rows:
        results.append(f"【{title}】\n{content}")
    return "\n\n---\n\n".join(results)