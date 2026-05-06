import os
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import VertexAiSearchTool
from google.genai import types
from ..config import DATASTORE_PATH

# Caricamento Prompt da file esterno
prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "docs_agent.md")
with open(prompt_path, "r", encoding="utf-8") as f:
    system_instruction = f.read()

# Tool Instantiation
vertex_search_tool = VertexAiSearchTool(data_store_id=DATASTORE_PATH)

# Istanza diretta dell'Agente
docs_agent = Agent(
    name="docs_agent",
    description="Esperto di manualistica tecnica Beckhoff. Usa questo agente per cercare informazioni nei manuali PDF o analizzare immagini.",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=system_instruction,
    tools=[vertex_search_tool],
)
