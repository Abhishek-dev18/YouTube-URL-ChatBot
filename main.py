# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai
import re
import os
import math
from typing import List

# Configure Gemini API key (set GEMINI_API_KEY in Render / environment)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# Allow frontend requests (since we serve the static file from the same app this is permissive)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend HTML
@app.get("/")
async def root():
    return FileResponse("index.html")


# Helper to extract YouTube video id
def get_video_id(url: str):
    if not url:
        return None
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


# Split text into chunks of ~max_chars characters with overlap
def chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


# Simple relevance ranking: count overlap of query words with chunk (case-insensitive)
def rank_chunks(chunks: List[str], query: str, top_k: int = 3) -> List[str]:
    q_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    scores = []
    for i, c in enumerate(chunks):
        c_words = re.findall(r"\w+", c.lower())
        # simple overlap count
        common = sum(1 for w in q_words if w in c_words)
        scores.append((common, i))
    # sort by score desc, index asc
    scores.sort(key=lambda x: (-x[0], x[1]))
    selected = [chunks[i] for score, i in scores[:top_k]]
    # If no matches at all, return first top_k chunks as fallback
    if all(s[0] == 0 for s in scores):
        return chunks[:top_k]
    return selected


@app.post("/get_transcript")
async def get_transcript(request: Request):
    payload = await request.json()
    url = payload.get("url")
    video_id = get_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or video id not found.")

    try:
        # Try to fetch transcript (English first; the library may return list/dict results)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except TranscriptsDisabled:
        raise HTTPException(status_code=404, detail="Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No transcript found for this video.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transcript: {str(e)}")

    # Join text pieces into a single string
    text = " ".join([t.get("text", "") for t in transcript_list]).strip()
    if not text:
        raise HTTPException(status_code=404, detail="Transcript is empty or could not be parsed.")

    # Pre-chunk the transcript once, so frontend can send transcript and backend can reuse
    chunks = chunk_text(text)
    return JSONResponse({"transcript": text, "chunks": chunks})


@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "").strip()
    transcript = data.get("transcript", "").strip()
    chunks = data.get("chunks")  # optional: use precomputed chunks from /get_transcript

    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is required.")

    # If chunks not provided, chunk now
    if not chunks:
        chunks = chunk_text(transcript)

    # Select top relevant chunks using simple keyword overlap
    relevant_chunks = rank_chunks(chunks, question, top_k=4)
    # Build a context that explicitly instructs the model to use ONLY the transcript content
    context = "\n\n---\n\n".join(relevant_chunks)

    system_instructions = (
        "You are an assistant that must answer questions *only* using the supplied transcript content. "
        "Do NOT invent facts or use outside knowledge. If the answer cannot be found in the transcript, "
        "say: 'I don't know — the transcript doesn't contain that information.'"
    )

    prompt = (
        f"{system_instructions}\n\n"
        f"Transcript excerpts (only use these):\n{context}\n\n"
        f"Question: {question}\n\nAnswer briefly and only from the transcript:"
    )

    try:
        model = genai.GenerativeModel("gemini-pro")
        # use model.generate_content, which returns an object with .text or similar
        # Keep this call simple — you may pass parameters (temperature, max tokens) as needed
        response = model.generate_content(prompt)
        # Some SDK responses put text at response.text or response.output[0].content[0].text depending on version
        answer_text = getattr(response, "text", None) or getattr(response, "content", None) or str(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error from Gemini API: {str(e)}")

    # Very small safety: ensure we don't return empty strings
    if not answer_text:
        answer_text = "I don't know — the transcript doesn't contain that information."

    return JSONResponse({"answer": answer_text})
