import os
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import AgentTool, VertexAiSearchTool
from google.genai import types

from ..config import DATASTORE_PATH
from ..tools.maintenance import log_maintenance_event

# Caricamento Prompt dell'Agente Diagnostico
prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "diagnostic_agent.md")
with open(prompt_path, "r", encoding="utf-8") as f:
    instruction = f.read()

# Definizione dell'Agente Diagnostico
diagnostic_agent = Agent(
    name="diagnostic_agent",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        VertexAiSearchTool(data_store_id=DATASTORE_PATH),
        log_maintenance_event
    ],
)
