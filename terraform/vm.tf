resource "google_compute_instance" "kafka_vm" {
  name         = "kafka-vm"
  machine_type = "e2-medium"
  zone         = var.zone
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }
  network_interface {
    network    = google_compute_network.vpc_network.id
    subnetwork = google_compute_subnetwork.subnet.id
  }
  shielded_instance_config {
    enable_secure_boot = true
  }
  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e

    # 1. Install Prerequisites (including Java FIRST)
    apt-get update
    apt-get install -y default-jdk software-properties-common wget gnupg git python3-pip python3-venv curl jq

    # 2. Add Confluent APT Repository
    wget -qO - https://packages.confluent.io/deb/7.2/archive.key | apt-key add -
    add-apt-repository "deb [arch=amd64] https://packages.confluent.io/deb/7.2 stable main"
    apt-get update

    # 3. Install Confluent Community Platform
    apt-get install -y confluent-community-2.13

    # 4. Start and Enable Services
    systemctl start confluent-zookeeper
    systemctl start confluent-kafka
    systemctl start confluent-schema-registry
    systemctl enable confluent-zookeeper
    systemctl enable confluent-kafka
    systemctl enable confluent-schema-registry

    # 5. Clone Data Generator Repository
    git clone https://github.com/anpag/dataflow-kf2bq-template-issue /opt/dataflow-repo

    # 6. Set up Python Environment
    cd /opt/dataflow-repo
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # 7. Register the Avro Schema
    # Wait a few seconds for Schema Registry to be fully up
    sleep 15
    jq -c '{ "schema": tostring }' /opt/dataflow-repo/PurchaseRequestEventV1.avsc | curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data @- http://localhost:8081/subjects/PurchaseRequestEventV1-value/versions
    
    EOF
  service_account {
    scopes = ["cloud-platform"]
  }
  tags = ["dataflow-test"]
  depends_on = [google_project_service.compute]
}
