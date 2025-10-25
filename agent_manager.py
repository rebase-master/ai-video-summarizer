from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from typing import Optional

# Keep a small factory for creating agents; useful for tests or different configs
def create_multimodal_agent(model_id: str = "gemini-2.5-flash-preview-09-2025", name: str = "Video AI summarizer", markdown: bool = True) -> Agent:
    """
    Initialize and return an Agno Agent configured for multimodal video analysis.
    """
    model = Gemini(id=model_id)
    tools = [DuckDuckGoTools()]
    return Agent(name=name, model=model, tools=tools, markdown=markdown)