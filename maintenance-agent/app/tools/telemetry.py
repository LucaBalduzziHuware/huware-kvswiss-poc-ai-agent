from google.cloud import bigquery
from ..config import PROJECT_ID, DATASET_ID, get_logger
from ..app_utils.ads_errors import get_ads_error_description

logger = get_logger(__name__)

def list_monitored_machines() -> str:
    """Restituisce la lista di tutti i macchinari Karlville Swiss monitorati nel sistema."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT DISTINCT machineId FROM `{PROJECT_ID}.{DATASET_ID}.telemetry`"
    
    try:
        logger.info("Fetching monitored machines list from BigQuery.")
        query_job = client.query(query)
        results = query_job.result()
        
        machines = [row.machineId for row in results]
        if not machines:
            return "Nessun macchinario trovato nel database di telemetria."
            
        return "Macchinari monitorati: " + ", ".join(machines)
    except Exception as e:
        logger.error(f"Error fetching machines list: {e}")
        return f"Errore durante il recupero della lista macchine: {str(e)}"

def query_production_data(machine_id: str, minutes_ago: int = 60) -> str:
    """Interroga BigQuery per analizzare lo stato recente della macchina."""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
        SELECT timestamp, tag_path as variable_name, tag_value as value
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
        logger.info(f"Querying telemetry for machine {machine_id} (last {minutes_ago}m).")
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        if results.total_rows == 0:
            return f"Nessun dato trovato per la macchina {machine_id} negli ultimi {minutes_ago} minuti."
        
        data_summary = []
        for row in results:
            val = row.value
            if any(term in row.variable_name.lower() for term in ["adserror", "errorcode", "status"]):
                val = f"{val} ({get_ads_error_description(val)})"
            data_summary.append(f"[{row.timestamp}] {row.variable_name}: {val}")
            
        return "\n".join(data_summary)
    except Exception as e:
        logger.error(f"Error querying production data: {e}")
        return f"Errore durante l'interrogazione di BigQuery: {str(e)}"
