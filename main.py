import os
import faiss
import numpy as np
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()
app = FastAPI()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Store transcript embeddings per video
video_store = {}

# Simple HTML frontend
html_template = Template("""
<!DOCTYPE html>
<html>
<head>
<title>YouTube Chat with Gemini</title>
<style>
    body { font-family: sans-serif; margin: 40px; background-color: #f4f4f4; }
    textarea, input { width: 100%; padding: 10px; margin: 10px 0; }
    button { padding: 10px 20px; }
</style>
</head>
<body>
    <h1>📺 YouTube Chatbot (Gemini)</h1>
    <form method="post" action="/process">
        <input type="text" name="url" placeholder="Enter YouTube URL" required>
        <button type="submit">Process Video</button>
    </form>
    {% if video_id %}
    <hr>
    <form method="post" action="/ask">
        <input type="hidden" name="video_id" value="{{ video_id }}">
        <textarea name="question" placeholder="Ask something about the video..." required></textarea>
        <button type="submit">Ask</button>
    </form>
    {% endif %}
    {% if answer %}
    <h3>Answer:</h3>
    <p>{{ answer }}</p>
    {% endif %}
</body>
</html>
""")

def get_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([x["text"] for x in transcript])

def embed_texts(texts):
    model = genai.embed_content(model="models/embedding-001", content=texts)
    return np.array(model["embedding"], dtype="float32")

@app.get("/", response_class=HTMLResponse)
async def home():
    return html_template.render(video_id=None, answer=None)

@app.post("/process", response_class=HTMLResponse)
async def process(url: str = Form(...)):
    if "v=" in url:
        video_id = url.split("v=")[-1].split("&")[0]
    else:
        video_id = url.split("/")[-1]
    transcript = get_transcript(video_id)

    # Create embeddings and FAISS index
    embedding = embed_texts(transcript[:5000])
    index = faiss.IndexFlatL2(len(embedding))
    index.add(np.array([embedding]))
    video_store[video_id] = (index, transcript)

    return html_template.render(video_id=video_id, answer=None)

@app.post("/ask", response_class=HTMLResponse)
async def ask(video_id: str = Form(...), question: str = Form(...)):
    index, transcript = video_store[video_id]
    prompt = f"Based on this transcript: {transcript}\nAnswer: {question}"
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content(prompt)
    return html_template.render(video_id=video_id, answer=resp.text)
