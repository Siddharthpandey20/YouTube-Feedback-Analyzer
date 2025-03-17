import re,torch
import googleapiclient.discovery
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
from backend.schemas import State
import json
import os
from config import YOUTUBE_API_KEY, SENTIMENT_MODEL

def remove_non_ascii(text):
    return text.encode('ascii', 'ignore').decode('ascii')

model_name = SENTIMENT_MODEL
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def preprocess_text(text):
    return tokenizer(text, return_tensors="pt", padding=True, truncation=True)

def analyze_sentiment(text):
    inputs = preprocess_text(text)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_id = torch.argmax(logits, dim=1).item()
    label = model.config.id2label[predicted_class_id]
    return label

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = YOUTUBE_API_KEY

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY)

def get_comments(video_id="0X0Jm8QValY", cache_file="youtube_comments_cache.json"):
    """Get comments with caching to avoid repeated API calls"""
    
    # Check if cached data exists and is less than 1 hour old
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
            if cached_data.get('video_id') == video_id:
                return cached_data.get('comments', [])

    # If no cache or different video, fetch from API
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            text = remove_non_ascii(comment['textDisplay'])
            if text:  # Only add non-empty comments
                comments.append(text)

        # Cache the results
        cache_data = {
            'video_id': video_id,
            'comments': comments
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

        return comments
    except Exception as e:
        print(f"Error fetching comments: {e}")
        # Return cached data if available, empty list otherwise
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f).get('comments', [])
        return []

# Replace direct DataFrame usage with function
text_data = get_comments()
state = State(text=text_data)

# Optionally save to CSV
df = pd.DataFrame(text_data, columns=['text'])
df['sentiment'] = df['text'].apply(analyze_sentiment)
df.to_csv('youtube_comments.csv', index=False)

# Export the function and data
__all__ = ['state', 'text_data', 'get_comments']