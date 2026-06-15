# API

The public API stays small.

## Upload Photo

```http
POST /v1/photos
```

Response:

```json
{
  "jobId": "job-2026-000001",
  "photoId": "photo-abc123",
  "status": "RECEIVED"
}
```

## Get Job Status

```http
GET /v1/jobs/{jobId}
```

## Get Photo Results

```http
GET /v1/photos/{photoId}/results
```

## Get Job Details

```http
GET /v1/jobs/{jobId}/details
```

The details endpoint is intended for debugging and portfolio demo visibility.
