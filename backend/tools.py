# tools.py
import fitz  # PyMuPDF
from langchain_core.tools import tool


def parse_pdf(file_bytes: bytes) -> str:
    """解析 PDF 文件，返回文本内容"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


@tool
def search_similar_jobs(query: str) -> str:
    """根据技能或岗位关键词，搜索知识库中相似的岗位JD，获取市场参考信息。
    当需要了解某类岗位的典型要求、或验证某个技能在市场上的普遍程度时调用。
    """
    from rag import search_similar_jds
    return search_similar_jds(query)


@tool
def get_skill_market_demand(skill: str) -> str:
    """查询某个技能在当前招聘市场的真实需求情况。
    当评估候选人缺失某个技能对匹配度的实际影响时调用，帮助判断该技能是硬性门槛还是加分项。
    """
    from tavily import TavilyClient
    import os

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    result = client.search(
        query=f"{skill} 技能招聘市场需求 2025 是否必备",
        max_results=3,
        search_depth="basic",
    )
    snippets = [item["content"] for item in result.get("results", [])]
    if not snippets:
        return f"未找到关于 {skill} 的市场需求信息"
    return f"【{skill} 市场需求参考】\n" + "\n---\n".join(snippets)