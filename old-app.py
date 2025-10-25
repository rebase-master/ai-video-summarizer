import traceback
import streamlit as st
import uuid  # Used to generate unique identifiers
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.media import Video
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables (including GOOGLE_API_KEY)
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("GOOGLE_API_KEY environment variable not found! Please check your .env file.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Multimodal AI Agent - Video Summarizer",
    page_icon="🤖",
    layout="wide"
)
st.title("Agno Video AI Summarizer Agent")
st.header("Powered by Gemini 2.5 Flash (Agno)")
st.warning(
    "🚨 Warning: If the error shows **403 PERMISSION DENIED** error, it means the issue is with your **API key permissions/billing** on the Google side, not the Python code. Please check your Google Cloud project's billing status.")

st.snow()

@st.cache_resource
def initialize_agent():
    # Using the stable, modern multimodal model ID.
    return Agent(
        name="Video AI summarizer",
        model=Gemini(id="gemini-2.5-flash-preview-09-2025"),
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
                        video_input = Video(filepath=video_path)

                        # Prompt generation for analysis
                        analysis_prompt = (
                            f"""
                            Analyze the uploaded video for content and context.
                            Respond to the following query using video insights and supplementary web research
                            {user_query}

                            Provide a detailed, user-friendly, and actionable response.
                            """
                        )

                        # AI agent processing - Agno handles the file upload and contents array internally.
                        response = multimodal_Agent.run(
                            analysis_prompt,
                            videos=[video_input],
                        )

                    # Display the result
                    st.subheader("Analysis Result")
                    st.markdown(response.content)

                except Exception as error:
                    error_str = str(error)
                    if "403" in error_str or "PERMISSION_DENIED" in error_str:
                        st.error("Analysis failed due to PERMISSION DENIED (403).")
                        st.markdown(
                            "**Action Required:** **STOP** and verify your **Google Cloud Billing Status** and **API Key Restrictions** immediately.")
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
