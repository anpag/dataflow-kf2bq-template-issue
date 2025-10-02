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
  metadata_startup_script = <<-EOF
    #!/bin/bash
    # Install Java
    sudo apt-get update
    sudo apt-get install -y default-jdk
    # Download and Extract Kafka
    wget https://archive.apache.org/dist/kafka/3.2.0/kafka_2.13-3.2.0.tgz
    tar -xzf kafka_2.13-3.2.0.tgz
    cd kafka_2.13-3.2.0
    # Start ZooKeeper and Kafka
    ./bin/zookeeper-server-start.sh config/zookeeper.properties &
    ./bin/kafka-server-start.sh config/server.properties &
    cd ..
    # Download and Start Confluent Schema Registry
    wget https://packages.confluent.io/archive/7.2/confluent-community-7.2.1.tar.gz
    tar -xzf confluent-community-7.2.1.tar.gz
    cd confluent-community-7.2.1
    # Update schema registry properties to listen on all interfaces
    sed -i 's/#listeners=http:\/\/0.0.0.0:8081/listeners=http:\/\/0.0.0.0:8081/g' etc/schema-registry/schema-registry.properties
    # Update kafka store properties
    sed -i 's/kafkastore.bootstrap.servers=PLAINTEXT:\/\/localhost:9092/kafkastore.bootstrap.servers=PLAINTEXT:\/\/127.0.0.1:9092/g' etc/schema-registry/schema-registry.properties
    ./bin/schema-registry-start etc/schema-registry/schema-registry.properties &
    EOF
  service_account {
    scopes = ["cloud-platform"]
  }
  tags = ["dataflow-test"]
}
