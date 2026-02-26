
import json
import base64
import uuid
from datetime import datetime, timezone
from config import Config
from utils import response as _response, CORS_HEADERS
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
jobs_table = dynamodb.Table(Config.JOBS_TABLE_NAME)
s3_client = boto3.client("s3")

def handle_create_upload(event):
    """
    POST /uploads
    Body: { "filename": "file.csv", "contentType": "text/csv" }
    Returns: { "uploadUrl", "jobId", "uploadKey" }
    """
    try:
        body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        payload = json.loads(body)
    except Exception:
        return _response(400, {"message": "Invalid JSON body"})

    filename = payload.get("filename")
    content_type = payload.get("contentType") or "application/octet-stream"

    if not filename:
        return _response(400, {"message": "filename is required"})

    # Generate a job ID and S3 key
    job_id = str(uuid.uuid4())
    # Store all uploads in a single "uploads/" folder with job ID as filename prefix
    safe_filename = filename.replace("/", "_")
    upload_key = f"uploads/{job_id}_{safe_filename}"

    # Put an initial job record into DynamoDB
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "jobId": job_id,
        "status": "PENDING_UPLOAD",
        "createdAt": now,
        "updatedAt": now,
        "filename": filename,
        "contentType": content_type,
        "bucket": Config.UPLOAD_BUCKET_NAME,
        "key": upload_key,
    }

    try:
        jobs_table.put_item(Item=item)
    except ClientError as e:
        print(f"DynamoDB put_item failed: {e}")
        return _response(500, {"message": "Failed to create job record"})

    # Generate a presigned S3 URL for the client to upload directly
    try:
        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": Config.UPLOAD_BUCKET_NAME,
                "Key": upload_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,  # 1 hour
        )
    except ClientError as e:
        print(f"Failed to generate presigned URL: {e}")
        return _response(500, {"message": "Failed to generate upload URL"})

    return _response(
        201,
        {
            "jobId": job_id,
            "uploadUrl": upload_url,
            "uploadKey": upload_key,
            "bucket": Config.UPLOAD_BUCKET_NAME,
            "status": "PENDING_UPLOAD",
        },
    )


def handle_get_job(job_id: str):
    """
    GET /jobs/{jobId}
    Returns the job record from DynamoDB if it exists.
    """
    try:
        resp = jobs_table.get_item(Key={"jobId": job_id})
    except ClientError as e:
        print(f"DynamoDB get_item failed: {e}")
        return _response(500, {"message": "Failed to read job"})

    item = resp.get("Item")
    if not item:
        return _response(404, {"message": "Job not found"})

    return _response(200, item)