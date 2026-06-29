from pydantic import BaseModel


class ResumeItem(BaseModel):
    id: str
    original_filename: str
    file_size: int
    mime_type: str
    created_at: str
