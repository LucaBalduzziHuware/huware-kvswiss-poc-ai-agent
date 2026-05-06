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
import google.auth.transport.requests
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext, AgentTool
from google.adk.tools import VertexAiSearchTool
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types

from .tools import (
    list_monitored_machines,
    query_production_data,
    log_maintenance_event,
    get_active_dashboard,
    get_system_user_info,
)

# Ottenimento delle credenziali del Service Account
credentials, project_id = google.auth.default()

# Define the DATASTORE_PATH for Vertex AI Search Tool
DATASTORE_ID = "kvswiss-manuals-ds-v2"
DATASTORE_PATH = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/{DATASTORE_ID}"

# Tool Instantiation: Official Vertex AI Search Tool
vertex_search_tool = VertexAiSearchTool(data_store_id=DATASTORE_PATH)

# Debug dell'identità nel terminale all'avvio
if hasattr(credentials, "service_account_email"):
    print(f"--- AGENTE AVVIATO CON SERVICE ACCOUNT: {credentials.service_account_email} ---")
else:
    print(f"--- ATTENZIONE: AGENTE AVVIATO CON CREDENZIALI PERSONALI ---")

# Disabilitiamo il Pluggable Auth interattivo (popup) tramite variabili d'ambiente
os.environ["ADK_FEATURE_PLUGGABLE_AUTH"] = "False"
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Inizializzazione BigQuery Toolset standard
bq_toolset = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials),
    bigquery_tool_config=BigQueryToolConfig(
        compute_project_id=project_id, location="US", write_mode=WriteMode.ALLOWED
    ),
)

# ---------------------------------------------------------
# 1. Agente Documentale (Specializzato in Vertex AI Search)
# ---------------------------------------------------------
docs_agent = Agent(
    name="docs_agent",
    description="Esperto di manualistica tecnica Beckhoff. Usa questo agente per cercare informazioni nei manuali PDF, trovare guide alla risoluzione degli errori, consultare documentazione tecnica o analizzare immagini di componenti.",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""Sei un esperto di manualistica tecnica per i macchinari Beckhoff di Karlville Swiss.
Usa il tool di ricerca Vertex AI per trovare informazioni nei manuali. Formula query di ricerca chiare e specifiche (preferibilmente in inglese) per ottenere i migliori risultati.

Linee guida:
1. **Grounding**: Fornisci risposte basate ESCLUSIVAMENTE sui documenti recuperati.
2. **Citazioni**: DEVI sempre citare la fonte (nome del file e pagina) per ogni informazione fornita. Se il tool non fornisce la pagina, indica almeno il documento.
3. **Analisi Immagini**: Se ricevi una foto di un componente o di un errore, analizzala attentamente e confrontala con i diagrammi tecnici presenti nei manuali per identificare discrepanze, bruciature o errori di cablaggio.
4. **Precisione**: Se non trovi l'informazione esatta, dillo chiaramente senza inventare.""",
    tools=[vertex_search_tool],
)

# ---------------------------------------------------------
# 2. Agente Dati e Telemetria (Specializzato in Function Calling)
# ---------------------------------------------------------
data_agent = Agent(
    name="data_agent",
    description="Analista dati e operatore di sistema. Usa questo agente per interrogare la telemetria, gestire la dashboard o registrare eventi di manutenzione.",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=f"""Sei l'analista dati e operatore tecnico di sistema per Karlville Swiss.
Hai accesso al dataset BigQuery `{project_id}.beckhoff_data`.

Linee guida per i tuoi tool:
1. **TEMPO E DATA**: Non cercare di indovinare MAI la data o l'ora corrente. Per ogni operazione che coinvolga scadenze, pianificazioni o consapevolezza temporale, DEVI prima usare `get_system_user_info` per ottenere l'ora esatta del server.
2. **Dashboard**: Usa `get_active_dashboard` per avere una visione d'insieme degli allarmi e dei task pendenti.
3. **Log Eventi**: Usa `log_maintenance_event` per registrare ogni cambio di stato. Classifica correttamente la categoria e la priorità.
4. **Identità**: Usa `get_system_user_info` se l'utente chiede chi è o che ore sono.

Riporta sempre fedelmente i dati tecnici e i risultati recuperati dai tuoi tool, senza inventare nulla.""",
    tools=[
        list_monitored_machines,
        query_production_data,
        log_maintenance_event,
        get_active_dashboard,
        get_system_user_info,
        bq_toolset,
    ],
)

# ---------------------------------------------------------
# 3. Agente Supervisore (Router)
# ---------------------------------------------------------
root_agent = Agent(
    name="maintenance_agent",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""Sei l'assistente tecnico e supervisore AI di Karlville Swiss. Il tuo compito è aiutare gli utenti a diagnosticare problemi e operare sui macchinari Beckhoff.

REGOLE DI COMPORTAMENTO:
1. **Briefing Iniziale (OBBLIGATORIO)**: All'inizio di ogni nuova sessione (quando l'utente ti saluta o inizia il turno), DEVI usare il tool `get_active_dashboard` tramite il `data_agent`. La tua primissima risposta deve includere un riassunto delle criticità (allarmi e task pendenti).
2. **Supporto Multimodale**: Puoi ricevere immagini (foto di componenti) per confronti tecnici.

Regole di DELEGA:
1. DELEGA al `docs_agent` per manuali, guide, specifiche tecniche o analisi di FOTO.
2. DELEGA al `data_agent` per dati real-time, dashboard, lista macchine o per registrare eventi di manutenzione.

Rispondi in modo professionale, cordiale e sintetico. Assicurati che le risposte finali includano le citazioni fornite dagli esperti.""",
    tools=[AgentTool(docs_agent), AgentTool(data_agent)],
)

app = App(
    root_agent=root_agent,
    name="app",
)
