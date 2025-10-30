from enum import Enum


class UploadStatus(str, Enum):
    """Lifecycle states for timeline ingestion."""

    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
