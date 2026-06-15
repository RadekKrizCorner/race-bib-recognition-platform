# Cloud Deployment

Phase 8 deploys the platform to Google Cloud with Terraform, GKE, and Google Cloud Storage.

## Preflight

```bash
uv run python scripts/cloud_preflight.py
```

## Terraform Plan

```bash
uv run python scripts/deploy_gcp.py \
  --project-id "$RBP_GCP_PROJECT_ID" \
  --bucket-name "$RBP_GCS_BUCKET"
```

## Terraform Apply

```bash
uv run python scripts/deploy_gcp.py \
  --project-id "$RBP_GCP_PROJECT_ID" \
  --bucket-name "$RBP_GCS_BUCKET" \
  --apply
```

## Secrets

Do not commit credentials. Configure cloud credentials with `gcloud auth application-default login`, workload identity, or CI secrets outside the repository.

## Deployment Notes

- Use `RBP_GCS_BUCKET` for artifact storage.
- Use Kubernetes Secrets for cloud-specific values.
- Run local Docker Compose and local Kubernetes validation before applying cloud infrastructure.
