from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd

# Initialize tokenizer and model
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
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

# Example DataFrame
comments = [
    {"author": "User1", "published_at": "2025-03-13T10:00:00Z", "updated_at": "2025-03-13T10:00:00Z", "like_count": 10, "text": "This is a test 😃"},
    {"author": "User2", "published_at": "2025-03-13T10:00:00Z", "updated_at": "2025-03-13T10:00:00Z", "like_count": 5, "text": "यह एक परीक्षण है"},
    {"author": "User3", "published_at": "2025-03-13T10:00:00Z", "updated_at": "2025-03-13T10:00:00Z", "like_count": 8, "text": "Nice video, bhai!"}
]
df = pd.DataFrame(comments)

# Apply the function to the 'text' column
df['sentiment'] = df['text'].apply(analyze_sentiment)
print(df)
