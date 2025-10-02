resource "google_storage_bucket" "dataflow_temp" {
  project      = var.project_id
  name         = "dataflow-temp-${var.project_id}"
  location     = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}
