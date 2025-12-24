import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

STAGE = os.environ.get("STAGE", "dev")
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
UPLOAD_BUCKET_NAME = os.environ["UPLOAD_BUCKET_NAME"]
API_TOKEN = os.environ.get("API_TOKEN")
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:5173")

dynamodb = boto3.resource("dynamodb")
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

s3_client = boto3.client("s3")


def handler(event, context):
    """
    Entry point for API Gateway -> Lambda proxy integration.
    """
    # Debug logging (shows up in CloudWatch Logs)
    print(f"Received event: {json.dumps(event)[:1000]}")

    headers = event.get("headers") or {}
    provided = headers.get("X-API-TOKEN") or headers.get("x-api-token")

    path = event.get("resource") or event.get("path", "")
    http_method = event.get("httpMethod", "")

    # Let OPTIONS pass through without auth
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": "",
        }

    # Auth for actual requests
    if API_TOKEN and provided != API_TOKEN:
        return _response(401, {"message": "Unauthorized"})

    # Health check
    if path == "/health" and http_method == "GET":
        return _response(200, {"status": "ok", "stage": STAGE})

    # POST /uploads
    if path == "/uploads" and http_method == "POST":
        return _handle_create_upload(event)

    # GET /jobs/{jobId}
    if path == "/jobs/{jobId}" and http_method == "GET":
        path_params = event.get("pathParameters") or {}
        job_id = path_params.get("jobId")
        if not job_id:
            return _response(400, {"message": "Missing jobId in path"})
        return _handle_get_job(job_id)

    # Fallback
    return _response(404, {"message": "Not found"})



# ---------- Handlers ----------

def _handle_create_upload(event):
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
        "bucket": UPLOAD_BUCKET_NAME,
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
                "Bucket": UPLOAD_BUCKET_NAME,
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
            "bucket": UPLOAD_BUCKET_NAME,
            "status": "PENDING_UPLOAD",
        },
    )


def _handle_get_job(job_id: str):
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


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": CORS_ORIGIN,
    "Access-Control-Allow-Headers": "Content-Type,X-API-TOKEN",
    "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
}

def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }
