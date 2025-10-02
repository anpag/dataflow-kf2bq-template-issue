resource "random_id" "job_suffix" {
  byte_length = 4
}

resource "google_dataflow_flex_template_job" "kafka_to_bigquery" {
  provider                      = google-beta
  project                       = var.project_id
  region                        = var.region
  name                          = "dataflow-bug-repro-${random_id.job_suffix.hex}"
  container_spec_gcs_path       = "gs://dataflow-templates-us-central1/latest/flex/Kafka_to_BigQuery_Flex"
  service_account_email         = google_service_account.dataflow_runner.email
  subnetwork                    = google_compute_subnetwork.subnet.self_link
  skip_wait_on_job_termination  = false
  on_delete                     = "cancel"

  parameters = {
    readBootstrapServerAndTopic = "${google_compute_instance.kafka_vm.network_interface[0].network_ip}:9092;PurchaseRequestEventV1"
    messageFormat               = "AVRO_CONFLUENT_WIRE_FORMAT"
    schemaRegistryConnectionUrl = "http://${google_compute_instance.kafka_vm.network_interface[0].network_ip}:8081"
    outputProject               = var.project_id
    outputDataset               = var.bigquery_dataset
    writeMode                   = "DYNAMIC_TABLE_NAMES"
    useAutoSharding             = "false"
    numStorageWriteApiStreams   = "1"
    numWorkers                  = "1"
    maxNumWorkers               = "1"
    useBigQueryDLQ              = "false"
    kafkaReadAuthenticationMode = "NONE"
    usePublicIps                = "false"
    schemaFormat                = "SCHEMA_REGISTRY"
    tempLocation                = "gs://${google_storage_bucket.dataflow_temp.name}/temp"
    stagingLocation             = "gs://${google_storage_bucket.dataflow_temp.name}/staging"
  }

  depends_on = [google_bigquery_dataset.dataset, google_project_service.dataflow]
}
