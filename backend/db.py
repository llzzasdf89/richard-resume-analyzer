import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jd_knowledge (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            embedding vector(1024)
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS jd_knowledge_embedding_idx
        ON jd_knowledge USING hnsw (embedding vector_cosine_ops)
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("数据库初始化完成")