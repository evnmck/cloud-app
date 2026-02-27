from dataclasses import asdict
import uuid
from datetime import datetime
from backend.api.models.job import Job
from backend.api.repositories.upload_repository import create_upload_repository, get_job_repository
from backend.api.services.s3_service import generate_presigned_upload_url
from config import Config

def create_upload_service(filename: str, content_type: str):
    # Generate a job ID and S3 key
    job_id = str(uuid.uuid4())
    # Store all uploads in a single "uploads/" folder with job ID as filename prefix
    safe_filename = filename.replace("/", "_")
    upload_key = f"uploads/{job_id}_{safe_filename}"

    # Put an initial job record into DynamoDB
    now = datetime.now(datetime.timezone.utc).isoformat()

    job = Job(
        jobId=job_id,
        status="PENDING_UPLOAD",
        createdAt=now,
        updatedAt=now,
        filename=filename,
        contentType=content_type,
        bucket=Config.UPLOAD_BUCKET_NAME,
        key=upload_key,
    )

    
    create_upload_repository(asdict(job))
    upload_url = generate_presigned_upload_url(
        Config.UPLOAD_BUCKET_NAME,
        upload_key,
        content_type
    )

    return {
        "jobId": job_id,
        "uploadUrl": upload_url,
        "uploadKey": upload_key,
        "bucket": Config.UPLOAD_BUCKET_NAME,
        "status": "PENDING_UPLOAD",
    }

def get_job_service(job_id: str) -> Job | None:
    item = get_job_repository(job_id)
    if not item:
        return None
    return Job(**item)
    