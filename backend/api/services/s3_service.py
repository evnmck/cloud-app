import boto3

s3_client = boto3.client("s3")

def generate_presigned_upload_url(bucket: str, key: str, content_type: str, expires_in: int = 3600) -> str:
    return s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )