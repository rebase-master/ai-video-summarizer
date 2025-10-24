import traceback
import streamlit as st
import uuid  # Used to generate unique identifiers
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.media import Video
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import glob
from openai import OpenAI

from agno.media import Image  # if available; else pass file paths
from pathlib import Path
import os

# Load environment variables (including OPENAI_API_KEY)
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    st.error("OPENAI_API_KEY environment variable not found! Please check your .env file.")
    st.stop()

client = OpenAI(api_key=API_KEY)

def extract_frames(video_path: str, out_dir: str, fps: int = 2):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    # -hide_banner reduces ffmpeg noise; adjust pattern as needed
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps={fps}",  # sample fps frames/sec
        f"{out_dir}/frame_%05d.jpg"
    ]
    subprocess.run(cmd, check=True)

def extract_audio(video_path: str, out_audio_path: str):
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", out_audio_path]
    subprocess.run(cmd, check=True)

def transcribe_audio_with_openai(audio_file_path: str) -> str:
    # This uses the common openai-python pattern for Whisper transcription:
    with open(audio_file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=f
    )
    # transcript may be dict or object; adapt:
    if isinstance(transcript, dict) and "text" in transcript:
        return transcript.text
    return str(transcript)

def get_video(video_path: str):
    frames_dir = "/tmp/my_video_frames"
    audio_file = "/tmp/my_video_audio.wav"
    extract_frames(video_path, frames_dir, fps=2)
    extract_audio(video_path, audio_file)
    transcript_text = transcribe_audio_with_openai(audio_file)

    # collect a few frames (limit to N to avoid huge costs)
    frame_paths = sorted(glob.glob(f"{frames_dir}/*.jpg"))
    st.write("Frames size: ", len(frame_paths))
    max_frames = 10
    selected_frames = frame_paths[:max_frames]

    # Convert to agno.media.Image if available, else send filepaths
    agno_images = []
    for p in selected_frames:
        try:
            agno_images.append(Image(filepath=p))  # if agno.media.Image exists
        except Exception:
            agno_images.append(p)
    st.write("agno images count: ", len(agno_images))
    return [agno_images, transcript_text]

# Page configuration
st.set_page_config(
    page_title="Multimodal AI Agent - Video Summarizer",
    page_icon="🤖",
    layout="wide"
)
st.title("Agno Video AI Summarizer Agent")

@st.cache_resource
def initialize_agent():
    # Using the stable, modern multimodal model ID.
    return Agent(
        name="Video AI summarizer",
        model=OpenAIChat(id="gpt-4o"),
        tools=[DuckDuckGoTools()],
        markdown=True
    )


## Initialize the agent
multimodal_Agent = initialize_agent()

# File uploader
video_file = st.file_uploader(
    "Upload a video file", type=['mp4', 'mov', 'avi'], help="Upload a video for AI analysis"
)

if video_file:
    video_path = None
    try:
        # 1. Determine the correct file extension
        extension = video_file.name.split('.')[-1] if '.' in video_file.name else video_file.type.split("/")[-1]

        # 2. Generate a short, unique ID (12 characters) for the File Service API limit
        unique_id = uuid.uuid4().hex[:12]
        suffix = f'_{unique_id}.{extension}'

        # 3. Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_video:
            temp_video.write(video_file.read())
            video_path = temp_video.name

        video_file_path = Path(video_path)
        st.text(f"Local temp file: {video_file_path}")
        if video_file_path.exists():
            st.text(f"File size: {video_file_path.stat().st_size} bytes")
        else:
            st.error("Temp file does not exist locally - upload failed early.")

        st.video(video_path, format="video/mp4", start_time=0)

        user_query = st.text_area(
            "What insights are you seeking from the video?",
            placeholder="Ask anything about the video content. The AI agent will analyze and gather additional information.",
            help="Provide specific questions or insights you want from the video"
        )

        if st.button(" Analyze Video", key="analyze_video_button", type="primary"):
            if not user_query:
                st.warning("Please enter a question or insight to analyze the video.")
            else:
                try:
                    with st.spinner("Processing video and gathering insights..."):

                        st.text(f"Attempting to upload local file with short ID: {Path(video_path).name}")

                        # Create the agno.media.Video object from the local path
                        agno_images, transcript_text = get_video(video_file_path)
                        analysis_prompt = (
                            f"""
                            Transcript (auto):\n{transcript_text}\n\n
                            User question: {user_query}\n\n
                            Please analyze the selected frames and transcript and answer the user question. Mention timestamps if relevant.
                            """
                        )
                        # AI agent processing - Agno handles the file upload and contents array internally.
                        response = multimodal_Agent.run(
                            analysis_prompt,
                            images=agno_images
                        )

                    # Display the result
                    st.subheader("Analysis Result")
                    st.markdown(response.content)

                except Exception as error:
                    error_str = str(error)
                    if "403" in error_str or "PERMISSION_DENIED" in error_str:
                        st.error("Analysis failed due to PERMISSION DENIED (403).")
                        st.markdown(
                            "**Action Required:** **STOP** and verify your **OpenAI Billing Status** and **API Key Restrictions** immediately.")
                    elif "contents are required" in error_str:
                        st.error("Analysis failed: The video upload failed entirely (likely a previous 403 error).")
                    else:
                        st.error(f"Analysis failed: {error}")

                    print("\n======= AGNO RUN Exception: ", error)
                    traceback.print_exc()
                finally:
                    # Clean up local temporary video file only if a path was successfully created
                    if video_path and Path(video_path).exists():
                        Path(video_path).unlink(missing_ok=True)
                        st.info("Local temporary file cleaned up.")
        else:
            st.info("Upload a video file and enter a question to begin analysis.")

    except Exception as outer_error:
        # This catches errors during the initial file handling phase
        st.error(f"An error occurred during file setup: {outer_error}")
        if video_path and Path(video_path).exists():
            Path(video_path).unlink(missing_ok=True)

    # customize text area height
    st.markdown(
        """
        <style>
            .stTextArea textarea {
                height: 100px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
