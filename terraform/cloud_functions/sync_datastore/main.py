import functions_framework
import os
from google.cloud import discoveryengine_v1beta as discoveryengine

# Costanti passate via variabili d'ambiente da Terraform
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "huware-kvswiss-poc")
LOCATION = os.environ.get("LOCATION", "global")
DATA_STORE_ID = os.environ.get("DATA_STORE_ID", "kvswiss-manuals-ds-v2")

@functions_framework.cloud_event
def trigger_vertex_sync(cloud_event):
    """
    Triggerato da un evento GCS (object.finalize).
    Avvia un'importazione incrementale in Vertex AI Search.
    """
    data = cloud_event.data
    bucket = data["bucket"]
    name = data["name"]
    
    # Ignora file che non sono PDF o Testo
    allowed_extensions = (".pdf", ".txt")
    if not name.lower().endswith(allowed_extensions):
        print(f"File ignorato (estensione non supportata): {name}")
        return

    # Costruiamo l'URI del file appena caricato
    gcs_uri = f"gs://{bucket}/{name}"
    print(f"Rilevato nuovo documento ({name.split('.')[-1]}): {gcs_uri}")

    # Inizializziamo il client per Vertex AI Search (Discovery Engine)
    client = discoveryengine.DocumentServiceClient()
    
    # Definiamo il path del Branch di default del nostro Data Store
    parent = client.branch_path(
        project=PROJECT_ID, 
        location=LOCATION, 
        data_store=DATA_STORE_ID, 
        branch="default_branch"
    )

    # CONFIGURAZIONE CORRETTA PER PDF UNSTRUCTURED (Versione Corretta)
    # Nota: La configurazione del parser appartiene al DataStore, non alla richiesta di import.
    # Qui specifichiamo solo che la sorgente contiene i documenti direttamente (data_schema="content").
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri],
            data_schema="content"
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    try:
        # Avviamo l'operazione asincrona
        operation = client.import_documents(request=request)
        print(f"Importazione avviata con successo per {gcs_uri}. Operation ID: {operation.operation.name}")
    except Exception as e:
        print(f"Errore critico durante l'avvio dell'importazione per {gcs_uri}: {str(e)}")
        raise e
