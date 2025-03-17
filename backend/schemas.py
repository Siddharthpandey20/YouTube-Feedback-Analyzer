from langgraph.graph import MessagesState
from typing import List, Optional
from pydantic import BaseModel, Field

class State(MessagesState):
    text: List[str]
    summary: Optional[str] = ""
    analysis: Optional[str] = ""
    major_topics: Optional[List[str]] = []

class VideoRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "0X0Jm8QValY"
            }
        }

    def get_checkpoint_id(self) -> str:
        return f"youtube_{self.video_id}"