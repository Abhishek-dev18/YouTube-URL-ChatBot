
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import re
import numpy as np
import faiss
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="YouTube Transcript Chat API - Gemini Powered", version="1.0.0")

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class VideoRequest(BaseModel):
    youtube_url: str

class VideoResponse(BaseModel):
    video_id: str
    transcript_preview: str
    message: str

class ChatRequest(BaseModel):
    video_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Store for video sessions (use Redis or database in production)
video_sessions = {}

class TranscriptService:
    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError("Invalid YouTube URL")

    @staticmethod
    def get_transcript(video_id: str) -> str:
        """Get transcript for a YouTube video"""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([item['text'] for item in transcript_list])
            return transcript_text
        except Exception as e:
            raise Exception(f"Failed to get transcript: {str(e)}")

class EmbeddingService:
    def __init__(self):
        self.chunk_size = 500
        self.overlap_size = 50
        # Use Gemini's embedding model
        self.embedding_model = "models/text-embedding-004"

    def create_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size - self.overlap_size):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)

        return chunks

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using Gemini API"""
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        return embeddings

    def create_embeddings(self, transcript: str) -> dict:
        """Create embeddings for transcript chunks"""
        chunks = self.create_chunks(transcript)
        embeddings = self.get_embeddings(chunks)

        # Create FAISS index for similarity search
        dimension = len(embeddings[0])
        index = faiss.IndexFlatIP(dimension)

        # Normalize and add embeddings
        embeddings_array = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings_array)
        index.add(embeddings_array)

        return {
            "chunks": chunks,
            "index": index,
            "embeddings": embeddings_array
        }

    def search_relevant_context(self, query: str, embeddings_data: dict, top_k: int = 3) -> str:
        """Search for most relevant chunks"""
        query_embedding = self.get_embeddings([query])[0]
        query_vector = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_vector)

        scores, indices = embeddings_data["index"].search(query_vector, top_k)
        relevant_chunks = [embeddings_data["chunks"][idx] for idx in indices[0]]

        return "\n\n".join(relevant_chunks)

class ChatService:
    def __init__(self):
        # Use Gemini 2.0 Flash for cost-effectiveness
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_response(self, query: str, context: str, chat_history: List[dict]) -> str:
        """Generate response using Gemini with context"""

        # Build conversation prompt
        system_prompt = f"""You are a helpful assistant that answers questions based on YouTube video transcripts. 
Use the following transcript context to answer questions accurately.

Context from transcript:
{context}

Instructions:
- Answer questions based only on the provided transcript context
- If the answer isn't in the context, say so politely
- Be conversational and helpful
- Reference specific parts of the video when relevant"""

        # Add recent chat history for context
        conversation_context = ""
        for exchange in chat_history[-3:]:  # Last 3 exchanges to save on token usage
            conversation_context += f"\nUser: {exchange['user']}\nAssistant: {exchange['assistant']}"

        # Create full prompt
        full_prompt = f"{system_prompt}\n\nPrevious conversation:{conversation_context}\n\nCurrent question: {query}"

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )
            return response.text
        except Exception as e:
            return f"I apologize, but I encountered an error processing your question: {str(e)}"

# Initialize services
transcript_service = TranscriptService()
embedding_service = EmbeddingService()
chat_service = ChatService()

@app.post("/process-video", response_model=VideoResponse)
async def process_video(request: VideoRequest):
    """Process YouTube video and create embeddings"""
    try:
        video_id = transcript_service.extract_video_id(request.youtube_url)
        transcript = transcript_service.get_transcript(video_id)
        embeddings_data = embedding_service.create_embeddings(transcript)

        # Store session data
        video_sessions[video_id] = {
            "transcript": transcript,
            "embeddings_data": embeddings_data,
            "chat_history": []
        }

        return VideoResponse(
            video_id=video_id,
            transcript_preview=transcript[:500] + "..." if len(transcript) > 500 else transcript,
            message="Video processed successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages with context retrieval"""
    try:
        if request.video_id not in video_sessions:
            raise HTTPException(status_code=404, detail="Video session not found")

        session = video_sessions[request.video_id]

        # Get relevant context from transcript using similarity search
        relevant_context = embedding_service.search_relevant_context(
            query=request.message,
            embeddings_data=session["embeddings_data"]
        )

        # Generate response with context
        response = chat_service.generate_response(
            query=request.message,
            context=relevant_context,
            chat_history=session["chat_history"]
        )

        # Update chat history
        session["chat_history"].append({
            "user": request.message,
            "assistant": response
        })

        return ChatResponse(response=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "YouTube Transcript Chat API with Google Gemini is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "ai_provider": "Google Gemini"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
