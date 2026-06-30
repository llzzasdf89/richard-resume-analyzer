from pydantic import BaseModel


class AnalysisCreateResponse(BaseModel):
    analysis_id: str
    resume_id: str
    status: str


class AnalysisListItem(BaseModel):
    id: str
    resume_id: str
    status: str
    score: int | None = None
    progress: int = 0
    current_step: str | None = None
    job_title: str | None = None
    company: str | None = None
