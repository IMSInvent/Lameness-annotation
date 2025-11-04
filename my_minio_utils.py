"""
MinIO client module for handling connections and operations.

This module provides functionality to connect to MinIO storage and
retrieve images from the preprocessed/oakd_43 folder structure.
"""

from minio import Minio
from minio.error import S3Error
from typing import List, Tuple, Optional
import io
from datetime import datetime
import yaml


class MinioClient:
    """
    MinIO client for managing storage operations.
    
    Handles connection to MinIO server and provides methods for
    listing and retrieving images from the preprocessed bucket.
    """
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        """
        Initialize MinIO client.
        
        Args:
            endpoint (str): MinIO server endpoint (IP:PORT).
            access_key (str): Access key for authentication.
            secret_key (str): Secret key for authentication.
            secure (bool): Whether to use HTTPS (default: False).
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.endpoint = endpoint
    
    def list_images_from_preprocessed(
        self, 
        bucket_name: str, 
        base_folder: str = "oakd_43"
    ) -> List[str]:
        """
        List all images from preprocessed/oakd_43 folder and its date subfolders.
        
        The folder structure is: preprocessed/oakd_43/YYYY/MM/DD/images
        
        Args:
            bucket_name (str): Name of the bucket (e.g., 'preprocessed').
            base_folder (str): Base folder name (default: 'oakd_43').
        
        Returns:
            List[str]: List of image file paths.
        """
        images = []
        prefix = f"{base_folder}/"
        
        try:
            objects = self.client.list_objects(
                bucket_name, 
                prefix=prefix, 
                recursive=True
            )
            
            for obj in objects:
                # Filter only image files
                if obj.object_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    images.append(obj.object_name)
            
            return sorted(images)
        
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []
    
    def get_image(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """
        Retrieve an image from MinIO storage.
        
        Args:
            bucket_name (str): Name of the bucket.
            object_name (str): Full path to the object.
        
        Returns:
            Optional[bytes]: Image data as bytes, or None if error occurs.
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        
        except S3Error as e:
            print(f"Error retrieving object {object_name}: {e}")
            return None
    
    def upload_annotation(
        self, 
        bucket_name: str, 
        object_name: str, 
        data: bytes
    ) -> bool:
        """
        Upload annotation JSON to MinIO storage.
        
        Args:
            bucket_name (str): Name of the bucket (e.g., 'lameness').
            object_name (str): Full path for the annotation file.
            data (bytes): JSON data as bytes.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type='application/json'
            )
            return True
        
        except S3Error as e:
            print(f"Error uploading annotation {object_name}: {e}")
            return False
    
    def list_annotations(
        self, 
        bucket_name: str, 
        base_folder: str = "oakd_43"
    ) -> List[str]:
        """
        List all annotation files from the annotations bucket.
        
        Args:
            bucket_name (str): Name of the annotations bucket.
            base_folder (str): Base folder name (default: 'oakd_43').
        
        Returns:
            List[str]: List of annotation file paths.
        """
        annotations = []
        prefix = f"{base_folder}/"
        
        try:
            objects = self.client.list_objects(
                bucket_name, 
                prefix=prefix, 
                recursive=True
            )
            
            for obj in objects:
                if obj.object_name.endswith('.json'):
                    annotations.append(obj.object_name)
            
            return annotations
        
        except S3Error as e:
            print(f"Error listing annotations: {e}")
            return []
    
    def check_bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a bucket exists.
        
        Args:
            bucket_name (str): Name of the bucket to check.
        
        Returns:
            bool: True if bucket exists, False otherwise.
        """
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error as e:
            print(f"Error checking bucket {bucket_name}: {e}")
            return False


def load_config_from_yaml(config_path: str = "dev_config.yaml") -> dict:
    """
    Load MinIO configuration from YAML file.
    
    Args:
        config_path (str): Path to the configuration file.
    
    Returns:
        dict: Configuration dictionary with MinIO settings.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            # Read line by line and parse manually
            config = {}
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    config[key] = value
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def create_minio_client_from_config(config_path: str = "dev_config.yaml") -> Optional[MinioClient]:
    """
    Create MinIO client from configuration file.
    
    Args:
        config_path (str): Path to the configuration file.
    
    Returns:
        Optional[MinioClient]: Initialized MinIO client or None if error occurs.
    """
    config = load_config_from_yaml(config_path)
    
    if not config:
        return None
    
    try:
        endpoint = f"{config.get('MINIO_IP')}:{config.get('MINIO_PORT')}"
        return MinioClient(
            endpoint=endpoint,
            access_key=config.get('ACCESS_KEY'),
            secret_key=config.get('SECRET_KEY'),
            secure=False
        )
    except Exception as e:
        print(f"Error creating MinIO client: {e}")
        return None
