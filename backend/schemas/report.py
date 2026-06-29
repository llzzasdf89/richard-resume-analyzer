from pydantic import BaseModel


class ReportItem(BaseModel):
    id: str
    analysis_id: str
    title: str
    format: str
    created_at: str
