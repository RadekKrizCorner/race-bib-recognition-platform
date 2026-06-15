# Local Kubernetes

Use kind or minikube to validate the Kubernetes deployment shape before cloud deployment.

## Validate Manifests

```bash
uv run python scripts/validate_local_kubernetes.py
```

## Apply to Current Cluster

```bash
uv run python scripts/validate_local_kubernetes.py --apply
```

## Expected Resources

- `race-bib-platform` namespace
- API deployment and service
- Worker deployments
- Kafka and MongoDB local deployments
- Grafana local deployment
- ConfigMap and Secret template
