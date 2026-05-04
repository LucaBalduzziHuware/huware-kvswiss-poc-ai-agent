# Riferimento al Dataset BigQuery esistente per i dati di telemetria
data "google_bigquery_dataset" "telemetry_dataset" {
  dataset_id = var.dataset_id
}

# Tabella per i log di manutenzione e scadenze (da creare nel dataset esistente)
resource "google_bigquery_table" "maintenance_log" {
  dataset_id = data.google_bigquery_dataset.telemetry_dataset.dataset_id
  table_id   = "maintenance_log"
  deletion_protection = false

  schema = <<EOF
[
  {
    "name": "task_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "ID univoco del task di manutenzione"
  },
  {
    "name": "machine_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "ID del macchinario"
  },
  {
    "name": "description",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Descrizione dell'intervento"
  },
  {
    "name": "due_date",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Data di scadenza del task"
  },
  {
    "name": "status",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Stato (PENDING, COMPLETED, OVERDUE)"
  }
]
EOF
}

# GCS Bucket per i manuali tecnici (PDF)
resource "google_storage_bucket" "manuals_bucket" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# Abilitazione delle API necessarie
resource "google_project_service" "discoveryengine" {
  service = "discoveryengine.googleapis.com"
  disable_dependent_services = true
  disable_on_destroy         = false
}

# Vertex AI Search (Discovery Engine) - Data Store
resource "google_discovery_engine_data_store" "manuals_datastore" {
  provider = google-beta
  
  location     = "global"
  data_store_id = var.datastore_id
  display_name  = "KV Swiss Manuals"
  industry_vertical = "GENERIC"
  
  content_config = "CONTENT_REQUIRED"
  solution_types = ["SOLUTION_TYPE_SEARCH"]
  
  document_processing_config {
    default_parsing_config {
      layout_parsing_config {
        enable_table_annotation = true
        enable_image_annotation = true
      }
    }
    chunking_config {
      layout_based_chunking_config {
        chunk_size               = 500
        include_ancestor_headings = true
      }
    }
  }

  depends_on = [google_project_service.discoveryengine]
}
