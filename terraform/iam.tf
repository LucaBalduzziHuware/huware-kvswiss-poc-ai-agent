# Creazione del Service Account per l'AI Agent
resource "google_service_account" "agent_sa" {
  account_id   = "kv-swiss-agent-sa"
  display_name = "Karlville Swiss AI Agent Service Account"
}

# Assegnazione Ruoli IAM
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

# Permesso per il logging (necessario per test_agent_feedback)
resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Permessi sul RAG (Vertex AI Search)
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

# Generazione della Chiave JSON
resource "google_service_account_key" "agent_sa_key" {
  service_account_id = google_service_account.agent_sa.name
}

# Salvataggio della chiave in locale per il Playground
resource "local_file" "sa_key_file" {
  content  = base64decode(google_service_account_key.agent_sa_key.private_key)
  filename = "${path.module}/../maintenance-agent/sa-key.json"
}
