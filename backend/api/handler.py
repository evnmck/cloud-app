import json
from config import Config
from utils import response as _response
from controllers.upload_controller import create_upload, get_job, update_job
from auth import check_auth

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
        return create_upload(event)

    # GET /jobs/{jobId}
    if path == "/jobs/{jobId}" and http_method == "GET":
        return get_job(event)
    
    # PUT /jobs/{jobId}/status - optional endpoint if you want to allow manual status updates (not required for the S3 event flow)
    if path == "/jobs/{jobId}/status" and http_method == "PUT":
        return update_job(event)

    # Fallback
    return _response(404, {"message": "Not found"})