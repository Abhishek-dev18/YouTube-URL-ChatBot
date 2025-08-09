# 🎥 YouTube Transcript Chat - Powered by Google Gemini

A **completely FREE** AI-powered application that lets you chat with any YouTube video using Google Gemini AI.

## ✨ Why Google Gemini?

- 🆓 **100% FREE** - No API costs, no billing required
- 🧠 **Advanced AI** - State-of-the-art language understanding
- ⚡ **Fast & Reliable** - Quick responses and high uptime
- 🌍 **Generous Limits** - 15 requests/minute, 1,500/day (more than enough!)
- 👥 **Perfect for Friends** - Share without worrying about costs

## 🚀 Quick Start (5 Minutes)

### 1. Get FREE Google Gemini API Key
1. Visit https://aistudio.google.com/
2. Sign in with Google account
3. Click "Get API Key" → "Create API Key"
4. Copy the key (starts with "AIza...")

### 2. Setup & Run
```bash
# Download all files, then:
chmod +x setup_gemini.sh
./setup_gemini.sh

# Add your API key to:
# - backend/.env
# - frontend/.env

# Run the app
./run_app.sh
```

### 3. Use the App
- Frontend: http://localhost:8501
- Paste YouTube URL, click "Process Video"
- Start chatting!

## 🌐 Deploy for Friends (FREE)

**Backend (Render):**
1. Push backend folder to GitHub
2. Deploy on Render.com (free tier)
3. Add `GEMINI_API_KEY` in environment variables

**Frontend (Streamlit Cloud):**
1. Push frontend folder to GitHub  
2. Deploy on share.streamlit.io (free)
3. Add API key in secrets

**Full guide:** See `DEPLOYMENT_GUIDE.md`

## 📁 Files

- `main_gemini.py` → Backend with Google Gemini
- `streamlit_app_gemini.py` → Frontend with Gemini branding
- `setup_gemini.sh` → Automated setup script
- `DEPLOYMENT_GUIDE.md` → Complete deployment guide

## 💡 Usage Tips

**Works best with:**
- Educational videos
- Tutorials
- Lectures
- Documentaries

**Try asking:**
- "What is this video about?"
- "Summarize the main points"
- "What does the speaker say about [topic]?"

## 🎯 Perfect for Students & Educators

- **Research**: Quickly understand video content
- **Study**: Get summaries and explanations
- **Language Learning**: Ask about specific parts
- **Accessibility**: Text-based interaction with video content

## 🆚 vs OpenAI Version

| Feature | OpenAI | Google Gemini |
|---------|--------|---------------|
| Cost | $5-20/month | **FREE** |
| Setup | Requires billing | Google account only |
| Quality | Excellent | **Equally excellent** |
| Limits | Restrictive on free tier | **Generous free limits** |

## 🤝 Share with Friends

Your friends can use the deployed version completely free! No API keys needed for them.

---

**Happy chatting with YouTube videos! 🎥💬**

*Powered by Google Gemini - The smart choice for free AI.*
