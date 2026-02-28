from dataclasses import asdict
from services.upload_service import create_upload_service, get_job_service
from shared_services import update_job_status
from utils import parse_body, response as _response
from botocore.exceptions import ClientError

def create_upload(event):
    """
    POST /uploads
    Body: { "filename": "file.csv", "contentType": "text/csv" }
    Returns: { "uploadUrl", "jobId", "uploadKey" }
    """
    body = parse_body(event)
    if body is None:
        return _response(400, {"message": "Invalid JSON body"})
    
    filename = body.get("filename")
    if not filename:
        return _response(400, {"message": "filename is required"})
    
    content_type = body.get("contentType") or "application/octet-stream"

    try:
        upload_data = create_upload_service(filename, content_type)
        return _response(201, upload_data)
    except ClientError as e:
        return _response(500, {"message": "Failed to create upload"})


def get_job(event):
    """
    GET /jobs/{jobId}
    Returns the job record from DynamoDB if it exists.
    """
    path_params = event.get("pathParameters") or {}
    job_id = path_params.get("jobId")
    if not job_id:
        return _response(400, {"message": "Missing jobId in path"})

    try:
        job = get_job_service(job_id)
        if not job:
            return _response(404, {"message": "Job not found"})
        return _response(200, asdict(job))
    except ClientError as e:
        return _response(500, {"message": "Failed to read job"})
    
def update_job_status(event):
    """
    Update job status based on S3 event. The actual update logic is handled in the upload handler Lambda using the shared repository function (update_job_repository).
    """
    path_params = event.get("pathParameters") or {}
    job_id = path_params.get("jobId")
    if not job_id:
        return _response(400, {"message": "Missing jobId in path"})
    try:
        update_job_status(job_id, "UPLOADED")
        return _response(200, {"message": "Job status updated"})
    except ClientError as e:
        return _response(500, {"message": "Failed to update job status"})