import json
import pytest
from unittest.mock import patch
from auth import check_auth


VALID_TOKEN = "test-token"


def _event(token=None, method="GET"):
    headers = {}
    if token is not None:
        headers["X-API-TOKEN"] = token
    return {"headers": headers, "httpMethod": method}


class TestCheckAuth:
    def test_valid_token_returns_none(self):
        result = check_auth(_event(token=VALID_TOKEN))
        assert result is None

    def test_missing_token_returns_401(self):
        result = check_auth(_event(token=None))
        assert result is not None
        assert result["statusCode"] == 401

    def test_wrong_token_returns_401(self):
        result = check_auth(_event(token="wrong-token"))
        assert result is not None
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert body["message"] == "Unauthorized"

    def test_options_request_bypasses_auth(self):
        result = check_auth(_event(token=None, method="OPTIONS"))
        assert result is None

    def test_lowercase_token_header_accepted(self):
        event = {"headers": {"x-api-token": VALID_TOKEN}, "httpMethod": "GET"}
        result = check_auth(event)
        assert result is None

    def test_missing_headers_key_returns_401(self):
        event = {"httpMethod": "GET"}
        result = check_auth(event)
        assert result is not None
        assert result["statusCode"] == 401

    def test_no_token_configured_allows_all(self):
        with patch("auth.Config") as mock_config:
            mock_config.API_TOKEN = None
            result = check_auth(_event(token=None))
            assert result is None
