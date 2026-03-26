"""ZIP file handling utilities for skill packages"""

import os
import json
import zipfile
import hashlib
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ZipExtractionResult:
    """Result of ZIP file extraction and validation
    
    Attributes:
        success: Whether the extraction was successful
        error: Error message if extraction failed
        checksum: SHA-256 checksum of the ZIP file
        source_url: Path where the ZIP file is stored
        readme_content: Content of SKILL.md file
        meta_data: Parsed content of _meta.json file
        extracted_path: Path where files were extracted (for cleanup if needed)
    """
    success: bool
    error: Optional[str] = None
    checksum: Optional[str] = None
    source_url: Optional[str] = None
    readme_content: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    extracted_path: Optional[str] = None


class ZipHandler:
    """Handler for ZIP file operations related to skill packages"""
    
    def __init__(self, upload_dir: str = "./data/uploads"):
        """Initialize the ZIP handler
        
        Args:
            upload_dir: Directory to store uploaded ZIP files
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def calculate_checksum(file_path: str) -> str:
        """Calculate SHA-256 checksum of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 checksum as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def calculate_checksum_from_bytes(data: bytes) -> str:
        """Calculate SHA-256 checksum of bytes data
        
        Args:
            data: Bytes data
            
        Returns:
            SHA-256 checksum as hex string
        """
        return hashlib.sha256(data).hexdigest()
    
    def validate_zip_structure(self, zip_path: str) -> Tuple[bool, Optional[str]]:
        """Validate that a ZIP file has the expected structure
        
        Expected structure:
        - Optional: root folder with skill name
        - Required: SKILL.md file
        - Optional: _meta.json file
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                if not file_list:
                    return False, "ZIP file is empty"
                
                # Check for SKILL.md (might be in root or in a subfolder)
                skill_md_found = any(
                    name.endswith('SKILL.md') or name == 'SKILL.md'
                    for name in file_list
                )
                
                if not skill_md_found:
                    return False, "SKILL.md file not found in ZIP package"
                
                return True, None
                
        except zipfile.BadZipFile:
            return False, "Invalid ZIP file format"
        except Exception as e:
            return False, f"Error reading ZIP file: {str(e)}"
    
    def extract_skill_content(self, zip_path: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Extract SKILL.md content and _meta.json from a ZIP file
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            Tuple of (readme_content, meta_data)
        """
        readme_content = None
        meta_data = None
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    file_name = file_info.filename
                    
                    # Extract SKILL.md content
                    if file_name.endswith('SKILL.md'):
                        with zip_ref.open(file_name) as f:
                            readme_content = f.read().decode('utf-8')
                    
                    # Extract _meta.json content
                    if file_name.endswith('_meta.json'):
                        with zip_ref.open(file_name) as f:
                            meta_data = json.loads(f.read().decode('utf-8'))
                
        except Exception:
            pass
        
        return readme_content, meta_data
    
    async def save_uploaded_file(
        self, 
        file_data: bytes, 
        original_filename: str,
        skill_name: str,
        version: str
    ) -> ZipExtractionResult:
        """Save uploaded ZIP file and extract relevant content
        
        Args:
            file_data: Raw bytes of the uploaded file
            original_filename: Original filename of the upload
            skill_name: Name of the skill
            version: Version string
            
        Returns:
            ZipExtractionResult with extraction details
        """
        # Create a temporary file to validate the ZIP
        temp_dir = tempfile.mkdtemp()
        temp_zip_path = os.path.join(temp_dir, "temp.zip")
        
        try:
            # Write bytes to temporary file
            with open(temp_zip_path, 'wb') as f:
                f.write(file_data)
            
            # Validate ZIP structure
            is_valid, error = self.validate_zip_structure(temp_zip_path)
            if not is_valid:
                return ZipExtractionResult(success=False, error=error)
            
            # Calculate checksum
            checksum = self.calculate_checksum(temp_zip_path)
            
            # Extract content
            # readme_content, meta_data = self.extract_skill_content(temp_zip_path)
            
            # Create storage directory for the skill version
            skill_dir = self.upload_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())[:8]
            stored_filename = f"{skill_name}-{version}-{file_id}.zip"
            stored_path = skill_dir / stored_filename
            
            # Move file to permanent storage
            shutil.move(temp_zip_path, stored_path)
            
            # Generate source URL (relative path from uploads directory)
            source_url = f"/uploads/{skill_name}/{stored_filename}"
            
            return ZipExtractionResult(
                success=True,
                checksum=checksum,
                source_url=source_url,
                # readme_content=readme_content,
                # meta_data=meta_data,
                extracted_path=str(stored_path)
            )
            
        except Exception as e:
            return ZipExtractionResult(
                success=False,
                error=f"Failed to process ZIP file: {str(e)}"
            )
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def extract_to_directory(self, zip_path: str, extract_dir: str) -> Tuple[bool, Optional[str]]:
        """Extract ZIP file contents to a directory
        
        Args:
            zip_path: Path to the ZIP file
            extract_dir: Directory to extract to
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            return True, None
            
        except zipfile.BadZipFile:
            return False, "Invalid ZIP file format"
        except Exception as e:
            return False, f"Error extracting ZIP file: {str(e)}"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_path(self, source_url: str) -> str:
        """Convert source URL to actual file path
        
        Args:
            source_url: Source URL (e.g., /uploads/skill-name/file.zip)
            
        Returns:
            Actual file system path
        """
        # Remove leading /uploads/ if present
        if source_url.startswith("/uploads/"):
            relative_path = source_url[9:]  # len("/uploads/") = 9
        else:
            relative_path = source_url
        
        return str(self.upload_dir / relative_path)
