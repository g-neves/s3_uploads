import os
import subprocess
import sys

import boto3
from botocore.client import BaseClient
from dotenv import load_dotenv

load_dotenv()


def show_notification(
    message: str, title: str = "S3 Upload", style: str = "informational"
) -> None:
    """
    Show a macOS notification

    Args:
        message: The message to display in the notification
        title: The title of the notification window
        style: The style of the alert ("informational", "warning", or "critical")
    """
    script: str = f"""
    display alert "{title}" message "{message}" as {style}
    """
    subprocess.run(["osascript", "-e", script])


def upload_to_s3(file_path: str, bucket_name: str, s3_prefix: str = "") -> bool:
    """
    Upload a file to S3 bucket

    Args:
        file_path: Local path to the file
        bucket_name: S3 bucket name
        s3_prefix: Optional prefix/folder in S3 (e.g., "uploads/" or "backups/")

    Returns:
        True if upload is successful, False otherwise
    """
    file_name: str = os.path.basename(file_path)
    if s3_prefix:
        s3_key: str = f"{s3_prefix.rstrip('/')}/{file_name}"
    else:
        s3_key: str = file_name
    try:
        s3_client: BaseClient = boto3.client("s3")


        s3_client.upload_file(
            file_path,
            bucket_name,
            s3_key,
        )
        show_notification(f"✓ Uploaded: {file_name}")
        return True
    except Exception as e:
        error_msg: str = f"Failed to upload {file_name}: {str(e)}"
        show_notification(error_msg, "S3 Upload Error", "critical")
        return False


def main() -> None:
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "your-default-bucket-name")
    S3_PREFIX: str = os.getenv("S3_PREFIX", "")

    # Get list of files from command line arguments;
    # the files are passed from the Automator Quick Action
    files: list[str] = sys.argv[1:]

    if not files:
        show_notification("No files selected for upload", "S3 Upload Error", "critical")
        return

    success_count: int = 0
    error_count: int = 0
    for file_path in files:
        if os.path.exists(file_path):
            if upload_to_s3(file_path, S3_BUCKET_NAME, S3_PREFIX):
                success_count += 1
            else:
                error_count += 1
        else:
            error_count += 1
            error_msg: str = f"File not found: {file_path}"
            show_notification(error_msg, "S3 Upload Error", "critical")
    if len(files) > 1 and success_count == len(files):
        show_notification(f"All {success_count} file(s) uploaded to S3 successfully!")
    elif len(files) > 1 and success_count > 0:
        show_notification(f"Uploaded {success_count} of {len(files)} files.")


if __name__ == "__main__":
    main()
