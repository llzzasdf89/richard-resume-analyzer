# state.py
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ResumeAnalysisState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # Inputs
    resume_text: str           # Parsed resume text
    jd_text: str               # Job description text

    # Job description analysis output
    jd_requirements: str       # Core job requirements
    jd_must_skills: list[str]  # Required skills
    jd_nice_skills: list[str]  # Nice-to-have skills

    # RAG retrieval output
    rag_context: str           # Retrieved similar job context

    # Match analysis output
    match_score: int           # Match score from 0 to 100
    matched_skills: list[str]  # Skills matched by the resume
    missing_skills: list[str]  # Skills missing from the resume

    # Supervisor output
    agents_to_run: list[str]   # Specialist agents selected by the supervisor

    # Parallel specialist agent output. operator.add appends instead of overwriting.
    sub_suggestions: Annotated[list[str], operator.add]

    # Aggregated optimization suggestions
    suggestions: str           # Combined targeted suggestions

    # Resume rewrite output
    rewritten_resume: str      # Rewritten resume sections

    # Error state
    error: str
