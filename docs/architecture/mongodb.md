# MongoDB

MongoDB stores operational pipeline state.

## Collections

| Collection | Purpose |
|---|---|
| `processing_jobs` | Main aggregate with job state, detections, crops, OCR results, final results, and errors |
| `artifacts` | References to raw images, crops, normalized images, and debug outputs |

## Indexes

```javascript
db.processing_jobs.createIndex({ jobId: 1 }, { unique: true })
db.processing_jobs.createIndex({ photoId: 1, createdAt: -1 })
db.processing_jobs.createIndex({ raceId: 1, createdAt: -1 })
db.processing_jobs.createIndex({ status: 1, updatedAt: -1 })

db.artifacts.createIndex({ jobId: 1, stage: 1 })
db.artifacts.createIndex({ photoId: 1, type: 1 })
db.artifacts.createIndex({ uri: 1 }, { unique: true })
```

`photoId` is intentionally not unique because the same photo may be reprocessed for model comparison or retraining.
