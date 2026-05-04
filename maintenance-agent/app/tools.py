import os
from typing import Optional, List
from google.cloud import bigquery
from google.cloud import discoveryengine_v1beta as discoveryengine
import datetime
from google.adk.tools import ToolContext

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "huware-kvswiss-poc")
DATASET_ID = "beckhoff_data"
DATASTORE_ID = "kvswiss-manuals-ds-v2"
LOCATION = "global"

def who_am_i(context: ToolContext) -> str:
    """Restituisce l'ID dell'utente che sta interagendo con l'agente.
    Usa questo tool per sapere chi sei o chi ha avviato la sessione.
    """
    user_id = context.user_id
    session_id = context.session
    return f"Sei l'utente: '{user_id}'\nSessione corrente: '{session_id}'"


def list_monitored_machines() -> str:
    """Restituisce la lista di tutti i macchinari Karlville Swiss monitorati nel sistema.
    
    Returns:
        Lista dei Machine ID unici trovati nel database di telemetria.
    """
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"SELECT DISTINCT machineId FROM `{PROJECT_ID}.{DATASET_ID}.telemetry`"
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        machines = [row.machineId for row in results]
        
        if not machines:
            return "Nessun macchinario trovato nel database di telemetria."
            
        return "Macchinari monitorati:\n- " + "\n- ".join(machines)
    except Exception as e:
        return f"Errore durante il recupero della lista macchine: {str(e)}"

def query_production_data(machine_id: str, minutes_ago: int = 60) -> str:
    """Interroga BigQuery per analizzare lo stato recente della macchina.
    
    Args:
        machine_id: ID del macchinario (es. 'KS-DSUP-400').
        minutes_ago: Finestra temporale di analisi in minuti.
        
    Returns:
        Dati di telemetria aggregati o log di errore ADS.
    """
    client = bigquery.Client(project=PROJECT_ID)
    
    # Query per recuperare gli ultimi log di errore e telemetria
    query = f"""
        SELECT 
            timestamp, 
            tag_path as variable_name, 
            tag_value as value
        FROM `{PROJECT_ID}.{DATASET_ID}.telemetry`
        WHERE machineId = @machine_id
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @minutes_ago MINUTE)
        ORDER BY timestamp DESC
        LIMIT 100
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("machine_id", "STRING", machine_id),
            bigquery.ScalarQueryParameter("minutes_ago", "INT64", minutes_ago),
        ]
    )
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        if results.total_rows == 0:
            return f"Nessun dato trovato per la macchina {machine_id} negli ultimi {minutes_ago} minuti."
        
        data_summary = []
        for row in results:
            data_summary.append(f"[{row.timestamp}] {row.variable_name}: {row.value}")
            
        return "\n".join(data_summary)
    except Exception as e:
        return f"Errore durante l'interrogazione di BigQuery: {str(e)}"

def search_manuals(query: str) -> str:
    """Esegue una ricerca semantica sui manuali tecnici dei macchinari Karlville Swiss.
    
    Args:
        query: Stringa di ricerca (es. 'Errore ADS 1808' o 'procedura calibrazione encoder').
        
    Returns:
        Paragrafi rilevanti estratti dai manuali con citazione della fonte.
    """
    client = discoveryengine.SearchServiceClient()
    
    serving_config = client.serving_config_path(
        project=PROJECT_ID,
        location=LOCATION,
        data_store=DATASTORE_ID,
        serving_config="default_search",
    )
    
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=3,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=3,
                include_citations=True
            )
        )
    )
    
    try:
        response = client.search(request)
        
        results = []
        for result in response.results:
            doc = result.document
            derived_struct_data = doc.derived_struct_data
            snippets = derived_struct_data.get("snippets", [])
            title = derived_struct_data.get("title", "Documento senza titolo")
            link = derived_struct_data.get("link", "Link non disponibile")
            
            snippet_text = "\n".join([s.get("snippet", "") for s in snippets])
            results.append(f"--- Documento: {title} ---\n{snippet_text}\nFonte: {link}")
            
        if not results:
            return "Nessuna informazione rilevante trovata nei manuali tecnici."
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Errore durante la ricerca nei manuali: {str(e)}"

def maintenance_scheduler(machine_id: str, description: str, due_date: str) -> str:
    """Registra un nuovo task di manutenzione nel log di sistema.
    
    Args:
        machine_id: ID del macchinario.
        description: Descrizione dell'intervento da pianificare.
        due_date: Data di scadenza in formato ISO (es. '2026-05-15T10:00:00Z').
        
    Returns:
        Conferma dell'avvenuta registrazione.
    """
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.maintenance_log"
    
    # Generazione task_id univoco
    task_id = f"TASK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    rows_to_insert = [
        {
            "task_id": task_id,
            "machine_id": machine_id,
            "description": description,
            "due_date": due_date,
            "status": "PENDING"
        }
    ]
    
    try:
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return f"Task di manutenzione registrato con successo. ID: {task_id}"
        else:
            return f"Errore durante l'inserimento nel log: {errors}"
    except Exception as e:
        return f"Errore tecnico durante la schedulazione: {str(e)}"
