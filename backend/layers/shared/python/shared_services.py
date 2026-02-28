
from shared_repositories import update_job_repository

def update_job_status(job_id: str, status: str):
    update_job_repository(job_id, status)