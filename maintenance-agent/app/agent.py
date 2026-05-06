import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

# Importazione configurazioni e istanze dirette degli agenti esperti
from .config import get_logger
from .agents.docs_agent import docs_agent
from .agents.data_agent import data_agent

logger = get_logger(__name__)

# Caricamento Prompt del Supervisore da file esterno
prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "root_agent.md")
with open(prompt_path, "r", encoding="utf-8") as f:
    root_instruction = f.read()

# ---------------------------------------------------------
# 3. Agente Supervisore (Router)
# ---------------------------------------------------------
root_agent = Agent(
    name="maintenance_agent",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=root_instruction,
    tools=[AgentTool(docs_agent), AgentTool(data_agent)],
)

# Punto di ingresso per l'applicazione ADK
app = App(
    root_agent=root_agent,
    name="app",
)

logger.info("ADK App initialized with direct modular Supervisor/Expert instances.")
