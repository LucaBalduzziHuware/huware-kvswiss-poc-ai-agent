import os
from typing import Optional, List
from google.cloud import bigquery
import datetime
from google.adk.tools import ToolContext
from .app_utils.ads_errors import get_ads_error_description

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "huware-kvswiss-poc")
DATASET_ID = "beckhoff_data"
DATASTORE_ID = "kvswiss-manuals-ds-v2"
LOCATION = "global"

def get_system_user_info(context: ToolContext) -> str:
    """Restituisce le informazioni tecniche del sistema sull'identità dell'utente (user_id e session_id).
    Usa questo tool quando l'utente chiede informazioni sulla sua identità tecnica o come è registrato nel sistema.
    """
    try:
        # Modo standard ADK per accedere ai dati di sessione via Context
        user_id = context.session.user_id
        session_id = context.session.id
        
        print(f"--- DEBUG: Esecuzione get_system_user_info per user {user_id} ---")
        return f"Dati tecnici di sistema:\n- User ID: '{user_id}'\n- Session ID: '{session_id}'"
    except Exception as e:
        print(f"--- DEBUG ERROR: {e} ---")
        # Fallback nel caso la struttura del contesto sia diversa in versioni future
        return f"Dati tecnici di sistema (fallback):\n- User ID: '{getattr(context, 'user_id', 'N/A')}'\n- Session ID: '{getattr(context, 'session', 'N/A')}'"


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
            
        return "Macchinari monitorati: " + ", ".join(machines)
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
            val = row.value
            # Se la variabile sembra un errore ADS, proviamo a mapparla
            if any(term in row.variable_name.lower() for term in ["adserror", "errorcode", "status"]):
                val = f"{val} ({get_ads_error_description(val)})"
            
            data_summary.append(f"[{row.timestamp}] {row.variable_name}: {val}")
            
        return "\n".join(data_summary)
    except Exception as e:
        return f"Errore durante l'interrogazione di BigQuery: {str(e)}"

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
