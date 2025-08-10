# 🎥 YouTube Transcript Chat

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v3.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A modern, professional Flask web application that extracts YouTube video transcripts and enables AI-powered conversations about video content using Google's Gemini AI.

## ✨ Features

- 🎯 **Smart Transcript Extraction** - Automatically extract transcripts from YouTube videos with captions
- 🤖 **AI-Powered Chat** - Chat with Google Gemini AI about video content  
- 🎨 **Professional UI** - Modern, responsive design with smooth animations
- 📱 **Mobile Friendly** - Optimized for all devices and screen sizes
- ⚡ **Real-time Processing** - Lightning-fast transcript extraction and AI responses
- 🔒 **Secure** - Production-ready security configurations
- 🚀 **Easy Deploy** - One-click deployment to Render, Heroku, or any cloud platform

## 🖥️ Live Demo

Experience the application in action: **[View Live Demo](your-app-url-here)**

## 📸 Screenshots

### Main Interface
![Main Interface](screenshots/main-interface.png)

### Chat Interface  
![Chat Interface](screenshots/chat-interface.png)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- A Google Gemini AI API key ([Get one free here](https://aistudio.google.com/app/apikey))
- Git for version control

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/youtube-transcript-chat.git
cd youtube-transcript-chat
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Activate virtual environment:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Copy the environment template
cp .env.template .env

# Edit .env file and add your API key:
# GEMINI_API_KEY=your-actual-api-key-here
# SECRET_KEY=your-secure-secret-key
```

5. **Run the application:**
```bash
python app.py
```

6. **Open your browser:**
Navigate to `http://localhost:5000`

## 🌐 Deploy to Render (Free!)

### Step 1: Prepare Your Repository
1. Fork this repository or create your own
2. Make sure all files are committed:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### Step 2: Deploy on Render
1. **Sign up** at [render.com](https://render.com) (free account)
2. **Connect your GitHub** repository
3. **Create a new Web Service** with these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:app`
   - **Environment:** Python 3
   - **Instance Type:** Free

### Step 3: Configure Environment Variables
Add these environment variables in Render dashboard:
- `GEMINI_API_KEY` = Your actual Gemini API key
- `SECRET_KEY` = A secure random string (generate one [here](https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY))
- `FLASK_ENV` = `production`

### Step 4: Deploy!
- Click **Create Web Service**
- Wait 2-5 minutes for deployment
- Your app will be live at `https://your-app-name.onrender.com`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini AI API key | ✅ Yes | None |
| `SECRET_KEY` | Flask secret key for sessions | ✅ Yes | None |
| `FLASK_ENV` | Flask environment | ❌ No | `development` |
| `PORT` | Server port | ❌ No | `5000` |
| `LOG_LEVEL` | Logging level | ❌ No | `INFO` |

### Getting Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the generated key
5. Add it to your `.env` file or Render environment variables

## 🏗️ Project Structure

```
youtube-transcript-chat/
├── app.py                    # Main Flask application
├── wsgi.py                   # WSGI entry point
├── requirements.txt          # Python dependencies  
├── .env.template            # Environment variables template
├── .gitignore               # Git ignore file
├── README.md                # This file
├── templates/               # Jinja2 templates
│   ├── base.html           # Base template
│   └── index.html          # Main page
├── static/                  # Static assets
│   ├── css/
│   │   └── style.css       # Enhanced CSS styles
│   └── js/
│       └── main.js         # JavaScript functionality
└── screenshots/             # Screenshots for README
```

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main application page |
| `POST` | `/extract_transcript` | Extract YouTube transcript |
| `POST` | `/ask_question` | Ask AI about transcript |
| `POST` | `/clear_session` | Clear current session |
| `GET` | `/health` | Health check endpoint |

## 📱 Usage

1. **Enter YouTube URL:** Paste any YouTube video URL that has captions
2. **Extract Transcript:** Click "Extract Transcript" to fetch the video's transcript  
3. **Ask Questions:** Type questions about the video content
4. **Get AI Responses:** Receive intelligent answers from Gemini AI
5. **Continue Chatting:** Ask follow-up questions for deeper insights

### Supported YouTube URL Formats
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`  
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/v/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`

## 🔍 Troubleshooting

### Common Issues

**❌ "Could not extract transcript" error**
- Video must have captions/subtitles available
- Try videos with auto-generated captions
- Some private/restricted videos may not work

**❌ "Gemini API key not configured" error**  
- Check that `GEMINI_API_KEY` is set correctly
- Verify the API key is active in Google AI Studio
- Ensure no extra spaces in the environment variable

**❌ Deployment issues**
- Verify all files are committed to GitHub
- Check Render deployment logs for specific errors
- Ensure environment variables are set in Render dashboard

### Debug Mode
Enable debug mode for local development:
```bash
export FLASK_DEBUG=True  # Linux/macOS
set FLASK_DEBUG=True     # Windows
```

## 🚀 Performance Tips

- **API Rate Limits:** Gemini AI has rate limits. Consider implementing request caching for production.
- **Large Transcripts:** Very long videos (>2 hours) may hit token limits. Consider transcript chunking.
- **Concurrent Users:** For high traffic, consider upgrading to paid Render plans or using Redis for session storage.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Test your changes before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Flask](https://flask.palletsprojects.com/)** - Web framework
- **[YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)** - Transcript extraction
- **[Google Gemini AI](https://ai.google.dev/)** - AI chat functionality  
- **[Bootstrap](https://getbootstrap.com/)** - UI components
- **[Font Awesome](https://fontawesome.com/)** - Icons
- **[Render](https://render.com/)** - Hosting platform

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/youtube-transcript-chat/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/youtube-transcript-chat/discussions)
- **Email:** your.email@example.com

---

<p align="center">
  <strong>Made with ❤️ using Flask + Gemini AI</strong>
</p>

<p align="center">
  <a href="#top">Back to top</a>
</p>
