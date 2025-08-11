"""
Streamlit YouTube-Transcript Chat (Gemini)
Single-file demo app.

How it works (high-level):
 - User pastes YouTube URL.
 - We fetch the transcript using youtube-transcript-api.
 - We chunk the transcript, create embeddings using Gemini embeddings.
 - For each user question: embed the question, find top-k transcript chunks via cosine similarity,
   then call Gemini text generation with a prompt that restricts answers to the provided chunks only.
 - Keeps a simple chat history in Streamlit session state.

Before running:
 - pip install -r requirements.txt
 - export GEMINI_API_KEY="your_gemini_api_key"    (on Windows use set)
"""

from typing import List, Tuple
import os
import re
import math
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from google import genai
from google.genai import types
import numpy as np
import time

# --------- Config ----------
EMBEDDING_MODEL = "gemini-embedding-001"      # embeddings model
GENERATION_MODEL = "gemini-2.5-flash"         # text generation model (fast + quality)
CHUNK_CHAR_SIZE = 2000                        # chunk transcript by approx chars (tuneable)
TOP_K = 3                                     # number of top chunks to retrieve for each query
# --------------------------

# Initialize Gemini client (reads GEMINI_API_KEY from environment by default)
def get_gemini_client():
    # You may optionally pass api_key=... if you prefer explicit auth
    return genai.Client()

# Utility: extract video id from YouTube URL or raw id
def extract_video_id(url_or_id: str) -> str:
    # common YouTube URL patterns
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})",          # v=VIDEOID or /VIDEOID
        r"([0-9A-Za-z_-]{11})$"                   # plain id at end
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    # fallback: assume the user typed the id
    return url_or_id.strip()

# Get transcript text (joined) and also keep segments with timestamps
def fetch_transcript(video_id: str) -> Tuple[str, List[dict]]:
    # Returns (full_text, segments)
    # segments: list of dicts with 'text' and 'start' (seconds)
    transcript = YouTubeTranscriptApi.get_transcript(video_id)  # may raise exceptions
    # transcript is a list of {"text": "...", "start": ..., "duration": ...}
    full_text = " ".join(segment["text"].strip() for segment in transcript)
    return full_text, transcript

# Chunk text into roughly CHUNK_CHAR_SIZE sized chunks, but keep sentence boundaries if possible
def chunk_text(text: str, chunk_size: int = CHUNK_CHAR_SIZE) -> List[str]:
    # naive chunker that tries to split on sentence boundaries (period, newline)
    sentences = re.split(r'(?<=[\.\?\!]\s)|\n', text)
    chunks = []
    cur = ""
    for s in sentences:
        if len(cur) + len(s) + 1 <= chunk_size:
            cur += (" " + s) if cur else s
        else:
            if cur:
                chunks.append(cur.strip())
            # if this sentence itself is very large, split it directly
            if len(s) > chunk_size:
                for i in range(0, len(s), chunk_size):
                    chunks.append(s[i:i+chunk_size].strip())
                cur = ""
            else:
                cur = s
    if cur:
        chunks.append(cur.strip())
    return chunks

# Create embeddings for a list of texts using Gemini embeddings
def create_embeddings(client, texts: List[str], model=EMBEDDING_MODEL) -> np.ndarray:
    """
    Returns numpy array of shape (len(texts), dim)
    """
    # Gemini embed_content supports lists
    # config can specify output_dimensionality if you want smaller vector sizes
    res = client.models.embed_content(model=model, contents=texts)
    # docs: result.embeddings is a list of lists (one per input)
    embeddings = np.array([np.array(e) for e in res.embeddings])
    # normalize to unit vectors to make cosine similarity fast (dot product)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms
    return embeddings

# Cosine similarity search: returns indices of top_k most similar chunks
def semantic_search(query_emb: np.ndarray, chunk_embeddings: np.ndarray, top_k=TOP_K) -> List[int]:
    # query_emb is 1-d normalized vector, chunk_embeddings shape (n_chunks, dim) normalized
    # similarity = dot product
    sims = np.dot(chunk_embeddings, query_emb)
    top_k = min(top_k, len(sims))
    top_idx = np.argsort(-sims)[:top_k]
    return top_idx.tolist()

# Build prompt for the generator: give strict instruction to only use provided context
def build_prompt(context_chunks: List[str], user_question: str, chat_history: List[Tuple[str,str]] = None) -> str:
    """
    Returns a single string prompt to send to Gemini.
    The system instruction instructs the model to only answer from the context; be concise and mention sources (timestamps).
    We include the top retrieved chunks, prefixed with chunk numbers.
    Optionally include short chat history (previous Q/A).
    """
    system = (
        "You are a helpful assistant that answers questions strictly using ONLY the context provided below."
        " If the answer is not contained in the context, respond with: 'I don't know — the video transcript does not contain that information.'"
        " Do not hallucinate. Keep answers concise and cite the chunk numbers you used (e.g. [chunk 2])."
    )
    ctx = "\n\n".join([f"[chunk {i+1}]: {c}" for i,c in enumerate(context_chunks)])
    history_text = ""
    if chat_history:
        # include last few exchanges (safe length)
        history_text = "\n\nPrevious conversation:\n"
        for q,a in chat_history[-6:]:
            history_text += f"Q: {q}\nA: {a}\n"
    prompt = f"{system}\n\nContext:\n{ctx}\n\n{history_text}\nUser question: {user_question}\n\nAnswer:"
    return prompt

# Call Gemini to generate the answer (text) given the prompt
def generate_answer(client, prompt: str, model=GENERATION_MODEL, max_output_tokens: int = 512) -> str:
    # Using generate_content API
    # We can disable "thinking" for speed by setting thinking_budget=0 (optional)
    config = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )
    # .text is a convenience property returning candidate content
    return response.text

# --------- Streamlit UI and app logic ----------
st.set_page_config(page_title="YouTube Transcript Chat (Gemini)", layout="wide")

st.title("🎬 YouTube Transcript Chat — Ask questions about any video's transcript")
st.markdown(
    """
    Paste a YouTube video URL or ID below. The app will fetch the transcript, create semantic embeddings (Gemini),
    and let you ask questions that are answered only from the transcript.
    """
)

with st.sidebar:
    st.header("Setup / Notes")
    st.write(
        """
        • Make sure your GEMINI_API_KEY is set as an environment variable before running:
          `export GEMINI_API_KEY='your_key'` (Linux / macOS) or `set` on Windows.\n
        • This demo stores everything in memory (no DB). For production use, persist embeddings (e.g. FAISS, Pinecone, etc.).\n
        • The Gemini free tier is usable for experimentation via Google AI Studio (see docs link in the main text).
        """
    )

# Input: URL
video_input = st.text_input("YouTube URL or video id", placeholder="https://www.youtube.com/watch?v=...")

col1, col2 = st.columns([1,1])
with col1:
    load_btn = st.button("Load transcript & build embeddings")
with col2:
    clear_btn = st.button("Clear session")

if clear_btn:
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()

if "client" not in st.session_state:
    try:
        st.session_state.client = get_gemini_client()
    except Exception as e:
        st.error(f"Could not initialize Gemini client: {e}")
        st.stop()

client = st.session_state.client

if load_btn:
    if not video_input:
        st.warning("Please enter a YouTube URL or video id.")
    else:
        video_id = extract_video_id(video_input)
        st.info(f"Fetching transcript for video id: `{video_id}` ...")
        try:
            full_text, segments = fetch_transcript(video_id)
        except TranscriptsDisabled:
            st.error("Transcripts are disabled for this video.")
            st.stop()
        except NoTranscriptFound:
            st.error("No transcript found for this video (it may not have subtitles or auto-generated captions).")
            st.stop()
        except Exception as e:
            st.error(f"Failed to fetch transcript: {e}")
            st.stop()

        st.success("Transcript fetched — chunking text...")
        chunks = chunk_text(full_text, chunk_size=CHUNK_CHAR_SIZE)
        st.write(f"Created {len(chunks)} chunks (approx {CHUNK_CHAR_SIZE} chars each).")

        # Create embeddings
        with st.spinner("Generating embeddings with Gemini..."):
            try:
                chunk_embeddings = create_embeddings(client, chunks, model=EMBEDDING_MODEL)
            except Exception as e:
                st.error(f"Failed to create embeddings: {e}")
                st.stop()

        # Save to session state
        st.session_state.video_id = video_id
        st.session_state.transcript_segments = segments
        st.session_state.chunks = chunks
        st.session_state.chunk_embeddings = chunk_embeddings
        st.session_state.chat_history = []  # list of (question, answer)
        st.success("Embeddings created and stored in session. You can now ask questions below.")

# If embeddings loaded, show chat UI
if "chunks" in st.session_state:
    st.subheader("Transcript preview (first 3 chunks)")
    for i, c in enumerate(st.session_state.chunks[:3]):
        st.markdown(f"**Chunk {i+1}:** {c[:400]}{'...' if len(c)>400 else ''}")

    st.divider()
    st.subheader("Ask a question (answers come only from the transcript)")
    question = st.text_input("Your question", key="question_input")
    ask_btn = st.button("Ask")

    if ask_btn:
        if not question.strip():
            st.warning("Please type a question.")
        else:
            # Embed user question
            try:
                q_emb_res = client.models.embed_content(model=EMBEDDING_MODEL, contents=question)
                q_emb = np.array(q_emb_res.embeddings[0])
                q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-12)
            except Exception as e:
                st.error(f"Failed to embed the question: {e}")
                st.stop()

            # semantic search
            top_idxs = semantic_search(q_emb, st.session_state.chunk_embeddings, top_k=TOP_K)
            retrieved_chunks = [st.session_state.chunks[i] for i in top_idxs]

            # Build prompt
            prompt = build_prompt(retrieved_chunks, question, chat_history=st.session_state.chat_history)

            # Generate answer
            with st.spinner("Generating answer with Gemini..."):
                try:
                    answer = generate_answer(client, prompt, model=GENERATION_MODEL)
                except Exception as e:
                    st.error(f"Generation failed: {e}")
                    st.stop()

            # Save to chat history & display
            st.session_state.chat_history.append((question, answer))
            st.markdown("**Answer:**")
            st.write(answer)
            st.markdown("---")
            st.markdown("**Source chunks used (top results):**")
            for rank, idx in enumerate(top_idxs, start=1):
                st.write(f"[chunk {rank}] — preview: {st.session_state.chunks[idx][:250]}{'...' if len(st.session_state.chunks[idx])>250 else ''}")

    # show chat history
    if st.session_state.get("chat_history"):
        st.subheader("Chat history")
        for q,a in st.session_state.chat_history[::-1]:
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
            st.markdown("---")
else:
    st.info("Load a transcript to begin (enter a YouTube URL/ID on the top).")
