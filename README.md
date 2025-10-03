# Reproducing the Dataflow Kafka to BigQuery Concurrent Connections Issue

This repository provides the necessary tools and instructions to reproduce a bug in the Dataflow "Kafka to BigQuery" template. The issue involves the template generating an excessive number of concurrent connections to the BigQuery Storage Write API, leading to quota exhaustion, even when configured for a single worker and a single write stream.

## The Issue

The core problem is the exhaustion of the "Concurrent connections per project for small regions per region" quota for the BigQuery Storage API. A Dataflow job, configured to be minimal, still creates over 1,000 concurrent connections, quickly hitting the default quota.

**Error Message:**
`com.google.cloud.bigquery.storage.v1.Exceptions$StreamWriterClosedException: FAILED_PRECONDITION: Connection is closed due to com.google.api.gax.rpc.ResourceExhaustedException.`

This repository helps demonstrate this behavior.

## Prerequisites

*   Google Cloud SDK (`gcloud`) installed and configured.
*   Python 3.7+ with `pip`.
*   A GCP project with the Dataflow and BigQuery APIs enabled.
*   A VPC and subnetwork for the Dataflow job.

## 1. Infrastructure Setup

The necessary GCP infrastructure (VPC, Subnet, Cloud NAT, GCE VM with Kafka and Schema Registry) can be deployed automatically using the provided Terraform scripts.

For detailed instructions on how to deploy the infrastructure, please refer to the [Terraform README](./terraform/README.md).

## 2. Data Generation

The provided Python scripts will generate and send Avro-formatted data to your Kafka topic.

### Setup

1.  **Clone this repository and install dependencies:**
    ```bash
    git clone https://github.com/your-repo/dataflow-kf2bq-template-issue.git
    cd dataflow-kf2bq-template-issue
    pip install -r requirements.txt
    ```

2.  **Update Kafka Broker IP:**
    In `dynamic_producer.py`, `eps_monitor.py`, and `data_generator.py`, replace the placeholder `[VM_INTERNAL_IP]` with the internal IP address of your `kafka-vm`.

### Scripts

*   `data_generator.py`: Contains the logic for generating fake data and the Avro schema.
*   `dynamic_producer.py`: The main script to produce messages to a Kafka topic. It dynamically adjusts the message rate.
*   `eps_monitor.py`: A script to monitor the Events Per Second (EPS) on a Kafka topic.

### Running the Producer

1.  **Start the producer:**
    The Terraform output will provide the internal IP of the `kafka-vm`.
    ```bash
    python dynamic_producer.py \
        --broker [KAFKA_VM_INTERNAL_IP]:9092 \
        --schema-registry http://[KAFKA_VM_INTERNAL_IP]:8081 \
        --topic PurchaseRequestEventV1 \
        --eps 1
    ```

2.  **(Optional) Monitor EPS in a separate terminal:**
    ```bash
    python eps_monitor.py \
        --broker [KAFKA_VM_INTERNAL_IP]:9092 \
        --topic PurchaseRequestEventV1 \
        --avro \
        --schema-registry http://[KAFKA_VM_INTERNAL_IP]:8081
    ```

## 3. Dataflow Job Baseline Configuration

The issue was reproduced using the official `Kafka_to_BigQuery_Flex` template. The core problem persists across various configurations, confirming it's a fundamental issue with the template's connection management rather than a specific setting.

### Key Findings:
*   **Runners:** The bug is present in both Dataflow **Runner V1** and **Runner V2**.
*   **Sharding:** The excessive connections occur regardless of whether `useAutoSharding` is set to `true` or `false`.
*   **Message Format:** The job is configured to process `AVRO_CONFLUENT_WIRE_FORMAT` messages.
*   **Schema Registry:** It utilizes a Confluent Schema Registry. This requires the `writeMode` to be set to `DYNAMIC_TABLE_NAMES`, as the template does not support Schema Registry lookups when writing to a single, predefined BigQuery table.

### Job Parameters and Metadata

Below is a summary of the key parameters from a job that reproduced the issue. Sensitive information has been replaced with placeholders.

*   **Template Version:** `goog-dataflow-provided-template-version=2025-09-23-00_rc00`
*   **SDK Version:** `Apache Beam SDK for Java 2.67.0`
*   **Job Type:** Streaming
*   **Region:** `us-central1`
*   **Worker Configuration:**
    *   `numWorkers`: 1
    *   `maxNumWorkers`: 1
    *   `autoscalingAlgorithm`: `NONE`
*   **Kafka Source:**
    *   `readBootstrapServerAndTopic`: `[KAFKA_VM_INTERNAL_IP]:9092;PurchaseRequestEventV1`
    *   `messageFormat`: `AVRO_CONFLUENT_WIRE_FORMAT`
    *   `schemaFormat`: `SCHEMA_REGISTRY`
    *   `schemaRegistryConnectionUrl`: `http://[KAFKA_VM_INTERNAL_IP]:8081`
*   **BigQuery Sink:**
    *   `outputProject`: `[YOUR_PROJECT_ID]`
    *   `outputDataset`: `[YOUR_BIGQUERY_DATASET]`
    *   `writeMode`: `DYNAMIC_TABLE_NAMES`
    *   `bqTableNamePrefix`: `kafka-`
    *   `useStorageWriteApi`: `true`
    *   `useAutoSharding`: `false` (also tested with `true`)
    *   `numStorageWriteApiStreams`: `1`
*   **Network & Service Account:**
    *   `network`: `projects/[YOUR_PROJECT_ID]/global/networks/dataflow-test-vpc`
    *   `subnetwork`: `projects/[YOUR_PROJECT_ID]/regions/us-central1/subnetworks/dataflow-test-subnet`
    *   `serviceAccount`: `dataflow-runner@[YOUR_PROJECT_ID].iam.gserviceaccount.com`

This configuration, designed to be as minimal as possible, still results in the exhaustion of the concurrent connection quota.

### Example Job Submission Command

This command will start the Dataflow job with the configuration that triggers the bug. The values for the subnetwork and service account email can be found in the Terraform output.

**Note:** This issue is reproducible with both Dataflow Runner V1 and V2, and with `useAutoSharding` set to either `true` or `false`. The command below uses the default Runner V1 and disables auto-sharding to create the most minimal configuration.

```bash
gcloud dataflow flex-template run dataflow-bug-repro \
  --template-file-gcs-location gs://dataflow-templates-us-central1/latest/flex/Kafka_to_BigQuery_Flex \
  --region us-central1 \
  --project=[YOUR_PROJECT_ID] \
  --num-workers 1 \
  --max-num-workers 1 \
  --subnetwork "https://www.googleapis.com/compute/v1/projects/[YOUR_PROJECT_ID]/regions/us-central1/subnetworks/dataflow-test-subnet" \
  --service-account-email "dataflow-runner@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
  --parameters '^~^useAutoSharding=false~readBootstrapServerAndTopic=10.0.0.4:9092;PurchaseRequestEventV1~persistKafkaKey=false~writeMode=DYNAMIC_TABLE_NAMES~storageWriteApiTriggeringFrequencySec=60~enableCommitOffsets=false~kafkaReadOffset=latest~kafkaReadAuthenticationMode=NONE~messageFormat=AVRO_CONFLUENT_WIRE_FORMAT~useBigQueryDLQ=false~stagingLocation=gs://dataflow-staging-us-central1-2648/staging~autoscalingAlgorithm=NONE~maxNumWorkers=1~serviceAccount=2613-compute@developer.gserviceaccount.com~outputProject=myproject~outputDataset=test~bqTableNamePrefix=kafka-~schemaFormat=SCHEMA_REGISTRY~schemaRegistryConnectionUrl=http://10.0.0.4:8081~schemaRegistryAuthenticationMode=NONE~numStorageWriteApiStreams=1~usePublicIps=false~experiments=use_runner_v2,enable_streaming_engine'
```

## 4. Observing the Issue

1.  **Navigate to the BigQuery Storage API Quotas:**
    In the Google Cloud Console, go to "IAM & Admin" > "Quotas" and filter for the "BigQuery Storage API".
2.  **Monitor Concurrent Connections:**
    Find the "Concurrent connections per project for small regions per region" quota for your region (e.g., `us-central1`). You will observe the usage quickly climbing to the limit of 1,000.
3.  **Check Dataflow Job Logs:**
    The Dataflow job logs will show the `RESOURCE_EXHAUSTED` errors, and the job's data freshness will increase, indicating it is falling behind.
