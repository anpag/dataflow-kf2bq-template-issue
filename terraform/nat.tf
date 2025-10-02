resource "google_compute_router" "router" {
  name    = "dataflow-test-router"
  network = google_compute_network.vpc_network.id
  region  = google_compute_subnetwork.subnet.region
  depends_on = [google_project_service.compute]
}

resource "google_compute_router_nat" "nat" {
  name                               = "dataflow-test-nat"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  nat_ip_allocate_option             = "AUTO_ONLY"
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}
