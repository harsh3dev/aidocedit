from typing import Annotated, List, Optional, Callable
from langchain_core.messages import BaseMessage
import operator
from typing import TypedDict
from .struct import Section, Feedback, SearchResults

def max_value(values):
    if not values:
        return 0
    max_val = values[0]
    for val in values[1:]:
        if val > max_val:
            max_val = val
    return max_val

class AgentState(TypedDict):
    query: str
    template_type: str
    document_id: str

    messages: Annotated[List[BaseMessage], operator.add]
    sections: List[Section]
    current_section_index: int
    section_names: List[str]
    search_results: Annotated[List[SearchResults], operator.add]
    current_section_id: Optional[str]
    current_section_content: str

    final_html_sections: Annotated[List[str], operator.add]

    latest_feedback: Optional[Feedback]
    section_approved: bool
    last_feedback_type: Optional[str]
    feedback: Optional[dict]
