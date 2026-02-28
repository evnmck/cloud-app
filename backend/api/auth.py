from config import Config
from utils import response

def check_auth(event):
    """Returns None if auth passes, otherwise returns error response"""
    headers = event.get("headers") or {}
    provided = headers.get("X-API-TOKEN") or headers.get("x-api-token")
    http_method = event.get("httpMethod", "")
    
    # OPTIONS pass through
    if http_method == "OPTIONS":
        return None
    
    # Check token
    if Config.API_TOKEN and provided != Config.API_TOKEN:
        return response(401, {"message": "Unauthorized"})
    
    return None