from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
import os

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

@app.post("/get_transcript")
async def get_transcript(request: Request):
    data = await request.json()
    video_id = get_video_id(data["url"])
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    text = " ".join([t["text"] for t in transcript])
    return {"transcript": text}

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    transcript = data["transcript"]
    question = data["question"]

    model = genai.GenerativeModel("gemini-pro")
    prompt = f"Answer the following question using only the given transcript.\n\nTranscript:\n{transcript}\n\nQuestion: {question}\nAnswer:"

    response = model.generate_content(prompt)
    return {"answer": response.text}
