# Runbooks

## Reprocess a Job

1. Locate the job in `processing_jobs`.
2. Verify the raw artifact URI exists.
3. Reset the target stage state if needed.
4. Publish the stage input event again or run `scripts/reprocess_job.py`.
5. Confirm the job reaches `COMPLETED` or records a failure with metadata.

Create a `photo.ingested` reprocessing event from a raw artifact:

```bash
uv run python scripts/reprocess_job.py job-1 \
  --photo-id photo-1 \
  --source-image-uri file://artifacts/jobs/job-1/raw/photo-1.jpg
```

## Inspect a DLQ

1. Read messages from the relevant `.dlq` topic.
2. Inspect `jobId`, `photoId`, `stage`, `errorCode`, `retryCount`, and `originalEventId`.
3. Confirm whether the source artifact exists.
4. Reprocess only after the root cause is corrected.

## Roll Out a Model Adapter

1. Register the new model version in documentation.
2. Run the local deterministic test suite.
3. Run a benchmark dataset through the adapter.
4. Compare OCR confidence and failed job count.
5. Deploy behind the adapter interface.

Evaluate labeled predictions:

```bash
uv run python scripts/evaluate_model.py evaluation-cases.json
```
