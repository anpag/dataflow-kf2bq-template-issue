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

These steps guide you through setting up a VM to host Kafka and the Schema Registry.

### Create a GCP VM

1.  **Create a VM instance:**
    ```bash
    gcloud compute instances create kafka-vm \
        --project=[YOUR_PROJECT_ID] \
        --zone=[YOUR_ZONE] \
        --machine-type=e2-medium \
        --image-family=debian-11 \
        --image-project=debian-cloud \
        --boot-disk-size=20GB \
        --subnetwork=[YOUR_SUBNETWORK] \
        --scopes=https://www.googleapis.com/auth/cloud-platform
    ```

2.  **SSH into the VM:**
    ```bash
    gcloud compute ssh kafka-vm --project=[YOUR_PROJECT_ID] --zone=[YOUR_ZONE]
    ```

### Install and Configure Kafka and Schema Registry

1.  **Install Java:**
    ```bash
    sudo apt-get update
    sudo apt-get install -y default-jdk
    ```

2.  **Download and Extract Kafka:**
    ```bash
    wget https://archive.apache.org/dist/kafka/3.2.0/kafka_2.13-3.2.0.tgz
    tar -xzf kafka_2.13-3.2.0.tgz
    cd kafka_2.13-3.2.0
    ```

3.  **Start ZooKeeper and Kafka:**
    ```bash
    ./bin/zookeeper-server-start.sh config/zookeeper.properties &
    ./bin/kafka-server-start.sh config/server.properties &
    ```

4.  **Download and Start Confluent Schema Registry:**
    ```bash
    wget https://packages.confluent.io/archive/7.2/confluent-community-7.2.1.tar.gz
    tar -xzf confluent-community-7.2.1.tar.gz
    cd confluent-community-7.2.1
    ./bin/schema-registry-start etc/schema-registry/schema-registry.properties &
    ```
    Your Kafka broker will be running at `[VM_INTERNAL_IP]:9092` and Schema Registry at `http://[VM_INTERNAL_IP]:8081`.

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
    ```bash
    python dynamic_producer.py \
        --broker [VM_INTERNAL_IP]:9092 \
        --schema-registry http://[VM_INTERNAL_IP]:8081 \
        --topic PurchaseRequestEventV1 \
        --eps 1000
    ```

2.  **(Optional) Monitor EPS in a separate terminal:**
    ```bash
    python eps_monitor.py \
        --broker [VM_INTERNAL_IP]:9092 \
        --topic PurchaseRequestEventV1 \
        --avro \
        --schema-registry http://[VM_INTERNAL_IP]:8081
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
    *   `readBootstrapServerAndTopic`: `[VM_INTERNAL_IP]:9092;PurchaseRequestEventV1`
    *   `messageFormat`: `AVRO_CONFLUENT_WIRE_FORMAT`
    *   `schemaFormat`: `SCHEMA_REGISTRY`
    *   `schemaRegistryConnectionUrl`: `http://[VM_INTERNAL_IP]:8081`
*   **BigQuery Sink:**
    *   `outputProject`: `[YOUR_PROJECT_ID]`
    *   `outputDataset`: `[YOUR_BIGQUERY_DATASET]`
    *   `writeMode`: `DYNAMIC_TABLE_NAMES`
    *   `bqTableNamePrefix`: `kafka-`
    *   `useStorageWriteApi`: `true`
    *   `useAutoSharding`: `false` (also tested with `true`)
    *   `numStorageWriteApiStreams`: `1`
*   **Network & Service Account:**
    *   `network`: `[YOUR_VPC_NETWORK]`
    *   `subnetwork`: `[YOUR_SUBNETWORK]`
    *   `serviceAccount`: `[YOUR_SERVICE_ACCOUNT_EMAIL]`

This configuration, designed to be as minimal as possible, still results in the exhaustion of the concurrent connection quota.

### Example Job Submission Command

This command will start the Dataflow job with the configuration that triggers the bug.

```bash
gcloud dataflow flex-template run dataflow-bug-repro \
  --template-file-gcs-location gs://dataflow-templates-us-central1/latest/flex/Kafka_to_BigQuery_Flex \
  --region us-central1 \
  --project=[YOUR_PROJECT_ID] \
  --num-workers 1 \
  --max-num-workers 1 \
  --subnetwork [YOUR_SUBNETWORK] \
  --service-account-email [YOUR_SERVICE_ACCOUNT_EMAIL] \
  --parameters \
    "readBootstrapServerAndTopic=[VM_INTERNAL_IP]:9092;PurchaseRequestEventV1,messageFormat=AVRO_CONFLUENT_WIRE_FORMAT,schemaRegistryConnectionUrl=http://[VM_INTERNAL_IP]:8081,outputProject=[YOUR_PROJECT_ID],outputDataset=[YOUR_BIGQUERY_DATASET],writeMode=DYNAMIC_TABLE_NAMES,useAutoSharding=false,numStorageWriteApiStreams=1"
```

## 4. Observing the Issue

1.  **Navigate to the BigQuery Storage API Quotas:**
    In the Google Cloud Console, go to "IAM & Admin" > "Quotas" and filter for the "BigQuery Storage API".
2.  **Monitor Concurrent Connections:**
    Find the "Concurrent connections per project for small regions per region" quota for your region (e.g., `us-central1`). You will observe the usage quickly climbing to the limit of 1,000.
3.  **Check Dataflow Job Logs:**
    The Dataflow job logs will show the `RESOURCE_EXHAUSTED` errors, and the job's data freshness will increase, indicating it is falling behind.
