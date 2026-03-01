from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Job:
    jobId: str
    status: str
    createdAt: str
    updatedAt: str
    filename: str
    contentType: str
    bucket: str
    key: str
    processedDataLocation: Optional[str] = None  # Added by Glue
    error: Optional[str] = None                   # Added if failed