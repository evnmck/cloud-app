from dataclasses import dataclass

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