resource "google_bigquery_dataset" "dataset" {
  project    = var.project_id
  dataset_id = var.bigquery_dataset
  location   = var.region

  # NOTE: This is set for easy cleanup in a demo environment.
  # Do not use this setting in production.
  delete_contents_on_destroy = true
}
