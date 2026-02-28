import base64
import json 
from config import Config

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": Config.CORS_ORIGIN,
    "Access-Control-Allow-Headers": "Content-Type,X-API-TOKEN",
    "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
}

def response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }

def parse_body(event):
    try:
        body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        return json.loads(body)
    except Exception:
        return None