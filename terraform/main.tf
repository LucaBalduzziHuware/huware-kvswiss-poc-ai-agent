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

# ==========================================
# Cloud Function per Sincronizzazione Automatica
# ==========================================

# Bucket per il codice sorgente delle Cloud Functions
resource "google_storage_bucket" "cf_source_bucket" {
  name          = "${var.project_id}-cf-source"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

# Zip del codice sorgente
data "archive_file" "sync_function_source" {
  type        = "zip"
  source_dir  = "${path.module}/cloud_functions/sync_datastore"
  output_path = "${path.module}/sync_datastore.zip"
}

# Upload dello zip su GCS
resource "google_storage_bucket_object" "sync_function_zip" {
  name   = "sync_datastore-${data.archive_file.sync_function_source.output_md5}.zip"
  bucket = google_storage_bucket.cf_source_bucket.name
  source = data.archive_file.sync_function_source.output_path
}

# La Cloud Function (2nd Gen)
resource "google_cloudfunctions2_function" "vertex_sync_function" {
  name        = "vertex-sync-on-upload"
  location    = var.region
  project     = var.project_id
  description = "Triggera l'importazione incrementale in Vertex AI Search al caricamento di un PDF"

  build_config {
    runtime     = "python311"
    entry_point = "trigger_vertex_sync"
    source {
      storage_source {
        bucket = google_storage_bucket.cf_source_bucket.name
        object = google_storage_bucket_object.sync_function_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 5
    available_memory   = "256M"
    timeout_seconds    = 60
    service_account_email = google_service_account.sync_sa.email
    
    environment_variables = {
      GOOGLE_CLOUD_PROJECT = var.project_id
      LOCATION             = "global"
      DATA_STORE_ID        = google_discovery_engine_data_store.manuals_datastore.data_store_id
    }
  }

  event_trigger {
    event_type            = "google.cloud.storage.object.v1.finalized"
    trigger_region        = var.region # Deve coincidere con la regione del bucket
    service_account_email = google_service_account.sync_sa.email
    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.manuals_bucket.name
    }
    retry_policy = "RETRY_POLICY_RETRY"
  }

  depends_on = [
    google_project_iam_member.discoveryengine_editor,
    google_project_iam_member.storage_viewer,
    google_project_iam_member.eventarc_receiver
  ]
}

