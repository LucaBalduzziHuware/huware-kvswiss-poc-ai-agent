# ==========================================
# 1. Service Account per l'AI Agent (Lettura/Query)
# ==========================================
resource "google_service_account" "agent_sa" {
  account_id   = "kv-swiss-agent-sa"
  display_name = "Karlville Swiss AI Agent Service Account"
}

# Assegnazione Ruoli IAM - Agente
resource "google_project_iam_member" "bigquery_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "discoveryengine_viewer" {
  project = var.project_id
  role    = "roles/discoveryengine.viewer"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Generazione della Chiave JSON per Sviluppo Locale (Agente)
resource "google_service_account_key" "agent_sa_key" {
  service_account_id = google_service_account.agent_sa.name
}

resource "local_file" "sa_key_file" {
  content  = base64decode(google_service_account_key.agent_sa_key.private_key)
  filename = "${path.module}/../maintenance-agent/sa-key.json"
}

# ==========================================
# 2. Service Account per la Sincronizzazione (Scrittura)
# ==========================================
resource "google_service_account" "sync_sa" {
  account_id   = "kv-swiss-sync-sa"
  display_name = "Karlville Swiss Datastore Sync Service Account"
}

# Assegnazione Ruoli IAM - Cloud Function Sync
resource "google_project_iam_member" "discoveryengine_editor" {
  project = var.project_id
  role    = "roles/discoveryengine.editor"
  member  = "serviceAccount:${google_service_account.sync_sa.email}"
}

resource "google_project_iam_member" "storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.sync_sa.email}"
}

resource "google_project_iam_member" "eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.sync_sa.email}"
}

# Permesso per invocare la Cloud Run service (necessario per GCF 2nd Gen + Eventarc)
resource "google_cloud_run_service_iam_member" "sync_sa_invoker" {
  location = var.region
  project  = var.project_id
  service  = "vertex-sync-on-upload" # Il nome del servizio coincide con quello della funzione
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.sync_sa.email}"
}

# ==========================================
# 3. Permessi Speciali per Eventarc GCS Trigger
# ==========================================

# Il Service Agent di GCS ha bisogno di pubblicare su Pub/Sub per Eventarc
data "google_storage_project_service_account" "gcs_account" {
  project = var.project_id
}

resource "google_project_iam_member" "gcs_pubsub_publishing" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

