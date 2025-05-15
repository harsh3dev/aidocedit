from pydantic import BaseModel

class DocumentCreate(BaseModel):
    userQuery: str
    selectedTemplate: str
