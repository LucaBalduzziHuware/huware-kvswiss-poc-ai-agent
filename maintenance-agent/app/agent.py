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
from google.genai import types

from .tools import list_monitored_machines, query_production_data, search_manuals, maintenance_scheduler
from .bq_tools import explore_database_schema, execute_analytic_query

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

root_agent = Agent(
    name="maintenance_agent",
    model=Gemini(
        model="gemini-2.5-pro",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "Sei l'assistente tecnico di Karlville Swiss specializzato in macchinari Beckhoff. "
        "Il tuo compito è minimizzare il downtime fornendo supporto diagnostico e operativo. "
        "Segui queste linee guida per l'uso dei tool:\n"
        "1. **Operazioni Standard**: Usa `list_monitored_machines`, `query_production_data` o `maintenance_scheduler` "
        "per flussi di lavoro comuni come il controllo rapido della telemetria o la pianificazione di interventi.\n"
        "2. **Documentazione**: Usa `search_manuals` (Vertex AI Search) per consultare i manuali tecnici PDF.\n"
        "3. **Analisi Dati Avanzata**: Se l'utente pone domande analitiche complesse (es. medie, aggregati, analisi storiche), "
        "usa prima `explore_database_schema` per capire la struttura dei dati e poi `execute_analytic_query` per scrivere la query SQL necessaria.\n"
        "Se ricevi una foto, analizzala alla ricerca di danni visibili o anomalie."
    ),
    tools=[
        list_monitored_machines, 
        query_production_data, 
        search_manuals, 
        maintenance_scheduler,
        explore_database_schema,
        execute_analytic_query
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
