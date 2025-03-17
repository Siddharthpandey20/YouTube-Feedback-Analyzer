from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,HTMLResponse, Response
from backend.main import graph
from langchain_core.messages import SystemMessage, HumanMessage
from backend.youtube import get_comments, analyze_sentiment
from backend.schemas import VideoRequest
import pandas as pd
from typing import Dict, List, Any
import json
from datetime import datetime
import re
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

def parse_major_issues(text: str) -> List[dict]:
    """Parse major issues from LLM output"""
    issues = []
    current_issue = None
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Problem:'):
            if current_issue and current_issue.get('problem'):
                issues.append(current_issue)
            current_issue = {'problem': line.replace('Problem:', '').strip(), 'solution': ''}
        elif line.startswith('Solution:') and current_issue:
            current_issue['solution'] = line.replace('Solution:', '').strip()
            
    if current_issue and current_issue.get('problem'):
        issues.append(current_issue)
    
    return issues

def parse_recommendations(messages) -> List[dict]:
    """Extract recommendations from LLM output"""
    recommendations = []
    
    if not messages:
        return recommendations
        
    content = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
    
    for line in content.split('\n'):
        line = line.strip()
        if line and any(line.startswith(f"{i}.") for i in range(1, 6)):
            text = line.split(".", 1)[1].strip()
            if text:
                recommendations.append({"text": text})
    
    return recommendations

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend directory directly
app.mount("/static", StaticFiles(directory="E:/Buisness/frontend"), name="static")

# Templates from frontend directory
templates = Jinja2Templates(directory="E:/Buisness/frontend")

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_video(request: VideoRequest):
    try:
        video_id = request.video_id
        print(f"Processing video ID: {video_id}")  # Debug log
        
        config = {
            "configurable": {
                "thread_id": video_id,
                "checkpoint_ns": "feedback_analysis",
                "checkpoint_id": f"youtube_{video_id}"
            }
        }
        
        comments = get_comments(video_id=video_id)
        if not comments:
            raise HTTPException(status_code=404, detail="No comments found")

        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content="Analyze the following YouTube comments for product feedback:")],
            "text": comments,
            "summary": "",
            "analysis": "",
            "major_topics": []
        }

        try:
            output = graph.invoke(initial_state, config)  # Pass config here
        except Exception as e:
            print(f"Graph execution error: {str(e)}")
            raise HTTPException(status_code=500, detail="Error analyzing comments")
            
        # Parse major issues
        major_issues = parse_major_issues(str(output.get('major_topics', '')))
        
        # Parse recommendations
        recommendations = parse_recommendations(output.get('messages', []))
        
        # Add fallback if no recommendations found
        if not recommendations:
            recommendations = [
                {"text": "Implement customer feedback system"},
                {"text": "Enhance product quality"},
                {"text": "Optimize performance"},
                {"text": "Improve user experience"},
                {"text": "Develop new features"}
            ]

        structured_output = {
            "overview": {
                "total_comments": len(comments),
                "analyzed_at": str(datetime.now())
            },
            "major_issues": {
                "issues": major_issues
            },
            "recommendations": {
                "actions": recommendations
            }
        }
        
        print("Recommendations:", recommendations)  # Debug output
        return structured_output
        
    except Exception as e:
        print(f"Error in analyze_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiment-stats/{video_id}")
async def get_sentiment_stats(video_id: str):
    try:
        comments = get_comments(video_id=video_id)
        if not comments:
            raise HTTPException(status_code=404, detail="No comments found")
            
        df = pd.DataFrame({'text': comments})
        df['sentiment'] = df['text'].apply(analyze_sentiment)
        
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        return {
            "sentiment_distribution": sentiment_counts,
            "total_comments": len(comments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))