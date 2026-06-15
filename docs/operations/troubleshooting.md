# Troubleshooting

## Upload Succeeds but Results Are Missing

- Check the job status endpoint.
- Confirm `photo.ingested` was published.
- Confirm raw artifact URI exists.
- Check worker logs for stage failures.

## OCR Confidence Is Low

- Inspect normalized crop artifacts.
- Add low-confidence samples to the dataset manifest.
- Compare model versions before replacing the adapter.

## Kafka Consumer Lag Is High

- Check partition count.
- Check consumer group membership.
- Scale worker replicas only when partitions are available.

## Cloud Deployment Fails

- Confirm Terraform variables are set.
- Confirm Google Cloud credentials are provided outside the repository.
- Confirm GKE and GCS APIs are enabled.
