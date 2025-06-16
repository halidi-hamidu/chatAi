import os
import joblib
import re
import pandas as pd
from supabase import create_client, Client
from celery import shared_task

# Load your saved model and vectorizer once, when the worker starts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'logistic_phishing_model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

# Supabase credentials - use env variables or settings securely
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"\W+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

@shared_task
def fetch_and_classify_messages():
    # Fetch new messages from Supabase table 'message'
    response = supabase.table('messages').select('*').execute()
    messages = response.data

    for message in messages:
        message_text = message.get('message_text', '')
        if not message_text:
            continue

        cleaned_text = preprocess_text(message_text)
        vectorized = vectorizer.transform([cleaned_text])
        prediction = model.predict(vectorized)[0]

        is_phishing = bool(prediction)

        # Save result back to Supabase in 'results' table
        # Assume 'message_id' uniquely identifies the message
        supabase.table('results').upsert({
            'message_id': message.get('id'),
            'message_body': message_text,
            'is_phishing': is_phishing,
            'reasons': 'Predicted by logistic model'
        }).execute()
