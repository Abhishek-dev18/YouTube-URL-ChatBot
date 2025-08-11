# YouTube Transcript QA App

This project is a **YouTube Transcript Question Answering App** built with **FastAPI** and deployed on **Render**.  
It fetches transcripts from YouTube videos and allows you to ask questions about the content.

## 🚀 Features
- Fetches transcripts from YouTube videos using `youtube-transcript-api`
- Uses LLM-based embeddings for semantic search over the transcript
- Interactive question answering based on video content
- Deployable on Render via GitHub

---

## 📂 Project Structure
```
.
├── main.py                 # Main FastAPI app
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── README.md               # Project documentation
```
---

## 🛠️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/youtube-transcript-qa.git
cd youtube-transcript-qa
```

### 2️⃣ Create a virtual environment & install dependencies
```bash
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate   # For Windows

pip install -r requirements.txt
```

### 3️⃣ Add Environment Variables
Create a `.env` file in the root directory:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 4️⃣ Run Locally
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Now open [http://localhost:8000](http://localhost:8000) to access the app.

---

## 🌐 Deploying to Render

1. Push the code to a GitHub repository.
2. Go to [Render Dashboard](https://dashboard.render.com/).
3. Create a **New Web Service** and connect your GitHub repo.
4. Fill in the settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (`GOOGLE_API_KEY`) in the Render dashboard.
6. Deploy and enjoy! 🎉

---

## 📦 Requirements
The main dependencies are:
```
fastapi
uvicorn
youtube-transcript-api
google-generativeai
faiss-cpu
numpy
python-multipart
python-dotenv
rpunct
```

Install them using:
```bash
pip install -r requirements.txt
```

---

## ⚠️ Troubleshooting

### `YouTubeTranscriptApi` error
Make sure you are importing it correctly:
```python
from youtube_transcript_api import YouTubeTranscriptApi

transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
```

### CORS errors
If you're accessing the API from a frontend, make sure to enable CORS in `main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📜 License
This project is licensed under the MIT License.
