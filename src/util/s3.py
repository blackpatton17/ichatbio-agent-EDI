import boto3
import os

class S3Client:
    def __init__(self, bucket_name=None, endpoint=None, access_key=None, secret_key=None):
        # self.bucket_name = bucket_name or os.environ.get("My_OSN_Bucket")
        # self.endpoint = endpoint or os.environ.get("My_OSN_Endpoint")
        # self.access_key = access_key or os.environ.get("My_OSN_Bucket_ACCESS_KEY")
        # self.secret_key = secret_key or os.environ.get("My_OSN_Bucket_SECRET_KEY")
        self.bucket_name = bucket_name or os.environ.get("S3_BUCKET_NAME")
        self.endpoint = endpoint or os.environ.get("S3_ENDPOINT")
        self.access_key = access_key or os.environ.get("S3_ACCESS_KEY")
        self.secret_key = secret_key or os.environ.get("S3_SECRET_KEY")
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint if self.endpoint else None,
        )

    def object_exists(self, key):
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except self.client.exceptions.NoSuchKey:
            return False
        except Exception:
            return False

    def upload_json(self, key, data):
        import json
        body = json.dumps(data, indent=2)
        self.client.put_object(Bucket=self.bucket_name, Key=key, Body=body, ContentType="application/json")

    def get_s3_url(self, key):
        if self.endpoint:
            return f"{self.endpoint}/{self.bucket_name}/{key}"
        return f"s3://{self.bucket_name}/{key}"
