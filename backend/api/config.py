import os

class Config:
    STAGE = os.environ.get("STAGE", "dev")
    JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
    UPLOAD_BUCKET_NAME = os.environ["UPLOAD_BUCKET_NAME"]
    API_TOKEN = os.environ.get("API_TOKEN")
    CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:5173")