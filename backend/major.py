from backend.schemas import State
from config import GEMINI_API_KEY, GEMINI_MODEL
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

gemini = GEMINI_API_KEY
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=gemini)
genai.configure(api_key=gemini)

def analyze_major_issues(state):
    all_feedback = "\n".join(state["text"])
    
    system_prompt = """
    Analyze the customer feedback and identify the top 3-4 major issues.
    Format your response EXACTLY as follows:

    Problem: [First issue description]
    Solution: [First solution]

    Problem: [Second issue description]
    Solution: [Second solution]

    Problem: [Third issue description]
    Solution: [Third solution]
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=all_feedback)
    ]
    
    try:
        response = llm.invoke(messages)
        return {"major_topics": response.content}
    except Exception as e:
        print(f"Error in major issues analysis: {e}")
        return {"major_topics": ""}
