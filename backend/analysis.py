import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.schemas import State
from config import GEMINI_API_KEY, GEMINI_MODEL

gemini = GEMINI_API_KEY
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=gemini)
genai.configure(api_key=gemini)

def analyse(state):
    system_message = f"Analyze this product comment to summarize the user's perspective, including their problems, concerns, feedback, likes, and dislikes for the owner to understand the user's experience. these are the comments from the user.{"\n".join(state["text"])}"
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content="\n".join(state["text"]))
    ]
    response = llm.invoke(messages)
    return {
        "analysis": response.content
    }