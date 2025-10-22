import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
from google.generativeai import upload_file, get_file
import google.generativeai as genai
import yt_dlp  # For downloading videos from URLs
import time
from pathlib import Path
import tempfile
from dotenv import load_dotenv
import os

# --- 1. Initialization and API Configuration ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Multimodal AI Agent - Video Summarizer",
    page_icon="🎥",
    layout="wide"
)
st.title("Phidata Video AI Summarizer Agent")
st.caption("Powered by Google Gemini")

# Initialize session state to store the video path
if "video_path" not in st.session_state:
    st.session_state.video_path = None

# --- 2. Caching the AI Agent ---
@st.cache_resource
def initialize_agent():
    """Initializes the Phidata Agent with Gemini and DuckDuckGo."""
    try:
        return Agent(
            name="Video AI summarizer",
            # Note: 'gemini-2.0-flash-exp' might not be a valid public model ID.
            # Using 'gemini-1.5-flash-latest' as a common, valid alternative.
            # Change this if you have specific access to 'gemini-2.0-flash-exp'.
            model=Gemini(id="gemini-2.0-flash-exp"),
            tools=[DuckDuckGo()],
            markdown=True,
            use_rag=False,
            ragStoreName=None
        )
    except Exception as e:
        st.error(f"Failed to initialize AI Agent. Check Model ID and API Key. Error: {e}")
        st.stop()

# Initialize the agent
multimodal_Agent = initialize_agent()

# --- 3. Helper Functions ---

def download_video(url):
    """
    Downloads a video from a URL (like YouTube) to a persistent temporary file.
    Returns the path to the downloaded file.
    """
    # Create a temp file first to get a persistent path
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video_path = temp_video.name

    # We must remove the file first, as yt-dlp wants to create it.
    os.remove(temp_video_path)

    ydl_opts = {
        'format': 'best[ext=mp4]/best', # Get the best MP4 format
        'outtmpl': temp_video_path,      # Download to this exact path
        'quiet': True,                   # Suppress console output
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        return temp_video_path  # Return the persistent path
    except Exception as e:
        st.error(f"Error downloading video: {e}")
        # Clean up the empty file if download failed
        Path(temp_video_path).unlink(missing_ok=True)
        return None

def get_result(analysis_prompt, video_path):
    """
    Analyzes the video file using the Gemini agent and displays the result.
    Cleans up the file afterward.
    Returns True on success, False on failure.
    """
    try:
        with st.spinner("Processing video and gathering insights... This may take a moment."):
            st.write("Uploading video...")
            processed_video = upload_file(video_path)

            st.write("Waiting for video processing...")
            while processed_video.state.name == "PROCESSING":
                time.sleep(2)
                processed_video = get_file(processed_video.name)

            if processed_video.state.name == "FAILED":
                st.error("Google AI failed to process the video.")
                return False

            st.write("Video processed. Analyzing with AI...")
            response = multimodal_Agent.run(
                analysis_prompt,
                files=[processed_video],
                use_rag=False,
                rag_store_name=None
            )

        # Display the result
        st.subheader("Analysis Result")
        st.markdown(response.content)
        return True

    except Exception as error:
        st.error(f"An error occurred during analysis: {error}")
        return False
    finally:
        # This cleanup will run in both success and error cases
        st.write("Cleaning up temporary files...")
        Path(video_path).unlink(missing_ok=True)
        if 'processed_video' in locals() and processed_video:
            try:
                genai.delete_file(processed_video.name)
                st.write("Server file deleted.")
            except Exception as e:
                st.warning(f"Could not delete server file: {e}")


# --- 4. Main UI Logic ---

# Use tabs for a clean input selection
tab1, tab2 = st.tabs(["Submit a Video URL", "Upload a Video File"])

with tab1:
    with st.form("url_form"):
        url = st.text_input("Enter the Video URL (e.g., YouTube)")
        submitted = st.form_submit_button("Submit & Process URL")

        if submitted and url:
            with st.spinner("Downloading video..."):
                video_path = download_video(url)
            if video_path:
                st.session_state.video_path = video_path
                st.rerun() # Rerun to show the video player
            else:
                st.error("Download failed. Please check the URL and try again.")
        elif submitted:
            st.warning("Please enter a URL.")

with tab2:
    video_file = st.file_uploader(
        "Upload a video file", type=['mp4', 'mov', 'avi'], help="Upload a video for AI analysis"
    )
    if video_file:
        st.write("Video FILE")
        with st.spinner("Saving uploaded video..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                temp_video.write(video_file.read())
                video_path = temp_video.name
            st.session_state.video_path = video_path
            st.rerun() # Rerun to show the video player
            st.write("video_path: ", video_path)

# --- 5. Video Display and Analysis Form ---

# This block runs if a video path is successfully stored in the session state
if st.session_state.video_path:
	st.write("In session")
	# Check if the file actually exists (it might have been deleted after a previous analysis)
	if Path(st.session_state.video_path).exists():
		st.subheader("Video Ready for Analysis")
		st.video(st.session_state.video_path, format="video/mp4", start_time=0)

		st.markdown("---")

		# This is the single, unified analysis form
		user_query = st.text_area(
			"What insights are you seeking from the video?",
			placeholder="e.g., Summarize the main points of this video.\nWhat is the key message?\nWho are the speakers?",
			height=100
		)

		if st.button("✨ Analyze Video", key="analyze_button", type="primary"):
			if not user_query:
				st.warning("Please enter a question to analyze the video.")
			else:
				# Call the analysis function
				analysis_success = get_result(user_query, st.session_state.video_path)
					# IMPORTANT: After analysis, the file is deleted by get_result.
					# Clear the session state path to reset the UI.
				st.session_state.video_path = None

				if analysis_success:
					st.success("Analysis complete! Upload or submit a new video to continue.")
				else:
					st.error("Analysis failed. Please check the error message above.")

				time.sleep(2) # Give user time to read success message
				st.rerun()
	else:
		st.write("Video not ready")
		# The file path was in session state, but the file is gone. Reset.
		st.session_state.video_path = None
		st.rerun()

else:
	st.info("Please submit a video URL or upload a file to begin analysis.")

# Optional: Customize text area height
st.markdown(
    """
    <style>
        .stTextArea textarea {
            min-height: 100px;
        }
    </style>
    """,
    unsafe_allow_html=True
)