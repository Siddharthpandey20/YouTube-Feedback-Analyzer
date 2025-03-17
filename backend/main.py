from backend.analysis import analyse
from backend.major import analyze_major_issues
from backend.summariser import summarize_conversation, should_continue_summarise
from backend.schemas import State
from langgraph.graph import StateGraph, START, END
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from typing import Dict, Any
#for proper printing 
from pprint import pprint
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown



# Initialize Gemini
gemini = 'AIzaSyCa3MN7Nwvhq0QQRrEzEmfnHuajBWUl_zU'
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=gemini)
genai.configure(api_key=gemini)

def call_model(state: State):
    system_prompt = """
    Based on the feedback analysis, provide EXACTLY 5 strategic recommendations.
    Number each recommendation from 1 to 5.
    Each recommendation must be clear and actionable.
    Format EXACTLY like this:
    1. First recommendation
    2. Second recommendation
    3. Third recommendation
    4. Fourth recommendation
    5. Fifth recommendation
    """
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Based on analysis:\n{state.get('analysis', '')}")
        ]
        
        response = llm.invoke(messages)
        
        # Ensure proper formatting
        recommendations = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 6)):
                text = line.split(".", 1)[1].strip()
                if text:
                    recommendations.append(text)
        
        if len(recommendations) != 5:
            recommendations = [
                "Implement customer feedback system",
                "Enhance product quality control",
                "Optimize performance metrics",
                "Improve user experience",
                "Develop new features based on feedback"
            ]
        
        formatted_response = "\n".join(f"{i+1}. {rec}" for i, rec in enumerate(recommendations))
        return {"messages": [HumanMessage(content=formatted_response)]}
        
    except Exception as e:
        print(f"Error in recommendations: {str(e)}")
        return {"messages": [HumanMessage(content="Error generating recommendations")]}

def categorize_recommendation(text: str) -> str:
    """Categorize recommendation based on content"""
    text = text.lower()
    if any(word in text for word in ['improve', 'enhance', 'optimize', 'upgrade']):
        return "Improvement"
    elif any(word in text for word in ['implement', 'add', 'develop', 'create']):
        return "New Feature"
    elif any(word in text for word in ['fix', 'resolve', 'address']):
        return "Fix"
    elif any(word in text for word in ['critical', 'immediate', 'urgent']):
        return "Priority"
    return "Strategic Action"

# Create graph
workflow = StateGraph(State)

# Add nodes
workflow.add_node("analyser", analyse)
workflow.add_node("major_issues", analyze_major_issues)
workflow.add_node("summarize", summarize_conversation)
workflow.add_node("call_model", call_model)

# Add edges
workflow.add_edge(START, "analyser")
workflow.add_edge("analyser", "major_issues")
workflow.add_edge("major_issues", "call_model")
workflow.add_conditional_edges("call_model", should_continue_summarise)
workflow.add_edge("summarize", END)

# Set up memory and compile graph
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Import youtube data and initialize state
from backend.youtube import get_comments

config = {
    "configurable": {
        "thread_id": "1",
        "checkpoint_ns": "feedback_analysis",
        "checkpoint_id": "youtube_comments"
    }
}

initial_state = {
    "messages": [HumanMessage(content="This is my product feedback from youtube and I want to know how to improve my product")],
    "text": get_comments(),  # Use function instead of direct df access
    "summary": "",
    "analysis": "",
    "major_topics": []
}

# Run graph with config
output = graph.invoke(initial_state, config)
# Create console for rich formatting
# console = Console()

# # Format and display Analysis
# console.print("\n[bold blue]🔍 CUSTOMER FEEDBACK ANALYSIS[/bold blue]")
# console.print("=" * 50)
# if output.get('analysis'):
#     analysis_content = output['analysis']
#     if hasattr(analysis_content, 'content'):  # If it's a Message object
#         analysis_content = analysis_content.content
#     console.print(Panel(str(analysis_content), title="Analysis", border_style="blue"))

# # Format and display Major Issues
# console.print("\n[bold red]⚠️ MAJOR ISSUES & SOLUTIONS[/bold red]")
# console.print("=" * 50)
# if output.get('major_topics'):
#     topics_content = output['major_topics']
#     if hasattr(topics_content, 'content'):  # If it's a Message object
#         topics_content = topics_content.content
#     console.print(Markdown(str(topics_content)))

# # Format and display Final Recommendations
# console.print("\n[bold green]💡 RECOMMENDATIONS[/bold green]")
# console.print("=" * 50)
# if output.get('messages'):
#     messages_content = output['messages']
#     if isinstance(messages_content, list):
#         messages_content = "\n\n".join([
#             m.content if hasattr(m, 'content') else str(m) 
#             for m in messages_content
#         ])
#     elif hasattr(messages_content, 'content'):
#         messages_content = messages_content.content
    
#     console.print(Panel(
#         str(messages_content),
#         title="Final Recommendations",
#         border_style="green"
#     ))