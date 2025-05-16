from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langgraph.types import Command
from typing import Literal
from .state import AgentState
from .configuration import Configuration
from .utils import init_llm
from models import save_section_to_db, get_next_section, update_section_feedback
from ws_manager import stream_to_websocket, wait_for_feedback_from_ws, send_document_complete, send_stream_end
from .prompts import MAIN_SYSTEM_PROMPT
from templates import TEMPLATE_SECTIONS
import asyncio
import uuid

def section_planner_node(state: AgentState, config: RunnableConfig) -> Command[Literal["generate"]]:
    """
    Determines the section structure of the document.
    If a template has predefined sections, use those.
    Otherwise, generate section titles using the LLM.
    """
    template = state.get("template_type", "")
    query = state.get("query", "General Information Document")

    if template in TEMPLATE_SECTIONS:
        section_names = TEMPLATE_SECTIONS[template]
        print(f"Using template sections: {section_names}")
    else:
        configurable = Configuration.from_runnable_config(config)
        llm = init_llm(provider=configurable.provider, model=configurable.model)  # type: ignore

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(MAIN_SYSTEM_PROMPT + 
            """You must generate at least 3 section names for the document based on the query.
            Return these as a list of strings. Each section name should be clear and descriptive.
            For example, for a query about machine learning, you might return:
            ["Introduction to Machine Learning", "Types of Machine Learning Algorithms", "Applications of Machine Learning"]
            """),
            HumanMessagePromptTemplate.from_template("""
            Template: {template_type}
            Query: {query}
            """)
        ])

        section_llm = prompt | llm.with_structured_output(list)
        try:
            section_names = section_llm.invoke({"template_type": template, "query": query})
            if isinstance(section_names, str):
                import ast
                try:
                    section_names = ast.literal_eval(section_names)
                except (ValueError, SyntaxError):
                    section_names = ["Introduction", "Main Content", "Conclusion"]

            if not section_names or not isinstance(section_names, list) or len(section_names) == 0:
                section_names = ["Introduction", "Main Content", "Conclusion"]
            print(f"Generated sections: {section_names}")
        except Exception as e:
            print(f"Error generating sections: {str(e)}")
            section_names = ["Introduction", "Main Content", "Conclusion"]
            print(f"Using fallback sections: {section_names}")

    state["section_names"] = section_names

    return Command(update={
        "section_names": section_names,
        "current_section_index": 0
    }, goto="generate")


def section_generator_node(state: AgentState, config: RunnableConfig) -> Command[Literal["stream"]]:
    """
    Generates HTML content for the current section.
    """
    print(f"Current state: {state.get('section_names', [])}")
    if "section_names" not in state or not state["section_names"]:
        print("No section names found in state, going back to planning stage")
        return Command(update={"section_names": []}, goto="plan")

    if "current_section_index" not in state or state["current_section_index"] >= len(state["section_names"]):
        print("Invalid or missing current_section_index, resetting to 0")
        return Command(update={"current_section_index": 0}, goto="plan")

    configurable = Configuration.from_runnable_config(config)
    llm = init_llm(provider=configurable.provider, model=configurable.model)

    current_section = state["section_names"][state["current_section_index"]]
    print(f"Generating content for section: {current_section} (index: {state['current_section_index']})")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("""
        You are an AI content writer. Write detailed HTML content for the following section of a document.
        Do not include headings. Return HTML only.
        ## OUTPUT FORMAT RULES:
            - Wrap each section in an outer `<div data-section="SectionName">...</div>` to help the frontend isolate and edit sections.
            - Use appropriate HTML tags:
            - `<h1>`, `<h2>` for headings
            - `<p>` for paragraphs
            - `<ul><li>` for bullet lists
            - `<pre><code>` for code blocks (include comments if needed)
            - Do **not** include full document output at once. Output only the section currently being generated.

        ## EXAMPLE OUTPUT (for a "Heading" section):
            ```html
            <div data-section="Heading">
            <h1>Understanding REST APIs: A Beginner's Guide</h1>
            </div>
            ````
        """),
        HumanMessagePromptTemplate.from_template("""
        Document Query: {query}
        Section: {section_name}
        """)
    ])

    content_llm = prompt | llm
    try:
        response = content_llm.invoke({
            "query": state["query"],
            "section_name": current_section
        })
        
        if hasattr(response, 'content'):
            html_content = response.content
        else:
            html_content = str(response)
            
        html_content = html_content.replace('```html', '').replace('```', '').strip()
        
    except Exception as e:
        print(f"Error generating content for section {current_section}: {str(e)}")
        html_content = f"<div data-section=\"{current_section}\"><p>Error generating content. Please try again.</p></div>"
    
    section_id = f"temp-{uuid.uuid4()}"
    
    if not isinstance(html_content, str):
        html_content = str(html_content)
    
    section_data = {
        "id": section_id,
        "name": current_section,
        "content": html_content
    }
    
    if "sections" not in state:
        state["sections"] = []
    state["sections"].append(section_data)
    
    if "final_html_sections" not in state:
        state["final_html_sections"] = []
    
    state["final_html_sections"].append(html_content)

    return Command(update={
        "current_section_content": html_content,
        "current_section_id": section_id
    }, goto="stream")



def websocket_streamer_node(state: AgentState, config: RunnableConfig) -> Command[Literal["wait_feedback"]]:
    """
    Streams the generated section HTML to the frontend via WebSocket.
    """
    required_keys = ["document_id", "current_section_id", "section_names", "current_section_index", "current_section_content"]
    missing_keys = [key for key in required_keys if key not in state]

    if missing_keys:
        print(f"Missing required keys in state: {missing_keys}")
        return Command(update={"missing_keys": missing_keys}, goto="plan")

    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        content_html = state["current_section_content"]
        if hasattr(content_html, 'content'):
            content_html = content_html.content
        if isinstance(content_html, str) and '```' in content_html:
            content_html = content_html.replace('```html', '').replace('```', '').strip()
        
        document_id = state["document_id"]
        
        section_name = state["section_names"][state["current_section_index"]]
        is_editable = True
        
        if any(keyword in section_name.lower() for keyword in 
              ["code", "configuration", "installation", "setup", "technical", "api reference"]):
            is_editable = False
            
        stream_to_websocket(
            document_id=document_id,
            section_id=state["current_section_id"],
            section_name=section_name,
            content_html=content_html,
            is_editable=is_editable
        )
        print(f"Successfully streamed section {state['section_names'][state['current_section_index']]} to WebSocket")
    except Exception as e:
        print(f"Error streaming to WebSocket: {str(e)}")
        
    return Command(goto="wait_feedback")



def feedback_waiter_node(state: AgentState, config: RunnableConfig) -> Command[Literal["update"]]:
    """
    Waits for human feedback through the frontend WebSocket and returns control.
    """
    if "current_section_id" not in state:
        print("Missing current_section_id in state during feedback wait")
        raise ValueError("Missing current_section_id in state")
        
    try:
        feedback = wait_for_feedback_from_ws(section_id=state["current_section_id"])
        if feedback["feedback_type"] == "end":
            print("Feedback type is 'end', ending workflow")
            return Command(update={"completed": True, "feedback": feedback}, goto="update")
        print(f"Received feedback for section {state['current_section_id']}: {feedback}")
        return Command(update={"feedback": feedback}, goto="update")
    except Exception as e:
        print(f"Error waiting for feedback: {str(e)}")
        raise e



def section_updater_node(state: AgentState, config: RunnableConfig) -> Command[Literal["next"]]:
    """
    Updates the state based on human feedback for the current section.
    No database updates for now, we're just keeping everything in memory.
    """
    if "feedback" not in state or not state["feedback"]:
        print("No feedback found in state, returning to next node")
        return Command(update={"last_feedback_type": "continue"}, goto="next")
    
    feedback = state["feedback"]
    feedback_type = feedback.get("feedback_type", "continue")
    
    if "current_section_id" not in state:
        print("Missing current_section_id in update section node")
        return Command(update={"last_feedback_type": "continue"}, goto="next")
    
    if feedback.get("edited_content") and state.get("sections"):
        for section in state.get("sections", []):
            if section.get("id") == state["current_section_id"]:
                section["content"] = feedback.get("edited_content")
                break
    
    print(f"Processing feedback: {feedback_type} for section {state['current_section_id']}")
    
    state["feedback"] = None
    
    return Command(update={"last_feedback_type": feedback_type}, goto="next")


def flow_controller_node(state: AgentState, config: RunnableConfig) -> Command:
    """
    Decides the next step based on feedback and remaining sections.
    """
    last_feedback = state.get("last_feedback_type", "continue")
    
    if last_feedback == "end" or state.get("completed", False):
        print("Ending workflow based on 'end' feedback or completed state")
        final_content = []
        if "sections" in state and isinstance(state["sections"], list):
            for section in state["sections"]:
                if isinstance(section, dict) and "content" in section:
                    final_content.append(section["content"])
        return Command(update={"completed": True, "final_content": final_content}, goto="end")
    
    if last_feedback == "regenerate":
        return Command(goto="generate")

    if ("section_names" in state and 
        "current_section_index" in state and 
        isinstance(state.get("section_names"), list) and
        state["current_section_index"] + 1 < len(state["section_names"])):
        next_index = state["current_section_index"] + 1
        print(f"Moving to next section index: {next_index}")
        return Command(update={"current_section_index": next_index}, goto="generate")
    
    print("All sections completed, ending workflow")
    final_content = []
    if "sections" in state and isinstance(state["sections"], list):
        for section in state["sections"]:
            if isinstance(section, dict) and "content" in section:
                final_content.append(section["content"])
    
    if "document_id" in state:
        try:
            send_stream_end(state["document_id"])
            send_document_complete(state["document_id"])
            print(f"Sent completion messages for document {state['document_id']}")
        except Exception as e:
            print(f"Error sending completion messages: {str(e)}")
                
    return Command(update={"completed": True, "final_content": final_content}, goto="end")
