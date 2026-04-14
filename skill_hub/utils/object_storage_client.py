# -*- coding=utf-8
import sys
import logging
from typing import Optional, Dict, Any

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

from skill_hub.config.config import Config

logger = logging.getLogger(__name__)

class ObjectStorageClient:
    """Client for interacting with Tencent Cloud Object Storage (COS)"""

    def __init__(self, config: Config):
        self.secret_id = config.cos_secret_id
        self.secret_key = config.cos_secret_key
        self.region = 'ap-beijing'

        if not self.secret_id or not self.secret_key or not self.region:
            logger.warning("Object storage credentials are not fully configured")
            self.client = None
            return

        self.cos_config = CosConfig(
            Region=self.region,
            SecretId=self.secret_id,
            SecretKey=self.secret_key,
            Token=None,
            Scheme='https'
        )
        self.client = CosS3Client(self.cos_config)

    def list_buckets(self) -> Optional[Dict[str, Any]]:
        """List all buckets in the region"""
        if not self.client:
            logger.error("COS client is not initialized")
            return None

        try:
            response = self.client.list_buckets()
            return response
        except Exception as e:
            logger.error(f"Failed to list buckets: {str(e)}")
            return None

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists

        Args:
            bucket_name: The name of the bucket (format: BucketName-Appid)

        Returns:
            True if the bucket exists, False otherwise
        """
        if not self.client:
            logger.error("COS client is not initialized")
            return False

        try:
            return self.client.bucket_exists(Bucket=bucket_name)
        except Exception as e:
            logger.error(f"Failed to check if bucket {bucket_name} exists: {str(e)}")
            return False

    def create_bucket(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """Create a new bucket

        Args:
            bucket_name: The name of the bucket to create (format: BucketName-Appid)
        """
        if not self.client:
            logger.error("COS client is not initialized")
            return None

        try:
            response = self.client.create_bucket(
                Bucket=bucket_name
            )
            return response
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {str(e)}")
            return None

    def upload_file(self, bucket_name: str, local_file_path: str, object_key: str) -> Optional[Dict[str, Any]]:
        """Upload a file to COS using the advanced upload interface

        Args:
            bucket_name: The name of the bucket
            local_file_path: The local path of the file to upload
            object_key: The destination key in the bucket

        Returns:
            The response from COS if successful, None otherwise
        """
        if not self.client:
            logger.error("COS client is not initialized")
            return None

        try:
            # Using the advanced upload interface which handles multipart uploads for large files
            response = self.client.upload_file(
                Bucket=bucket_name,
                LocalFilePath=local_file_path,
                Key=object_key,
                PartSize=1,
                MAXThread=10,
                EnableMD5=False
            )
            return response
        except Exception as e:
            logger.error(f"Failed to upload file {local_file_path} to {bucket_name}/{object_key}: {str(e)}")
            return None

    def clear_folder(self, bucket_name: str, folder_prefix: str) -> bool:
        """Clear all objects in a specific folder (prefix)

        Args:
            bucket_name: The name of the bucket
            folder_prefix: The prefix of the folder to clear (e.g., 'uploads/')

        Returns:
            True if successfully cleared or empty, False on failure
        """
        if not self.client:
            logger.error("COS client is not initialized")
            return False

        try:
            # Ensure folder_prefix ends with '/' to only match contents of that folder
            if not folder_prefix.endswith('/'):
                folder_prefix += '/'

            is_truncated = True
            marker = ""

            while is_truncated:
                response = self.client.list_objects(
                    Bucket=bucket_name,
                    Prefix=folder_prefix,
                    Marker=marker,
                    MaxKeys=1000
                )

                if 'Contents' not in response:
                    break

                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]

                if objects_to_delete:
                    self.client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Object': objects_to_delete, 'Quiet': 'true'}
                    )

                is_truncated = response.get('IsTruncated', 'false') == 'true'
                if is_truncated:
                    marker = response.get('NextMarker', '')

            return True
        except Exception as e:
            logger.error(f"Failed to clear folder {folder_prefix} in bucket {bucket_name}: {str(e)}")
            return False


if __name__ == "__main__":
    from skill_hub.config.config import Config
    import os

    # Configure logging for testing
    logging.basicConfig(level=logging.INFO)

    config = Config()
    client = ObjectStorageClient(config)

    if client.client:
        # Create a dummy file for testing
        test_file_path = "./default.png"

        bucket_name = "sudoclaw-1309794936"
        object_key = "skill-hub/tmp/default.png"

        logger.info(f"Testing upload_file to bucket {bucket_name} with key {object_key}")
        # client.clear_folder(bucket_name, 'skill-hub/tmp/')
        result = client.upload_file(bucket_name, test_file_path, object_key)

        if result:
            logger.info(f"Upload successful: {result}")
        else:
            logger.error("Upload failed.")

        # Clean up local file
        # if os.path.exists(test_file_path):
        #     os.remove(test_file_path)
    else:
        logger.error("Client not initialized. Check your credentials.")

