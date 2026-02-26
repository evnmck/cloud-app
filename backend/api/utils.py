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