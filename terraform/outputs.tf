output "kafka_vm_internal_ip" {
  description = "The internal IP address of the Kafka VM."
  value       = google_compute_instance.kafka_vm.network_interface[0].network_ip
}

output "subnetwork" {
  description = "The subnetwork to use for the Dataflow job."
  value       = google_compute_subnetwork.subnet.self_link
}

output "network" {
  description = "The network to use for the Dataflow job."
  value       = google_compute_network.vpc_network.self_link
}
