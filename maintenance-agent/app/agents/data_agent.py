import os
import google.auth
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types

from ..config import PROJECT_ID
from ..tools.telemetry import list_monitored_machines, query_production_data
from ..tools.maintenance import log_maintenance_event, get_active_dashboard
from ..tools.system import get_system_user_info

# Caricamento Prompt da file esterno
prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "data_agent.md")
with open(prompt_path, "r", encoding="utf-8") as f:
    system_instruction = f.read()

# Inizializzazione BigQuery Toolset standard
credentials, _ = google.auth.default()
bq_toolset = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials),
    bigquery_tool_config=BigQueryToolConfig(
        compute_project_id=PROJECT_ID, location="US", write_mode=WriteMode.ALLOWED
    ),
)

# Istanza diretta dell'Agente
data_agent = Agent(
    name="data_agent",
    description="Analista dati e operatore di sistema. Interroga telemetria, dashboard e log eventi.",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=system_instruction,
    tools=[
        list_monitored_machines,
        query_production_data,
        log_maintenance_event,
        get_active_dashboard,
        get_system_user_info,
        bq_toolset,
    ],
)
