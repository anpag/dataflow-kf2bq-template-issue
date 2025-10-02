# Terraform Infrastructure for Dataflow Bug Reproduction

This Terraform script automates the setup of the necessary GCP infrastructure to reproduce the Dataflow concurrent connections bug.

## Deployed Resources

*   **VPC and Subnet:** A new VPC (`dataflow-test-vpc`) and subnet (`dataflow-test-subnet`) are created to host the resources.
*   **Cloud NAT:** A Cloud NAT is configured to allow the VM to access the internet for downloading packages without requiring an external IP.
*   **Firewall Rules:** Firewall rules are created to allow internal traffic within the VPC and SSH access via IAP.
*   **GCE VM:** A `e2-medium` Debian 11 VM is created to host Kafka and the Confluent Schema Registry. A startup script automates the installation and configuration of these services.

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

The startup script automatically clones the required repository and sets up the Python environment.

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
        --eps 1000
    ```
    Leave this process running.

### Step 3: Launch the Dataflow Job

Once the data producer is running, you can launch the Dataflow job from your local machine (not on the VM).

1.  **Apply the Dataflow Job Configuration:**
    This command uses the `-target` flag to create *only* the Dataflow job resource, without affecting the rest of the infrastructure. You will need to provide your Dataflow service account and the target BigQuery dataset.
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
