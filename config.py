from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

def get_google_api_key() -> Optional[str]:
    return os.getenv("GOOGLE_API_KEY")