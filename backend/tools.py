# tools.py
import fitz  # PyMuPDF
from langchain_core.tools import tool


def parse_pdf(file_bytes: bytes) -> str:
    """Parse a PDF file and return extracted text."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


@tool
def search_similar_jobs(query: str) -> str:
    """Search similar job descriptions in the knowledge base.

    Use this when the model needs typical role requirements or market context
    for a skill or position keyword.
    """
    from rag import search_similar_jds
    return search_similar_jds(query)


@tool
def get_skill_market_demand(skill: str) -> str:
    """Search current hiring-market demand for a skill.

    Use this when evaluating how much a missing skill should affect the match
    score and whether it is likely a hard requirement or a nice-to-have.
    """
    from tavily import TavilyClient
    import os

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    result = client.search(
        query=f"{skill} hiring market demand 2025 required skill or nice to have",
        max_results=3,
        search_depth="basic",
    )
    snippets = [item["content"] for item in result.get("results", [])]
    if not snippets:
        return f"No market demand information found for {skill}"
    return f"{skill} Market Demand Reference\n" + "\n---\n".join(snippets)
