# Terraform Infrastructure for Dataflow Bug Reproduction

This Terraform script automates the setup of the necessary GCP infrastructure to reproduce the Dataflow concurrent connections bug.

## Deployed Resources

*   **VPC and Subnet:** A new VPC (`dataflow-test-vpc`) and subnet (`dataflow-test-subnet`) are created to host the resources.
*   **Cloud NAT:** A Cloud NAT is configured to allow the VM to access the internet for downloading packages without requiring an external IP.
*   **Firewall Rules:** Firewall rules are created to allow internal traffic within the VPC and SSH access via IAP.
*   **GCE VM:** A `e2-medium` Debian 11 VM is created to host Kafka and the Confluent Schema Registry. A startup script automates the installation and configuration of these services.

## How to Use

1.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

2.  **Review the Plan:**
    ```bash
    terraform plan -var="project_id=[YOUR_PROJECT_ID]"
    ```
    Replace `[YOUR_PROJECT_ID]` with your Google Cloud project ID.

3.  **Apply the Configuration:**
    ```bash
    terraform apply -var="project_id=[YOUR_PROJECT_ID]"
    ```
    Enter `yes` when prompted to confirm.

4.  **Get Outputs:**
    After the apply is complete, Terraform will output the internal IP of the Kafka VM, and the network and subnetwork names. You will need these for running the producer and the Dataflow job.

## Cleanup

To destroy the created resources, run:
```bash
terraform destroy -var="project_id=[YOUR_PROJECT_ID]"
```
