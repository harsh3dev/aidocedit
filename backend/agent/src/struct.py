from typing import List, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel


class Section(BaseModel):
    """Represents one section of the document."""
    title: str
    content: Optional[str] = None
    messages: Optional[List[BaseMessage]] = None


class Feedback(BaseModel):
    """Represents feedback given by a human."""
    section_title: str
    comments: str
    approved: bool


class SearchResults(BaseModel):
    """Represents a search result used in research."""
    query: str
    results: List[str]
