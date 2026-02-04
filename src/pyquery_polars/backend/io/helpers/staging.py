"""
StagingManager

Helper class for managing staging directories.
"""

from typing import Optional

import os
import tempfile
import time
import uuid
import re
import shutil


class StagingManager:
    default_stage_name = "pyquery_staging"

    def __init__(self, staging_dir: Optional[str] = None, staging_folder_name: Optional[str] = None):

        self.env_path = os.environ.get("PYQUERY_STAGING_DIR")

        if not staging_dir and not staging_folder_name:
            self.staging_dir = self._get_staging_dir(self.default_stage_name)
        elif staging_dir and not staging_folder_name:
            self.staging_dir = os.path.join(staging_dir, self.default_stage_name) if os.path.exists(
                staging_dir) else self._get_staging_dir(self.default_stage_name)
        elif staging_dir and staging_folder_name:
            self.staging_dir = os.path.join(staging_dir, staging_folder_name) if os.path.exists(
                staging_dir) else self._get_staging_dir(staging_folder_name)

    def _get_staging_dir(self, staging_name: str) -> str:
        """
        Get or create the centralized staging directory.
        Respects 'PYQUERY_STAGING_DIR' environment variable if set.
        """
        env_path = self.env_path
        if env_path:
            staging_path = os.path.abspath(env_path)
        else:
            temp_dir = tempfile.gettempdir()
            staging_path = os.path.join(temp_dir, staging_name)

        os.makedirs(staging_path, exist_ok=True)
        return staging_path

    def create_unique_staging_folder(self, base_name: str) -> str:
        """
        Create a unique subfolder in the staging directory.
        Format: timestamp_uuid_basename
        """
        staging_root = self.staging_dir

        # Generate unique identifier components
        ts = int(time.time())
        unique_id = uuid.uuid4().hex[:8]

        # Sanitize base name
        safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', base_name)

        folder_name = f"{ts}_{unique_id}_{safe_name}"
        folder_path = os.path.join(staging_root, folder_name)

        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def cleanup_staging_files(self, max_age_hours: int = 24):
        """Clean up old files from the staging directory."""
        try:
            staging_dir = self.staging_dir
            now = time.time()
            cutoff = now - (max_age_hours * 3600)

            if os.path.exists(staging_dir):
                for filename in os.listdir(staging_dir):
                    file_path = os.path.join(staging_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            if os.path.getmtime(file_path) < cutoff:
                                os.remove(file_path)
                        elif os.path.isdir(file_path):
                            # Clean up stale directories
                            if os.path.getmtime(file_path) < cutoff:
                                shutil.rmtree(file_path)
                    except Exception as e:
                        pass
        except Exception as e:
            pass

    def cleanup_staging_file(self, file_path: str):
        """Remove a specific staging file immediately."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
