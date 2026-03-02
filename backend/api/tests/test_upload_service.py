import pytest
from unittest.mock import patch, MagicMock
from models.job import Job
from services.upload_service import create_upload_service, get_job_service


class TestCreateUploadService:
    @patch("services.upload_service.generate_presigned_upload_url")
    @patch("services.upload_service.create_upload_repository")
    def test_returns_expected_keys(self, mock_repo, mock_presign):
        mock_presign.return_value = "https://s3.example.com/presigned"
        result = create_upload_service("report.csv", "text/csv")
        assert "jobId" in result
        assert "uploadUrl" in result
        assert "uploadKey" in result
        assert "bucket" in result
        assert result["status"] == "PENDING_UPLOAD"

    @patch("services.upload_service.generate_presigned_upload_url")
    @patch("services.upload_service.create_upload_repository")
    def test_upload_key_contains_filename(self, mock_repo, mock_presign):
        mock_presign.return_value = "https://s3.example.com/presigned"
        result = create_upload_service("my_file.csv", "text/csv")
        assert "my_file.csv" in result["uploadKey"]

    @patch("services.upload_service.generate_presigned_upload_url")
    @patch("services.upload_service.create_upload_repository")
    def test_slashes_in_filename_are_replaced(self, mock_repo, mock_presign):
        mock_presign.return_value = "https://s3.example.com/presigned"
        result = create_upload_service("path/to/file.csv", "text/csv")
        # Slashes in the filename portion should be replaced
        key_filename = result["uploadKey"].split("/", 2)[-1]
        assert "/" not in key_filename

    @patch("services.upload_service.generate_presigned_upload_url")
    @patch("services.upload_service.create_upload_repository")
    def test_repository_called_once(self, mock_repo, mock_presign):
        mock_presign.return_value = "https://s3.example.com/presigned"
        create_upload_service("file.csv", "text/csv")
        mock_repo.assert_called_once()

    @patch("services.upload_service.generate_presigned_upload_url")
    @patch("services.upload_service.create_upload_repository")
    def test_presigned_url_called_with_correct_content_type(self, mock_repo, mock_presign):
        mock_presign.return_value = "https://s3.example.com/presigned"
        create_upload_service("file.csv", "text/csv")
        args = mock_presign.call_args.args
        assert args[2] == "text/csv"


class TestGetJobService:
    @patch("services.upload_service.get_job_repository")
    def test_returns_job_when_found(self, mock_repo):
        mock_repo.return_value = {
            "jobId": "abc-123",
            "status": "PENDING_UPLOAD",
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-01-01T00:00:00+00:00",
            "filename": "file.csv",
            "contentType": "text/csv",
            "bucket": "my-bucket",
            "key": "uploads/abc-123/file.csv",
        }
        result = get_job_service("abc-123")
        assert isinstance(result, Job)
        assert result.jobId == "abc-123"
        assert result.status == "PENDING_UPLOAD"

    @patch("services.upload_service.get_job_repository")
    def test_returns_none_when_not_found(self, mock_repo):
        mock_repo.return_value = None
        result = get_job_service("nonexistent")
        assert result is None
