from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoURL(BaseModel):
    url: str

class Question(BaseModel):
    question: str
    transcript: str

# Extract YouTube video ID
def extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")

@app.post("/get_transcript")
async def get_transcript(video: VideoURL):
    try:
        video_id = extract_video_id(video.url)
        transcript_data = YouTubeTranscriptApi.list_transcripts(video_id).find_transcript(['en']).fetch()
        transcript_text = " ".join([entry['text'] for entry in transcript_data])
        return {"transcript": transcript_text}
    except Exception as e:
        return {"error": str(e)}

@app.post("/ask_question")
async def ask_question(q: Question):
    try:
        prompt = f"""You are a chatbot that ONLY answers questions based on the given transcript.
If the answer is not present in the transcript, say "I couldn't find that in the transcript."

Transcript:
{q.transcript}

Question:
{q.question}
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return {"answer": response.text}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "YouTube Transcript QA API is running"}
