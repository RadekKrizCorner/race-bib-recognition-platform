variable "project_id" {
  description = "Google Cloud project identifier."
  type        = string
}

variable "region" {
  description = "Google Cloud region."
  type        = string
  default     = "europe-west3"
}

variable "cluster_name" {
  description = "GKE cluster name."
  type        = string
  default     = "race-bib-platform"
}

variable "artifact_bucket_name" {
  description = "GCS bucket for race bib artifacts."
  type        = string
}
