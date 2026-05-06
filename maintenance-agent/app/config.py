import os
import logging
import google.auth

# Ottenimento delle credenziali del Service Account
credentials, project_id = google.auth.default()

# --- Configurazione Google Cloud ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", project_id)
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
DATASET_ID = "beckhoff_data"
DATASTORE_ID = "kvswiss-manuals-ds-v2"

# --- Vertex AI Search Path ---
DATASTORE_PATH = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATASTORE_ID}"

# --- Setup Logging Professionale ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def get_logger(name):
    return logging.getLogger(name)

# Esposizione delle variabili d'ambiente necessarie per ADK e SDK
os.environ["ADK_FEATURE_PLUGGABLE_AUTH"] = "False"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
