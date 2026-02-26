import json
from config import Config
from utils import response as _response, CORS_HEADERS
from controllers.upload_controller import handle_create_upload, handle_get_job
from auth import check_auth
import boto3

def handler(event, context):
    """
    Entry point for API Gateway -> Lambda proxy integration.
    """
    # Debug logging (shows up in CloudWatch Logs)
    print(f"Received event: {json.dumps(event)[:1000]}")

    auth_error = check_auth(event)
    if auth_error:
        return auth_error

    path = event.get("resource") or event.get("path", "")
    http_method = event.get("httpMethod", "")

    # Health check
    if path == "/health" and http_method == "GET":
        return _response(200, {"status": "ok", "stage": Config.STAGE})

    # POST /uploads
    if path == "/uploads" and http_method == "POST":
        return handle_create_upload(event)

    # GET /jobs/{jobId}
    if path == "/jobs/{jobId}" and http_method == "GET":
        path_params = event.get("pathParameters") or {}
        job_id = path_params.get("jobId")
        if not job_id:
            return _response(400, {"message": "Missing jobId in path"})
        return handle_get_job(job_id)

    # Fallback
    return _response(404, {"message": "Not found"})