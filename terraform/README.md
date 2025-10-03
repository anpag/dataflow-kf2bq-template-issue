# Terraform Infrastructure for Dataflow Bug Reproduction

This Terraform script automates the setup of the necessary GCP infrastructure to reproduce the Dataflow concurrent connections bug.

## Deployed Resources

This Terraform configuration creates a secure, isolated environment with no external IP addresses assigned to the virtual machines, reducing the attack surface.

*   **VPC and Subnet:** A new VPC (`dataflow-test-vpc`) and subnet (`dataflow-test-subnet`) are created to host the resources. The subnet has **Private Google Access** enabled, allowing internal resources to reach Google Cloud APIs without a public IP.
*   **Cloud NAT:** A Cloud NAT is configured to allow the VM to access the internet for downloading packages (e.g., for the startup script) without requiring an external IP.
*   **Firewall Rules:** Firewall rules are created to allow internal traffic within the VPC and SSH access via IAP (Identity-Aware Proxy), which is a more secure method than exposing SSH to the internet.
*   **GCE VM:** A `e2-medium` Debian 11 VM (`kafka-vm`) is created without a public IP address. It hosts Kafka and the Confluent Schema Registry. A startup script automates the installation and configuration of these services.
*   **GCS Bucket:** A Google Cloud Storage bucket is created to be used by Dataflow for staging and temporary files.
*   **BigQuery Dataset:** A BigQuery dataset is created where the Dataflow job will write the data.
*   **IAM Service Account:** A dedicated service account (`dataflow-runner`) is created with the necessary roles (`BigQuery Data Editor`, `Storage Object Admin`, `Dataflow Worker`) for the Dataflow job to run.

## How to Use

The deployment is a two-step process. First, you create the base infrastructure, and second, you launch the Dataflow job after the data producer is running.

### Step 1: Deploy the Infrastructure

1.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

2.  **Apply the Infrastructure Configuration:**
    This step provisions the VPC, VM, and the BigQuery dataset. Provide your Project ID and the desired name for the new BigQuery dataset when prompted.
    ```bash
    terraform apply \
      -var="project_id=[YOUR_PROJECT_ID]" \
      -var="bigquery_dataset=[YOUR_BIGQUERY_DATASET]"
    ```
    Enter `yes` when prompted to confirm. This will provision the VM and configure it, which may take 5-10 minutes.

### Step 2: Run the Data Generator

The startup script automatically clones the required repository and sets up the Python environment on the `kafka-vm`.

There are two ways to start the data producer:

**Option A: Interactive SSH Session**

1.  **SSH into the VM:**
    ```bash
    gcloud compute ssh kafka-vm --zone=[YOUR_ZONE] --project=[YOUR_PROJECT_ID]
    ```
    *(The default zone is `us-central1-a`)*

2.  **Start the producer:**
    Navigate to the repository, activate the virtual environment, and start the producer script.
    ```bash
    cd /opt/dataflow-repo
    source venv/bin/activate
    python dynamic_producer.py \
        --broker localhost:9092 \
        --schema-registry http://localhost:8081 \
        --topic PurchaseRequestEventV1 \
        --eps 1
    ```
    Leave this process running.

**Option B: One-Liner SSH Command**

You can also start the producer with a single command from your local machine. This is useful for automation.

```bash
gcloud compute ssh kafka-vm --zone=[YOUR_ZONE] --project=[YOUR_PROJECT_ID] --command="cd /opt/dataflow-repo && source venv/bin/activate && python dynamic_producer.py --broker localhost:9092 --schema-registry http://localhost:8081 --topic PurchaseRequestEventV1 --eps 1"
```

### Step 3: Launch the Dataflow Job

Once the data producer is running, you can launch the Dataflow job from your local machine (not on the VM).

1.  **Apply the Dataflow Job Configuration:**
    This command uses the `-target` flag to create *only* the Dataflow job resource, without affecting the rest of the infrastructure.
    ```bash
    terraform apply \
      -var="project_id=[YOUR_PROJECT_ID]" \
      -var="bigquery_dataset=[YOUR_BIGQUERY_DATASET]" \
      -target="google_dataflow_flex_template_job.kafka_to_bigquery"
    ```

## Cleanup

To destroy all created resources (including the Dataflow job), run:
```bash
terraform destroy -var="project_id=[YOUR_PROJECT_ID]"
```
