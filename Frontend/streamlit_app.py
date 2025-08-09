
import streamlit as st
import requests
import json
import time

# Configure page
st.set_page_config(
    page_title="YouTube Transcript Chat - Powered by Gemini",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4285f4 0%, #ea4335 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .gemini-badge {
        background: linear-gradient(45deg, #4285f4, #34a853, #fbbc04, #ea4335);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        margin: 0.5rem 0;
        display: inline-block;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
    }
    .user-message {
        background-color: #e8f0fe;
        margin-left: 20%;
        border-left: 4px solid #4285f4;
    }
    .assistant-message {
        background-color: #f8f9fa;
        margin-right: 20%;
        border-left: 4px solid #34a853;
    }
    .stButton > button {
        background: linear-gradient(90deg, #4285f4 0%, #34a853 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .free-tier-info {
        background: linear-gradient(135deg, #e8f5e8, #f0f8f0);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #34a853;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Backend URL - change this to your deployed backend URL
BACKEND_URL = "http://localhost:8000"  # Change to your deployed backend URL

def is_valid_youtube_url(url):
    """Validate YouTube URL"""
    import re
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
        r'(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)'
    ]
    return any(re.search(pattern, url) for pattern in youtube_patterns)

def process_video(youtube_url):
    """Process YouTube video via API"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/process-video",
            json={"youtube_url": youtube_url},
            timeout=60  # Increased timeout for Gemini processing
        )

        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            st.error(f"Error processing video: {error_detail}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Please ensure the API is running.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def send_chat_message(video_id, message):
    """Send chat message via API"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"video_id": video_id, "message": message},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()["response"]
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            st.error(f"Error sending message: {error_detail}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎥 YouTube Transcript Chat</h1>
        <p>Powered by Google Gemini AI - Free & Powerful</p>
        <div class="gemini-badge">✨ FREE TIER UNLIMITED</div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for video input
    with st.sidebar:
        st.header("📺 Video Input")

        # YouTube URL input
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL here"
        )

        # Process button
        if st.button("🚀 Process Video", type="primary"):
            if not youtube_url:
                st.warning("Please enter a YouTube URL")
            elif not is_valid_youtube_url(youtube_url):
                st.error("Please enter a valid YouTube URL")
            else:
                with st.spinner("🔄 Processing video with Google Gemini... This may take a moment."):
                    result = process_video(youtube_url)

                    if result:
                        st.session_state.video_data = result
                        st.session_state.chat_history = []
                        st.success("✅ Video processed successfully with Google Gemini!")
                        st.rerun()

        # Video info section
        if 'video_data' in st.session_state:
            st.subheader("📄 Transcript Preview")
            with st.expander("View transcript preview", expanded=False):
                st.text_area(
                    "First 500 characters:",
                    value=st.session_state.video_data['transcript_preview'],
                    height=150,
                    disabled=True
                )

            st.info(f"💡 **Video ID:** {st.session_state.video_data['video_id']}")

        # Gemini Features
        st.markdown("""
        <div class="free-tier-info">
            <h4>🌟 Google Gemini Features</h4>
            <ul>
                <li>✅ <strong>Completely FREE</strong> - No usage limits</li>
                <li>🧠 Advanced AI reasoning</li>
                <li>🌍 Multilingual support</li>
                <li>⚡ Fast response times</li>
                <li>🔒 Secure and private</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Instructions
        st.subheader("📖 How to Use")
        st.markdown("""
        1. **Paste YouTube URL** above
        2. **Click Process Video** 
        3. **Start asking questions** about the video content

        **Example questions:**
        - "What is the main topic?"
        - "Can you summarize this?"
        - "What does the speaker say about...?"
        """)

        # Cost savings info
        st.subheader("💰 Why Google Gemini?")
        st.markdown("""
        - **100% FREE**: No API costs ever
        - **Smart Context**: Only relevant parts analyzed
        - **Advanced AI**: State-of-the-art language model
        - **No Rate Limits**: Use as much as you want
        """)

    # Main chat interface
    if 'video_data' in st.session_state:
        st.header("💬 Chat with Video (Powered by Gemini)")

        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # Chat container
        chat_container = st.container()

        with chat_container:
            # Display chat history
            for i, exchange in enumerate(st.session_state.chat_history):
                # User message
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>🙋 You:</strong><br>{exchange['user']}
                </div>
                """, unsafe_allow_html=True)

                # Assistant message
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Gemini AI:</strong><br>{exchange['assistant']}
                </div>
                """, unsafe_allow_html=True)

        # Chat input
        if prompt := st.chat_input("Ask a question about the video..."):
            # Add user message to display
            st.session_state.chat_history.append({'user': prompt, 'assistant': ''})

            # Display user message immediately
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>🙋 You:</strong><br>{prompt}
            </div>
            """, unsafe_allow_html=True)

            # Get AI response
            with st.spinner("🤖 Gemini AI is thinking..."):
                response = send_chat_message(
                    st.session_state.video_data['video_id'], 
                    prompt
                )

                if response:
                    # Update chat history with response
                    st.session_state.chat_history[-1]['assistant'] = response

                    # Display assistant response
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>🤖 Gemini AI:</strong><br>{response}
                    </div>
                    """, unsafe_allow_html=True)

                    st.rerun()

    else:
        # Welcome message
        st.info("👈 Enter a YouTube URL in the sidebar to get started!")

        # Feature showcase
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            ### 🎯 Smart Analysis
            Google Gemini analyzes YouTube transcripts to answer your questions with advanced AI reasoning.
            """)

        with col2:
            st.markdown("""
            ### 💰 Completely FREE
            Uses Google Gemini's free tier with no usage limits or API costs.
            """)

        with col3:
            st.markdown("""
            ### 🚀 Easy to Use
            Simply paste a YouTube URL and start chatting about the video content.
            """)

        # Gemini advantages
        st.subheader("🌟 Why Google Gemini is Perfect for This App")

        advantages_col1, advantages_col2 = st.columns(2)

        with advantages_col1:
            st.markdown("""
            **🆓 Cost Benefits:**
            - Free tier with generous limits
            - No per-token charges
            - Perfect for personal/friend usage
            - No billing setup required
            """)

        with advantages_col2:
            st.markdown("""
            **🧠 AI Capabilities:**
            - Advanced reasoning and context understanding
            - Excellent at Q&A tasks
            - Supports long context windows
            - Multilingual support
            """)

        # Example video suggestions
        st.subheader("🎬 Try with these example videos:")

        example_videos = [
            {
                "title": "Machine Learning Explained",
                "url": "https://www.youtube.com/watch?v=9gGnTQTYNaE",
                "description": "Educational content about ML concepts"
            },
            {
                "title": "Python Programming Tutorial", 
                "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
                "description": "Learn Python programming basics"
            },
            {
                "title": "How AI Works",
                "url": "https://www.youtube.com/watch?v=mJeNghZXtMo",
                "description": "Understanding artificial intelligence"
            }
        ]

        for video in example_videos:
            with st.expander(f"📹 {video['title']}"):
                st.write(f"**Description:** {video['description']}")
                st.code(video['url'])
                if st.button(f"Try this video", key=video['url']):
                    st.session_state.example_url = video['url']
                    st.rerun()

if __name__ == "__main__":
    main()
