from magika import Magika
import magic
import exiftool
import json
import os
from pathlib import Path
import hashlib


import pandas as pd
import numpy as np

def file_type_magika(file_path):
    """
    Identifies the file type using Magika.

    Args:
        file_path (str): The path to the file to be identified.

    Returns:
        str: The file type label identified by Magika, or "Unknown" if identification fails.
    """
    m = Magika()
    res = m.identify_path(Path(file_path))
    return res.output.ct_label if res else "Unknown"


def file_type_libmagic(file_path):
    """
    Identifies the file type using the libmagic library.

    Args:
        file_path (str): The path to the file to be identified.

    Returns:
        str: The file type identified by libmagic, or "Unknown" if an error occurs.
    """
    try:
        file_magic = magic.Magic()
        file_type = file_magic.from_file(file_path)
    except Exception as e:
        print(f"Error identifying file type with libmagic: {e} - File: {file_path}")
        file_type = None
    return file_type if file_type else "Unknown"


def file_type_exiftool_save_json(file_path, sha256):
    """
    Identifies the file type using ExifTool and saves metadata as JSON.
    If a cached JSON file exists for the SHA-256 hash, it loads and uses that instead.

    Args:
        file_path (str): The path to the file to be identified.
        sha256 (str): The SHA-256 hash of the file, used to cache results.

    Returns:
        str: The MIME type identified by ExifTool, or "Unknown" if the type cannot be determined.
    """
    cache_path = f"./exiftool_output/{sha256}.json"
    
    # Load cached metadata if available
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            metadata = json.load(f)
        return metadata[0].get('File:MIMEType', 'Unknown')

    # Retrieve metadata using ExifTool and save it
    with exiftool.ExifTool() as e:
        metadata = e.execute_json(file_path)
        file_type = metadata[0].get('File:MIMEType', 'Unknown')
    
    # Save metadata to cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(metadata, f)
    
    return file_type


def get_all_file_types(file_path, sha256):
    """
    Retrieves file types using Magika, libmagic, and ExifTool.

    Args:
        file_path (str): The path to the file to be identified.
        sha256 (str): The SHA-256 hash of the file, used for caching ExifTool results.

    Returns:
        tuple: A tuple containing the file type from Magika, libmagic, and ExifTool.
    """
    magika_type = file_type_magika(file_path)
    libmagic_type = file_type_libmagic(file_path)
    exiftool_type = file_type_exiftool_save_json(file_path, sha256)
    return magika_type, libmagic_type, exiftool_type


def compute_hash(file_path, hash_type):
    """
    Computes the specified hash type (sha256, md5, or sha1) for a given file.

    Args:
        file_path (str): The file path to compute the hash for.
        hash_type (str): The hash type ('sha256', 'md5', or 'sha1').

    Returns:
        str: The computed hash in hexadecimal format.
    """
    hash_obj = getattr(hashlib, hash_type)()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            hash_obj.update(byte_block)
    return hash_obj.hexdigest()


def compute_hashes(file_path):
    """
    Computes sha256, md5, and sha1 hashes for the given file.

    Args:
        file_path (str): The path to the file.

    Returns:
        tuple: sha256, md5, and sha1 hashes in hexadecimal format.
    """
    return (
        compute_hash(file_path, 'sha256'),
        compute_hash(file_path, 'md5'),
        compute_hash(file_path, 'sha1')
    )
