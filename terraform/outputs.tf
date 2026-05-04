output "bigquery_dataset_id" {
  value = data.google_bigquery_dataset.telemetry_dataset.dataset_id
}

output "gcs_bucket_name" {
  value = google_storage_bucket.manuals_bucket.name
}

output "datastore_id" {
  value = google_discovery_engine_data_store.manuals_datastore.data_store_id
}

output "agent_service_account" {
  value = google_service_account.agent_sa.email
}
