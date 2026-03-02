import json
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from controllers.upload_controller import create_upload, get_job


def _upload_event(body=None):
    return {
        "body": json.dumps(body) if body else None,
        "pathParameters": {},
    }


def _job_event(job_id=None):
    return {
        "pathParameters": {"jobId": job_id} if job_id else {},
    }


def _client_error():
    return ClientError({"Error": {"Code": "500", "Message": "AWS error"}}, "operation")


class TestCreateUpload:
    @patch("controllers.upload_controller.create_upload_service")
    def test_success_returns_201(self, mock_service):
        mock_service.return_value = {
            "jobId": "abc",
            "uploadUrl": "https://s3.example.com/presigned",
            "uploadKey": "uploads/abc/file.csv",
        }
        result = create_upload(_upload_event({"filename": "file.csv"}))
        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert body["jobId"] == "abc"

    def test_invalid_json_body_returns_400(self):
        result = create_upload({"body": "not-json"})
        assert result["statusCode"] == 400

    def test_missing_filename_returns_400(self):
        result = create_upload(_upload_event({"contentType": "text/csv"}))
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "filename" in body["message"]

    @patch("controllers.upload_controller.create_upload_service")
    def test_uses_default_content_type(self, mock_service):
        mock_service.return_value = {"jobId": "x", "uploadUrl": "url", "uploadKey": "key"}
        create_upload(_upload_event({"filename": "file.bin"}))
        mock_service.assert_called_once_with("file.bin", "application/octet-stream")

    @patch("controllers.upload_controller.create_upload_service")
    def test_aws_error_returns_500(self, mock_service):
        mock_service.side_effect = _client_error()
        result = create_upload(_upload_event({"filename": "file.csv"}))
        assert result["statusCode"] == 500


class TestGetJob:
    @patch("controllers.upload_controller.get_job_service")
    def test_success_returns_200(self, mock_service):
        from models.job import Job
        mock_service.return_value = Job(
            jobId="abc-123",
            status="PENDING_UPLOAD",
            createdAt="2024-01-01T00:00:00+00:00",
            updatedAt="2024-01-01T00:00:00+00:00",
            filename="file.csv",
            contentType="text/csv",
            bucket="my-bucket",
            key="uploads/abc-123/file.csv",
        )
        result = get_job(_job_event("abc-123"))
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["jobId"] == "abc-123"

    def test_missing_job_id_returns_400(self):
        result = get_job({"pathParameters": {}})
        assert result["statusCode"] == 400

    def test_missing_path_parameters_returns_400(self):
        result = get_job({"pathParameters": None})
        assert result["statusCode"] == 400

    @patch("controllers.upload_controller.get_job_service")
    def test_job_not_found_returns_404(self, mock_service):
        mock_service.return_value = None
        result = get_job(_job_event("nonexistent"))
        assert result["statusCode"] == 404

    @patch("controllers.upload_controller.get_job_service")
    def test_aws_error_returns_500(self, mock_service):
        mock_service.side_effect = _client_error()
        result = get_job(_job_event("abc-123"))
        assert result["statusCode"] == 500
