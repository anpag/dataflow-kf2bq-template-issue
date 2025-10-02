variable "project_id" {
  description = "The ID of the GCP project."
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources in."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone to deploy the VM in."
  type        = string
  default     = "us-central1-a"
}

variable "bigquery_dataset" {
  description = "The BigQuery dataset for the Dataflow job to write to."
  type        = string
}
