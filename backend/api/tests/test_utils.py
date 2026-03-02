import json
import pytest
from utils import response, parse_body


class TestResponse:
    def test_returns_correct_status_code(self):
        result = response(200, {"status": "ok"})
        assert result["statusCode"] == 200

    def test_body_is_json_string(self):
        result = response(201, {"jobId": "abc"})
        body = json.loads(result["body"])
        assert body == {"jobId": "abc"}

    def test_headers_include_content_type(self):
        result = response(200, {})
        assert result["headers"]["Content-Type"] == "application/json"

    def test_headers_include_cors_origin(self):
        result = response(200, {})
        assert "Access-Control-Allow-Origin" in result["headers"]

    def test_error_response(self):
        result = response(404, {"message": "Not found"})
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["message"] == "Not found"


class TestParseBody:
    def test_parses_valid_json(self):
        event = {"body": '{"filename": "test.csv"}'}
        result = parse_body(event)
        assert result == {"filename": "test.csv"}

    def test_returns_empty_dict_when_body_is_none(self):
        event = {"body": None}
        result = parse_body(event)
        assert result == {}

    def test_returns_none_on_invalid_json(self):
        event = {"body": "not-json"}
        result = parse_body(event)
        assert result is None

    def test_decodes_base64_body(self):
        import base64
        raw = json.dumps({"filename": "file.csv"})
        encoded = base64.b64encode(raw.encode()).decode()
        event = {"body": encoded, "isBase64Encoded": True}
        result = parse_body(event)
        assert result == {"filename": "file.csv"}

    def test_returns_empty_dict_when_no_body_key(self):
        event = {}
        result = parse_body(event)
        assert result == {}
