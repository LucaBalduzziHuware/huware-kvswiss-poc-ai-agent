variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "huware-kvswiss-poc"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-west1"
}

variable "dataset_id" {
  description = "The ID of the EXISTING BigQuery dataset for telemetry"
  type        = string
  default     = "beckhoff_data"
}

variable "bucket_name" {
  description = "The name of the GCS bucket for manuals (must be globally unique)"
  type        = string
}

variable "datastore_id" {
  description = "The ID of the Vertex AI Search Datastore"
  type        = string
  default     = "kvswiss-manuals-ds"
}
