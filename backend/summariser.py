from backend.schemas import State
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END
from langchain_core.messages import SystemMessage, HumanMessage,RemoveMessage
from config import GEMINI_API_KEY, GEMINI_MODEL

gemini = GEMINI_API_KEY
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=gemini)
genai.configure(api_key=gemini)

def summarize_conversation(state: State):
    
    # First, we get any existing summary
    summary = state.get("summary", "")

    # Create our summarization prompt 
    if summary:
        
        # A summary already exists
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
        
    else:
        summary_message = "Create a summary of the conversation above:"

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response =llm.invoke(messages)
    
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"messages":  delete_messages, "summary": response.content,}

# Determine whether to end or summarize the conversation
def should_continue_summarise(state: State):
    
    """Return the next node to execute."""
    
    messages = state["messages"]
    
    # If there are more than six messages, then we summarize the conversation
    if len(messages) > 6:
        return "summarize"
    
    # Otherwise we can just end
    return END