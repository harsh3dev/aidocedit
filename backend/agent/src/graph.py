from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState

from .nodes import (
    section_planner_node,
    section_generator_node,
    websocket_streamer_node,
    feedback_waiter_node,
    section_updater_node,
    flow_controller_node
)

checkpointer = MemorySaver()

builder = StateGraph(AgentState)

builder.add_node("plan", section_planner_node)
builder.add_node("generate", section_generator_node)
builder.add_node("stream", websocket_streamer_node)
builder.add_node("wait_feedback", feedback_waiter_node)
builder.add_node("update", section_updater_node)
builder.add_node("next", flow_controller_node)

builder.set_entry_point("plan")

builder.add_edge("plan", "generate")
builder.add_edge("generate", "stream")
builder.add_edge("stream", "wait_feedback")
builder.add_edge("wait_feedback", "update")
builder.add_edge("update", "next")

builder.add_conditional_edges(
    "next",
    lambda state: (
        END if state.get("completed", False) or state.get("last_feedback_type") == "end"
        else "generate" if state.get("last_feedback_type") == "regenerate" and not state.get("completed", False)
        else "generate" if not state.get("completed", False) and "current_section_index" in state and "section_names" in state and state["current_section_index"] + 1 < len(state["section_names"])
        else END
    )
)

document_graph = builder.compile(checkpointer=checkpointer)
