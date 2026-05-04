# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types

from .tools import list_monitored_machines, query_production_data, search_manuals, maintenance_scheduler, who_am_i

# Ottenimento delle credenziali del Service Account
# GOOGLE_APPLICATION_CREDENTIALS DEVE essere settata nella shell prima dell'avvio.
credentials, project_id = google.auth.default()

# Debug dell'identità nel terminale all'avvio
if hasattr(credentials, "service_account_email"):
    print(f"--- AGENTE AVVIATO CON SERVICE ACCOUNT: {credentials.service_account_email} ---")
else:
    print(f"--- ATTENZIONE: AGENTE AVVIATO CON CREDENZIALI PERSONALI --- ")

# --- CONFIGURAZIONE TOOLSET ADK ---
# Disabilitiamo il Pluggable Auth interattivo (popup) tramite variabili d'ambiente
os.environ["ADK_FEATURE_PLUGGABLE_AUTH"] = "False"
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# Inizializzazione BigQuery Toolset standard con credenziali rinfrescate.
# Non specifichiamo client_id, client_secret o scopes qui, in modo che usi solo i ruoli IAM.
bq_toolset = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials),
    bigquery_tool_config=BigQueryToolConfig(
        compute_project_id=project_id,
        location="US",
        write_mode=WriteMode.ALLOWED
    )
)

root_agent = Agent(
    name="maintenance_agent",
    model=Gemini(
        model="gemini-2.5-pro",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "Sei l'assistente tecnico di Karlville Swiss specializzato in macchinari Beckhoff. "
        "Il tuo compito è minimizzare il downtime fornendo supporto diagnostico e operativo. "
        "\n\n**CONTESTO DATI (BigQuery)**:\n"
        f"- Progetto GCP: `{project_id}`\n"
        "- Dataset principale: `beckhoff_data`\n"
        "- Tabella Telemetria: `telemetry` (contiene i campi `timestamp`, `machineId`, `tag_path`, `tag_value`)\n\n"
        "**Linee guida per l'uso dei tool**:\n"
        "1. **Informazioni Utente**: Usa `who_am_i` per recuperare l'identità dell'utente corrente.\n"
        "2. **Operazioni Standard**: Usa `list_monitored_machines`, `query_production_data` o `maintenance_scheduler`.\n"
        "3. **Documentazione**: Usa `search_manuals` per i manuali tecnici.\n"
        "4. **Analisi Dati Avanzata**: Usa i tool BigQuery standard come `execute_sql` per calcoli statistici. "
        "Scrivi query SQL che puntano a `beckhoff_data.telemetry`.\n"
        "Se ricevi una foto, analizzala alla ricerca di danni visibili."
        ),

        tools=[
        list_monitored_machines, 
        query_production_data, 
        search_manuals, 
        maintenance_scheduler,
        who_am_i,
        bq_toolset,
        ],
        )


app = App(
    root_agent=root_agent,
    name="app",
)
