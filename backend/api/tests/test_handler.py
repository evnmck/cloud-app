import json
import pytest
from unittest.mock import patch, MagicMock
from handler import handler


VALID_TOKEN = "test-token"


def _event(path="/health", method="GET", body=None, path_params=None):
    return {
        "resource": path,
        "path": path,
        "httpMethod": method,
        "headers": {"X-API-TOKEN": VALID_TOKEN},
        "body": json.dumps(body) if body else None,
        "pathParameters": path_params,
    }


class TestHandlerHealth:
    def test_health_check_returns_200(self):
        result = handler(_event("/health", "GET"), {})
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ok"

    def test_health_check_includes_stage(self):
        result = handler(_event("/health", "GET"), {})
        body = json.loads(result["body"])
        assert "stage" in body


class TestHandlerRouting:
    def test_unknown_route_returns_404(self):
        result = handler(_event("/unknown", "GET"), {})
        assert result["statusCode"] == 404

    def test_wrong_method_returns_404(self):
        result = handler(_event("/health", "POST"), {})
        assert result["statusCode"] == 404

    def test_unauthenticated_request_returns_401(self):
        event = _event("/health", "GET")
        event["headers"] = {}
        result = handler(event, {})
        assert result["statusCode"] == 401

    @patch("handler.create_upload")
    def test_post_uploads_calls_controller(self, mock_create):
        mock_create.return_value = {"statusCode": 201, "body": "{}"}
        event = _event("/uploads", "POST", body={"filename": "test.csv"})
        handler(event, {})
        mock_create.assert_called_once_with(event)

    @patch("handler.get_job")
    def test_get_job_calls_controller(self, mock_get_job):
        mock_get_job.return_value = {"statusCode": 200, "body": "{}"}
        event = _event("/jobs/{jobId}", "GET", path_params={"jobId": "abc-123"})
        handler(event, {})
        mock_get_job.assert_called_once_with(event)
