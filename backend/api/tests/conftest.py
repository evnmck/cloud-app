import os
import sys

# Set required environment variables before any application modules are imported
os.environ.setdefault("JOBS_TABLE_NAME", "test-jobs-table")
os.environ.setdefault("UPLOAD_BUCKET_NAME", "test-upload-bucket")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("STAGE", "test")
os.environ.setdefault("CORS_ORIGIN", "http://localhost:5173")

# Dummy AWS credentials/region so boto3 module-level initialisation succeeds
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

# Add the api directory to the path so tests can import application modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Add the shared layer to path for imports like "from shared_services import ..."
shared_layer_path = os.path.join(os.path.dirname(__file__), "../../../backend/layers/shared/python")
if os.path.exists(shared_layer_path):
    sys.path.insert(0, shared_layer_path)

