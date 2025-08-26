import os
import boto3
import uuid
import subprocess
import logging
from botocore.exceptions import ClientError
import dotenv
dotenv.load_dotenv()

def upload_file_to_s3(file_path: str, object_name: str = None) -> str:
    s3_bucket = os.getenv("AWS_S3_BUCKET_NAME")
    if not s3_bucket:
        logging.error("AWS_S3_BUCKET_NAME environment variable is not set.")
        raise ValueError("AWS_S3_BUCKET_NAME is not set")

    # If an S3 object name is not specified, generate a unique one
    if object_name is None:
        file_extension = os.path.splitext(file_path)[1]
        file_name = os.path.basename(file_path)  # Just the file name
        unique_name = f"{uuid.uuid4()}{file_extension}"
        object_name = f"songs/original_song/{unique_name}"

    # Create an S3 client
    s3_client = boto3.client("s3")

    try:
        # Use upload_file for efficient handling of local files
        s3_client.upload_file(file_path, s3_bucket, object_name)
        logging.info(f"Successfully uploaded {file_path} to s3://{s3_bucket}/{object_name}")

        # Construct the S3 object URL
        # Note: For this URL to be public, the bucket/object must have public read access.
        region = s3_client.meta.region_name
        s3_url = f"https://{s3_bucket}.s3.{region}.amazonaws.com/{object_name}"
        
        return s3_url

    except FileNotFoundError:
        logging.error(f"The file to upload was not found: {file_path}")
        return None
    except ClientError as e:
        logging.error(f"An error occurred during S3 upload: {e}")
        return None
