## About
AI Video Summarizer sample application. It uses Phidata, Google Gemini and Streamlit. 

## Setup
- Clone the repository and browse to the application folder.
- ```
    # Create the environement
        python -m venv venv
    # Activate the environment
    # On macOS/Linux:
        source venv/bin/activate
    # On Windows:
        .\venv\Scripts\activate
    ```
- Create the .env file in your project root folder and add your Google API key
  `GOOGLE_API_KEY="YOUR_SECRET_API_KEY_HERE"`
- Run `pip install -r requirements.txt` to install project dependencies.
- Run `streamlit run app.py` which opens up the app
- Upload a video and provide the query
- Wait for a few seconds for processing
- Analyzed result will be displayed

## Limitations
- Only videos less than 200 MB can be processed at this time.
