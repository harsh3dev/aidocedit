from pydantic import BaseModel
from typing import Optional

class DocumentCreate(BaseModel):
    userQuery: str
    selectedTemplate: str

class DocumentResponse(BaseModel):
    id: int
    user_query: str
    template_type: str
    content_generated: str

    class Config:
        from_attributes = True  # For ORM compatibility
