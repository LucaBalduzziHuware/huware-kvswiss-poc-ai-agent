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
    """Restituisce le informazioni tecniche del sistema sull'identità dell'utente e la data/ora corrente del server.
    Usa questo tool quando l'utente chiede chi è o per sapere esattamente che giorno e ora è oggi (fondamentale per le scadenze).
    """
    try:
        user_id = context.session.user_id
        session_id = context.session.id
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"Dati tecnici di sistema:\n- User ID: '{user_id}'\n- Session ID: '{session_id}'\n- Data/Ora Corrente Server: '{now}'"
    except Exception as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Dati tecnici di sistema (limitati):\n- Data/Ora Corrente Server: '{now}'"


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

def log_maintenance_event(
    machine_id: str, 
    maintenance_category: str,
    event_type: str,
    priority: str,
    description: str,
    task_id: Optional[str] = None,
    trigger_reference: Optional[str] = None,
    due_date: Optional[str] = None,
    context: ToolContext = None
) -> str:
    """Registra un evento nel log di manutenzione (Event-Sourcing).
    
    Args:
        machine_id: ID del macchinario.
        maintenance_category: ORDINARY, EXTRAORDINARY, BREAKDOWN, OBSERVATION.
        event_type: SCHEDULED, STARTED, ESCALATED, COMPLETED, CANCELLED.
        priority: LOW, MEDIUM, HIGH, CRITICAL.
        description: Dettaglio dell'attività o del problema rilevato.
        task_id: ID univoco del task (se omesso per un nuovo task, viene generato).
        trigger_reference: Riferimento opzionale (es. codice errore ADS).
        due_date: Data di scadenza opzionale (ISO format).
        context: Contesto per recuperare l'identità del tecnico.
    """
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.maintenance_log"
    
    # Se è un nuovo task (SCHEDULED), generiamo un ID
    if not task_id:
        task_id = f"MNT-{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{machine_id[-3:]}"
    
    technician_id = context.session.user_id if context else "unknown_tech"
    
    rows_to_insert = [
        {
            "event_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "task_id": task_id,
            "machine_id": machine_id,
            "maintenance_category": maintenance_category.upper(),
            "event_type": event_type.upper(),
            "priority": priority.upper(),
            "description": description,
            "trigger_reference": trigger_reference,
            "due_date": due_date,
            "technician_id": technician_id
        }
    ]
    
    try:
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return f"Evento registrato con successo. Task ID: {task_id} (Stato: {event_type})"
        else:
            return f"Errore nell'inserimento: {errors}"
    except Exception as e:
        return f"Errore tecnico: {str(e)}"

def get_active_dashboard() -> str:
    """Restituisce il cruscotto operativo attuale: allarmi recenti e task di manutenzione aperti.
    Usa questo tool all'inizio di ogni sessione per fare il briefing al tecnico.
    """
    client = bigquery.Client(project=PROJECT_ID)
    
    # 1. Query per gli allarmi real-time (ultima ora)
    alarms_query = f"""
        SELECT machineId, tag_path, tag_value, timestamp
        FROM `{PROJECT_ID}.{DATASET_ID}.telemetry`
        WHERE (tag_path LIKE '%AdsError%' OR tag_path LIKE '%ErrorCode%' OR tag_path LIKE '%Status%')
        AND CAST(tag_value AS STRING) NOT IN ('0', '0.0', 'None', '')
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        ORDER BY timestamp DESC
        LIMIT 20
    """
    
    # 2. Query per i task aperti (Window Function per l'ultimo stato)
    maintenance_query = f"""
        WITH LatestEvents AS (
            SELECT *,
            ROW_NUMBER() OVER(PARTITION BY task_id ORDER BY event_timestamp DESC) as rn
            FROM `{PROJECT_ID}.{DATASET_ID}.maintenance_log`
        )
        SELECT * FROM LatestEvents
        WHERE rn = 1 
        AND event_type NOT IN ('COMPLETED', 'CANCELLED')
        ORDER BY 
            CASE priority 
                WHEN 'CRITICAL' THEN 1 
                WHEN 'HIGH' THEN 2 
                WHEN 'MEDIUM' THEN 3 
                WHEN 'LOW' THEN 4 
            END ASC, 
            event_timestamp DESC
    """
    
    try:
        dashboard = ["=== operativo dashboard ==="]
        
        # Esecuzione query allarmi
        alarms_res = client.query(alarms_query).result()
        if alarms_res.total_rows > 0:
            dashboard.append("\n🚨 ALLARMI REAL-TIME (ULTIMA ORA):")
            for row in alarms_res:
                desc = get_ads_error_description(row.tag_value)
                dashboard.append(f"- [{row.machineId}] {row.tag_path}: {row.tag_value} ({desc})")
        else:
            dashboard.append("\n✅ Nessun allarme critico rilevato nell'ultima ora.")
            
        # Esecuzione query manutenzioni
        maint_res = client.query(maintenance_query).result()
        if maint_res.total_rows > 0:
            dashboard.append("\n🔧 TASK APERTI E OSSERVAZIONI:")
            for row in maint_res:
                due = f" (Scadenza: {row.due_date.strftime('%d/%m')})" if row.due_date else ""
                dashboard.append(f"- [{row.priority}] {row.maintenance_category}: {row.description} {due} [ID: {row.task_id}]")
        else:
            dashboard.append("\n📋 Nessun task di manutenzione o osservazione pendente.")
            
        return "\n".join(dashboard)
    except Exception as e:
        return f"Errore durante il recupero del dashboard: {str(e)}"
