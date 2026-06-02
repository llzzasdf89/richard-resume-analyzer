# rag.py
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from dotenv import load_dotenv
import os

load_dotenv()

# 用 Anthropic 的 Embedding（DashScope 中转）
from langchain_community.embeddings import DashScopeEmbeddings

embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key=os.getenv("API_KEY"),
)

CONNECTION_STRING = os.getenv("DATABASE_URL")
COLLECTION_NAME = "jd_knowledge"

def get_vectorstore():
    return PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        embedding_function=embeddings,
    )

def add_jd_to_knowledge(title: str, content: str):
    """向知识库添加 JD"""
    vectorstore = get_vectorstore()
    doc = Document(
        page_content=content,
        metadata={"title": title}
    )
    vectorstore.add_documents([doc])
    return "添加成功"

def search_similar_jds(query: str, k: int = 3) -> str:
    """检索相似 JD"""
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        return "知识库暂无相似岗位数据"
    results = []
    for doc in docs:
        results.append(f"【{doc.metadata.get('title', '未知岗位')}】\n{doc.page_content}")
    return "\n\n---\n\n".join(results)