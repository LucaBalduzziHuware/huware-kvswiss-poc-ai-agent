import os
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "huware-kvswiss-poc")

def explore_database_schema() -> str:
    """Esplora lo schema del database BigQuery per capire quali tabelle e colonne sono disponibili.
    Usa questo tool prima di scrivere una query SQL se non sei sicuro della struttura dei dati.
    
    Returns:
        Descrizione delle tabelle e dei campi disponibili.
    """
    client = bigquery.Client(project=PROJECT_ID)
    dataset_id = "beckhoff_data"
    
    try:
        tables = client.list_tables(dataset_id)
        schema_info = []
        for table in tables:
            full_table_id = f"{dataset_id}.{table.table_id}"
            t = client.get_table(full_table_id)
            columns = [f"{f.name} ({f.field_type})" for f in t.schema]
            schema_info.append(f"Tabella: {full_table_id}\nColonne: {', '.join(columns)}")
            
        return "\n\n".join(schema_info)
    except Exception as e:
        return f"Errore durante l'esplorazione dello schema: {str(e)}"

def execute_analytic_query(sql_query: str) -> str:
    """Esegue una query SQL personalizzata su BigQuery per analisi dati complesse.
    Usa questo tool per calcolare medie, massimi, aggregazioni o filtri non coperti dai tool standard.
    IMPORTANTE: La query deve essere in standard SQL e riferirsi a tabelle nel dataset 'beckhoff_data'.
    
    Args:
        sql_query: La query SQL da eseguire.
        
    Returns:
        Risultato della query in formato testuale o tabella.
    """
    client = bigquery.Client(project=PROJECT_ID)
    
    # Sicurezza: Impediamo query che non siano SELECT (sola lettura)
    if not sql_query.strip().upper().startswith("SELECT"):
        return "Errore: Sono permesse solo query di sola lettura (SELECT)."

    try:
        query_job = client.query(sql_query)
        df = query_job.to_dataframe()
        
        if df.empty:
            return "La query non ha restituito alcun risultato."
            
        return df.to_string(index=False)
    except Exception as e:
        return f"Errore durante l'esecuzione della query SQL: {str(e)}"
