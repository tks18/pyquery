from typing import List, Optional, Dict

import os
import codecs
import re
import io

from chardet.universaldetector import UniversalDetector

from pyquery_polars.backend.io.helpers.staging import StagingManager


class FileEncodingConverter:
    """
    Utilities for detection and conversion of file (csv) encodings to utf-8
    """

    def __init__(self, staging_manager: StagingManager) -> None:
        self.staging = staging_manager

    def detect_encoding(self, file_path: str, limit_bytes: int = 200_000) -> str:
        """
        Robustly detect file encoding using streaming analysis (UniversalDetector).
        Scans up to `limit_bytes` (default 200KB) or until high confidence is reached.
        """
        try:
            detector = UniversalDetector()

            # Read in binary mode, 16KB chunks
            chunk_size = 16 * 1024
            processed_bytes = 0

            with open(file_path, 'rb') as f:
                while processed_bytes < limit_bytes:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    detector.feed(chunk)
                    processed_bytes += len(chunk)

                    if detector.done:
                        break

            detector.close()
            result = detector.result

            encoding = result['encoding']
            confidence = result['confidence']

            # Confidence Threshold
            if not encoding or (confidence and confidence < 0.6):
                return 'utf-8'

            # Normalize typical compatible encodings
            if encoding.lower() in ['ascii', 'utf-8-sig']:
                return 'utf-8'

            return encoding

        except Exception:
            # Fallback to UTF-8 on any error
            return 'utf-8'

    def batch_detect_encodings(self, files: List[str]) -> Dict[str, str]:
        """
        Detect encodings for a list of files.
        Returns a dictionary mapping file path to detected encoding.
        Only returns entries where encoding is NOT utf8 (or ascii).
        """
        results = {}
        for f in files:
            # Skip if not a text file (simplified check)
            ext = os.path.splitext(f)[1].lower()
            if ext not in [".csv", ".txt", ".json", ".ndjson"]:
                continue

            enc = self.detect_encoding(f)
            # Normalize: ascii is compatible with utf8
            if enc.lower() not in ['utf8', 'utf-8', 'ascii']:
                results[f] = enc
        return results

    def convert_file_to_utf8(self, file_path: str, source_encoding: str, dataset_alias: Optional[str] = None) -> str:
        """
        Convert a file from source_encoding to UTF-8 using robust streaming.
        Features:
        - Normalizes newlines to '\\n' (critical for Polars CSV parser robustness)
        - Removes NULL bytes (\\x00)
        - Uses 'replace' error handler for garbage characters
        - Streams in 4MB chunks for low RAM usage
        """
        # 1. Validate Encoding
        try:
            if not source_encoding:
                source_encoding = "utf-8"
            codecs.lookup(source_encoding)
        except LookupError:
            print(
                f"Warning: Encoding '{source_encoding}' not found, falling back to 'utf-8'.")
            source_encoding = "utf-8"

        new_path = None
        try:
            # Use alias if provided, else filename
            base_name = dataset_alias if dataset_alias else os.path.basename(
                file_path)

            # Create unique folder for this conversion
            staging_dir = self.staging.create_unique_staging_folder(base_name)

            filename = os.path.basename(file_path)

            # Sanitize filename
            safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
            new_filename = f"utf8_{safe_name}"
            new_path = os.path.join(staging_dir, new_filename)

            # 4MB Chunk Size for better IO throughput
            chunk_size = 4 * 1024 * 1024

            # Open Source: newline=None enables Universal Newlines (normalizes \r\n to \n)
            # Open Target: newline='\n' ensures we write clean Unix-style output
            with io.open(file_path, 'r', encoding=source_encoding, errors='replace', newline=None) as source_f:
                with io.open(new_path, 'w', encoding='utf-8', newline='\n') as target_f:
                    while True:
                        chunk = source_f.read(chunk_size)
                        if not chunk:
                            break

                        # Robustness: Remove NULL bytes which confuse C-parsers
                        if '\0' in chunk:
                            chunk = chunk.replace('\0', '')

                        target_f.write(chunk)

            return new_path

        except Exception as e:
            print(f"Failed to convert {file_path}: {e}")
            # Attempt cleanup of partial file
            # Check if new_path was ever assigned (it is local to try block, but accessible in except if assigned)
            # But to be safe against 'possibly unbound' (if exception happened before assignment), we check
            if 'new_path' in locals() and new_path and os.path.exists(new_path):
                try:
                    os.remove(new_path)
                except:
                    pass
            raise e
