
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
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

app = FastAPI(title="YouTube Transcript Chat - Gemini Powered", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Models
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

# Store for video sessions
video_sessions = {}

class TranscriptService:
    @staticmethod
    def extract_video_id(url: str) -> str:
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
        self.embedding_model = "models/text-embedding-004"

    def create_chunks(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.overlap_size):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)
        return chunks

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
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
        chunks = self.create_chunks(transcript)
        embeddings = self.get_embeddings(chunks)

        dimension = len(embeddings[0])
        index = faiss.IndexFlatIP(dimension)

        embeddings_array = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings_array)
        index.add(embeddings_array)

        return {
            "chunks": chunks,
            "index": index,
            "embeddings": embeddings_array
        }

    def search_relevant_context(self, query: str, embeddings_data: dict, top_k: int = 3) -> str:
        query_embedding = self.get_embeddings([query])[0]
        query_vector = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_vector)

        scores, indices = embeddings_data["index"].search(query_vector, top_k)
        relevant_chunks = [embeddings_data["chunks"][idx] for idx in indices[0]]

        return "\n\n".join(relevant_chunks)

class ChatService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_response(self, query: str, context: str, chat_history: List[dict]) -> str:
        system_prompt = f"""You are a helpful assistant that answers questions based on YouTube video transcripts. 
Use the following transcript context to answer questions accurately.

Context from transcript:
{context}

Instructions:
- Answer questions based only on the provided transcript context
- If the answer isn't in the context, say so politely
- Be conversational and helpful
- Reference specific parts of the video when relevant"""

        conversation_context = ""
        for exchange in chat_history[-3:]:
            conversation_context += f"\nUser: {exchange['user']}\nAssistant: {exchange['assistant']}"

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

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Transcript Chat - Powered by Google Gemini</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(90deg, #4285f4 0%, #34a853 50%, #fbbc04 75%, #ea4335 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            padding: 2rem;
            min-height: 600px;
        }

        .sidebar {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 15px;
        }

        .chat-area {
            display: flex;
            flex-direction: column;
        }

        .url-input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 1rem;
            margin-bottom: 1rem;
        }

        .btn {
            background: linear-gradient(45deg, #4285f4, #34a853);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 10px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .chat-messages {
            flex-grow: 1;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 1rem;
            max-height: 400px;
            overflow-y: auto;
        }

        .message {
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 10px;
        }

        .user-message {
            background: #e3f2fd;
            margin-left: 20%;
        }

        .assistant-message {
            background: #e8f5e8;
            margin-right: 20%;
        }

        .chat-input {
            display: flex;
            gap: 1rem;
        }

        .chat-input input {
            flex-grow: 1;
            padding: 1rem;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 1rem;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        .error {
            background: #ffebee;
            color: #c62828;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }

        .success {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 YouTube Transcript Chat</h1>
            <p>Powered by Google Gemini - 100% Free AI Analysis</p>
        </div>

        <div class="main-content">
            <div class="sidebar">
                <h3>📺 Process Video</h3>
                <input 
                    type="url" 
                    id="youtubeUrl" 
                    class="url-input"
                    placeholder="https://www.youtube.com/watch?v=..."
                >
                <button id="processBtn" class="btn">🚀 Process Video</button>

                <div id="videoInfo" style="display: none; margin-top: 2rem;">
                    <h4>📄 Video Processed!</h4>
                    <p id="videoId"></p>
                    <div id="transcriptPreview" style="max-height: 150px; overflow-y: auto; background: white; padding: 1rem; border-radius: 10px; margin-top: 1rem; font-size: 0.9rem;"></div>
                </div>

                <div style="margin-top: 2rem;">
                    <h4>💡 Features</h4>
                    <ul style="margin-top: 1rem; padding-left: 1rem;">
                        <li>✅ 100% Free with Google Gemini</li>
                        <li>🧠 Advanced AI reasoning</li>
                        <li>⚡ Smart context retrieval</li>
                        <li>💬 Natural conversation</li>
                        <li>🌍 Works with any video</li>
                    </ul>
                </div>
            </div>

            <div class="chat-area">
                <div id="chatMessages" class="chat-messages">
                    <div class="message assistant-message">
                        <strong>🤖 Gemini AI:</strong><br>
                        Welcome! Process a YouTube video to start chatting about its content.
                    </div>
                </div>

                <div class="chat-input">
                    <input 
                        type="text" 
                        id="chatInput" 
                        placeholder="Ask a question about the video..."
                        disabled
                    >
                    <button id="sendBtn" class="btn" disabled>Send</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentVideoId = null;

        document.getElementById('processBtn').addEventListener('click', processVideo);
        document.getElementById('sendBtn').addEventListener('click', sendMessage);
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        async function processVideo() {
            const url = document.getElementById('youtubeUrl').value;
            if (!url) {
                alert('Please enter a YouTube URL');
                return;
            }

            const processBtn = document.getElementById('processBtn');
            processBtn.disabled = true;
            processBtn.innerHTML = '⏳ Processing...';

            try {
                const response = await fetch('/api/process-video', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ youtube_url: url }),
                });

                const data = await response.json();

                if (response.ok) {
                    currentVideoId = data.video_id;
                    document.getElementById('videoId').textContent = `Video ID: ${data.video_id}`;
                    document.getElementById('transcriptPreview').textContent = data.transcript_preview;
                    document.getElementById('videoInfo').style.display = 'block';

                    // Enable chat
                    document.getElementById('chatInput').disabled = false;
                    document.getElementById('sendBtn').disabled = false;

                    addMessage('assistant', '✅ Video processed successfully! You can now ask questions about the video content.');
                } else {
                    alert('Error: ' + data.detail);
                }
            } catch (error) {
                alert('Error processing video: ' + error.message);
            } finally {
                processBtn.disabled = false;
                processBtn.innerHTML = '🚀 Process Video';
            }
        }

        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();

            if (!message || !currentVideoId) return;

            addMessage('user', message);
            input.value = '';

            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            sendBtn.innerHTML = '⏳ Thinking...';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        video_id: currentVideoId,
                        message: message
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    addMessage('assistant', data.response);
                } else {
                    addMessage('assistant', 'Sorry, I encountered an error: ' + data.detail);
                }
            } catch (error) {
                addMessage('assistant', 'Sorry, I encountered an error: ' + error.message);
            } finally {
                sendBtn.disabled = false;
                sendBtn.innerHTML = 'Send';
            }
        }

        function addMessage(type, text) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;

            const icon = type === 'user' ? '🙋 You:' : '🤖 Gemini AI:';
            messageDiv.innerHTML = `<strong>${icon}</strong><br>${text}`;

            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    </script>
</body>
</html>
    """

# API Routes
@app.post("/api/process-video", response_model=VideoResponse)
async def process_video(request: VideoRequest):
    try:
        video_id = transcript_service.extract_video_id(request.youtube_url)
        transcript = transcript_service.get_transcript(video_id)
        embeddings_data = embedding_service.create_embeddings(transcript)

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

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if request.video_id not in video_sessions:
            raise HTTPException(status_code=404, detail="Video session not found")

        session = video_sessions[request.video_id]

        relevant_context = embedding_service.search_relevant_context(
            query=request.message,
            embeddings_data=session["embeddings_data"]
        )

        response = chat_service.generate_response(
            query=request.message,
            context=relevant_context,
            chat_history=session["chat_history"]
        )

        session["chat_history"].append({
            "user": request.message,
            "assistant": response
        })

        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "ai_provider": "Google Gemini"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
