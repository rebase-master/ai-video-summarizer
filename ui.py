import traceback
import streamlit as st
from pathlib import Path
from config import get_google_api_key
from agent_manager import create_multimodal_agent
from video_handler import TempVideoFile
from agno.media import Video
from typing import Optional

def configure_page():
    st.set_page_config(
        page_title="Multimodal AI Agent - Video Summarizer",
        page_icon="🤖",
        layout="wide"
    )
    st.title("Agno Video AI Summarizer Agent")
    st.header("Powered by Gemini 2.5 Flash (Agno)")
    st.warning(
        "🚨 Warning: If the error shows **403 PERMISSION DENIED**, verify your Google Cloud billing & API key permissions."
    )

# initialize agent lazily with caching to avoid repeated re-initialization
@st.cache_resource
def get_agent():
    return create_multimodal_agent()

def show_app():
    configure_page()

    api_key = get_google_api_key()
    if not api_key:
        st.error("GOOGLE_API_KEY environment variable not found! Please check your .env file.")
        st.stop()

    agent = get_agent()

    info_placeholder = st.empty()
    video_file = st.file_uploader(
        "Upload a video file", type=['mp4', 'mov', 'avi'], help="Upload a video for AI analysis"
    )

    if not video_file:
        info_placeholder.info("Upload a video file and enter a question to begin analysis.")
        return
    info_placeholder.empty()

    # show preview and info
    try:
        with TempVideoFile(video_file, original_name=video_file.name) as local_path:
            if not local_path.exists():
                st.error("Temp file does not exist locally - upload failed early.")

            # Streamlit video preview
            st.video(str(local_path), format="video/mp4", start_time=0)

            user_query = st.text_area(
                "What insights are you seeking from the video?",
                placeholder="Ask anything about the video content. The AI agent will analyze and gather additional information.",
                help="Provide specific questions or insights you want from the video"
            )

            if st.button(" Analyze Video", key="analyze_video_button", type="primary"):
                if not user_query:
                    st.warning("Please enter a question or insight to analyze the video.")
                else:
                    run_analysis(agent, local_path, user_query)
    except Exception as e:
        st.error(f"An unexpected error occurred while handling the uploaded file: {e}")
        traceback.print_exc()

def run_analysis(agent, video_path: Path, user_query: str):
    from agno.media import Video  # local import keeps top-level light
    status_placeholder = st.empty()
    try:
        with st.spinner("Processing video and gathering insights..."):
            status_placeholder.text(f"Attempting to upload local file.")

            video_input = Video(filepath=str(video_path))

            analysis_prompt = (
                f"""
                Analyze the uploaded video for content and context.
                Respond to the following query using video insights and supplementary web research
                {user_query}

                Provide a detailed, user-friendly, and actionable response.
                """
            )

            response = agent.run(analysis_prompt, videos=[video_input])

        st.subheader("Analysis Result")
        st.markdown(response.content)
        st.snow()
    except Exception as error:
        status_placeholder.empty()
        handle_agent_error(error)
    finally:
        status_placeholder.empty()

def handle_agent_error(error: Exception):
    error_str = str(error)
    if "403" in error_str or "PERMISSION_DENIED" in error_str:
        st.error("Analysis failed due to PERMISSION DENIED (403).")
        st.markdown(
            "**Action Required:** **STOP** and verify your **Google Cloud Billing Status** and **API Key Restrictions** immediately."
        )
    elif "contents are required" in error_str:
        st.error("Analysis failed: The video upload failed entirely (likely a previous 403 error).")
    else:
        st.error(f"Analysis failed: {error}")
    # still print stacktrace to console for debugging
    traceback.print_exc()