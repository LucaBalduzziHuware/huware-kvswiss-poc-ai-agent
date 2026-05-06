import datetime
from typing import Optional
from google.cloud import bigquery
from google.adk.tools import ToolContext
from ..config import PROJECT_ID, DATASET_ID, get_logger
from ..app_utils.ads_errors import get_ads_error_description

logger = get_logger(__name__)

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
    """Registra un evento nel log di manutenzione (Event-Sourcing)."""
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.maintenance_log"
    
    if not task_id:
        task_id = f"MNT-{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{machine_id[-3:]}"
    
    technician_id = context.session.user_id if context else "unknown_tech"
    
    rows_to_insert = [{
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
    }]
    
    try:
        logger.info(f"Logging maintenance event for task {task_id} (Category: {maintenance_category}).")
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return f"Evento registrato con successo. Task ID: {task_id} (Stato: {event_type})"
        else:
            logger.error(f"BigQuery insertion errors: {errors}")
            return f"Errore nell'inserimento: {errors}"
    except Exception as e:
        logger.error(f"Critical error logging maintenance event: {e}")
        return f"Errore tecnico: {str(e)}"

def get_active_dashboard() -> str:
    """Restituisce il cruscotto operativo attuale: allarmi recenti e task di manutenzione aperti."""
    client = bigquery.Client(project=PROJECT_ID)
    
    alarms_query = f"""
        SELECT machineId, tag_path, tag_value, timestamp
        FROM `{PROJECT_ID}.{DATASET_ID}.telemetry`
        WHERE (tag_path LIKE '%AdsError%' OR tag_path LIKE '%ErrorCode%' OR tag_path LIKE '%Status%')
        AND CAST(tag_value AS STRING) NOT IN ('0', '0.0', 'None', '')
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        ORDER BY timestamp DESC
        LIMIT 20
    """
    
    maintenance_query = f"""
        WITH LatestEvents AS (
            SELECT *,
            ROW_NUMBER() OVER(PARTITION BY task_id ORDER BY event_timestamp DESC) as rn
            FROM `{PROJECT_ID}.{DATASET_ID}.maintenance_log`
        )
        SELECT * FROM LatestEvents
        WHERE rn = 1 AND event_type NOT IN ('COMPLETED', 'CANCELLED')
        ORDER BY 
            CASE priority 
                WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 
            END ASC, 
            event_timestamp DESC
    """
    
    try:
        logger.info("Generating operational dashboard.")
        dashboard = ["=== operativo dashboard ==="]
        
        alarms_res = client.query(alarms_query).result()
        if alarms_res.total_rows > 0:
            dashboard.append("\n🚨 ALLARMI REAL-TIME (ULTIMA ORA):")
            for row in alarms_res:
                desc = get_ads_error_description(row.tag_value)
                dashboard.append(f"- [{row.machineId}] {row.tag_path}: {row.tag_value} ({desc})")
        else:
            dashboard.append("\n✅ Nessun allarme critico rilevato nell'ultima ora.")
            
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
        logger.error(f"Error generating dashboard: {e}")
        return f"Errore durante il recupero del dashboard: {str(e)}"
