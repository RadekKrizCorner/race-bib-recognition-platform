output "cluster_name" {
  description = "Created GKE cluster name."
  value       = google_container_cluster.primary.name
}

output "artifact_bucket" {
  description = "Created artifact bucket name."
  value       = google_storage_bucket.artifacts.name
}
