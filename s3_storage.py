# Author: dhirenkumarsingh
"""AWS S3 integration for document storage."""

import logging
import boto3
from botocore.exceptions import ClientError
from config import settings

logger = logging.getLogger(__name__)


class S3Storage:
    """Handles S3 operations for document storage."""

    def __init__(self):
        logger.info("Initializing S3Storage")
        logger.info(f"AWS Region: {settings.aws_region}, Bucket: {settings.s3_bucket}")
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bucket_name = settings.s3_bucket
        logger.info("S3Storage initialized")

    def upload_document(self, file_path: str, document_id: str) -> str:
        """Upload a document to S3."""
        logger.info(
            f"Uploading document to S3: file_path={file_path}, document_id={document_id}"
        )
        key = f"documents/{document_id}/document.pdf"

        try:
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": "application/pdf"},
            )
            s3_path = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Successfully uploaded to: {s3_path}")
            return s3_path
        except ClientError as e:
            logger.error(f"Failed to upload document: {e}")
            raise Exception(f"Failed to upload document: {str(e)}")

    def download_document(self, document_id: str, destination_path: str) -> str:
        """Download a document from S3."""
        logger.info(f"Downloading document from S3: document_id={document_id}")
        key = f"documents/{document_id}/document.pdf"

        try:
            self.s3_client.download_file(self.bucket_name, key, destination_path)
            logger.info(f"Successfully downloaded to: {destination_path}")
            return destination_path
        except ClientError as e:
            logger.error(f"Failed to download document: {e}")
            raise Exception(f"Failed to download document: {str(e)}")

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from S3."""
        logger.info(f"Deleting document from S3: document_id={document_id}")
        key = f"documents/{document_id}/document.pdf"

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted document: {document_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete document: {e}")
            raise Exception(f"Failed to delete document: {str(e)}")

    def get_document_url(self, document_id: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for document access."""
        logger.info(f"Generating presigned URL for document: {document_id}")
        key = f"documents/{document_id}/document.pdf"

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )
            logger.info(f"Generated presigned URL, expires in {expiration}s")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate URL: {str(e)}")

    def list_documents(self, prefix: str = "documents/") -> list:
        """List all documents in the bucket."""
        logger.info(f"Listing documents in bucket: {self.bucket_name}")
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )
            documents = [
                obj["Key"].replace(prefix, "").split("/")[0]
                for obj in response.get("Contents", [])
            ]
            logger.info(f"Found {len(documents)} documents")
            return documents
        except ClientError as e:
            logger.error(f"Failed to list documents: {e}")
            raise Exception(f"Failed to list documents: {str(e)}")
