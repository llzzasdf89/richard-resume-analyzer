from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: str
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None
