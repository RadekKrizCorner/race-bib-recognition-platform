"""Pipeline analytics helpers."""

from typing import Any


class PipelineAnalytics:
    """Calculate lightweight pipeline analytics for dashboards."""

    def summarize_jobs(self, jobs: list[dict[str, Any]]) -> dict[str, float | int]:
        """Summarize job counts and OCR confidence."""
        completed = sum(1 for job in jobs if job.get("status") == "COMPLETED")
        failed = sum(1 for job in jobs if job.get("status") == "FAILED")
        confidences = [
            float(result["confidence"])
            for job in jobs
            for result in job.get("finalResults", [])
            if "confidence" in result
        ]
        average = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
        return {
            "completedJobs": completed,
            "failedJobs": failed,
            "averageOcrConfidence": average,
        }
