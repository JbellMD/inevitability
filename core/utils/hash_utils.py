"""
Hash Utility Functions
--------------------
Standardized hash functions for the Inevitability system.
This module provides consistent hashing across all components,
standardizing on BLAKE3 as the primary hash algorithm with
fallback to blake2b where needed for compatibility.
"""

import json
import hashlib
from typing import Any, Dict, List, Union, Optional
import base64

# Attempt to import BLAKE3 (preferred algorithm)
try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False
    print("Warning: BLAKE3 not available, falling back to blake2b")


def hash_data(data: Any, digest_size: int = 32, as_hex: bool = True) -> str:
    """
    Generate a standardized hash of any data using BLAKE3 (or blake2b fallback).
    
    Args:
        data: Data to hash (strings, dicts, lists, etc.)
        digest_size: Size of digest in bytes (default: 32 bytes/256 bits)
        as_hex: Return as hex string (True) or base64 (False)
        
    Returns:
        str: Hash digest as hex string or base64
    """
    # Convert to bytes if not already
    if isinstance(data, str):
        data_bytes = data.encode('utf-8')
    elif isinstance(data, (dict, list)):
        # Sort keys for consistent hashing of dictionaries
        data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
    elif isinstance(data, bytes):
        data_bytes = data
    else:
        # Convert other types to string first
        data_bytes = str(data).encode('utf-8')
    
    # Use BLAKE3 if available, otherwise blake2b
    if HAS_BLAKE3:
        hasher = blake3.blake3(data_bytes)
        digest = hasher.digest(length=digest_size)
    else:
        hasher = hashlib.blake2b(data_bytes, digest_size=digest_size)
        digest = hasher.digest()
    
    # Return in requested format
    if as_hex:
        return digest.hex()
    else:
        return base64.b64encode(digest).decode('ascii')


def incremental_hasher(digest_size: int = 32) -> 'Hasher':
    """
    Create an incremental hasher for processing data in chunks.
    
    Args:
        digest_size: Size of digest in bytes (default: 32)
        
    Returns:
        Hasher: Incremental hasher object
    """
    return Hasher(digest_size)


class Hasher:
    """Incremental hasher for processing data in chunks."""
    
    def __init__(self, digest_size: int = 32):
        """
        Initialize an incremental hasher.
        
        Args:
            digest_size: Size of digest in bytes
        """
        self.digest_size = digest_size
        if HAS_BLAKE3:
            self.hasher = blake3.blake3()
        else:
            self.hasher = hashlib.blake2b(digest_size=digest_size)
    
    def update(self, data: Any) -> 'Hasher':
        """
        Update the hash with new data.
        
        Args:
            data: Data chunk to add to hash
            
        Returns:
            self: For chaining
        """
        # Convert to bytes if not already
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, (dict, list)):
            # Sort keys for consistent hashing
            data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            # Convert other types to string first
            data_bytes = str(data).encode('utf-8')
        
        self.hasher.update(data_bytes)
        return self
    
    def finalize(self, as_hex: bool = True) -> str:
        """
        Finalize and return the hash digest.
        
        Args:
            as_hex: Return as hex string (True) or base64 (False)
            
        Returns:
            str: Hash digest
        """
        if HAS_BLAKE3:
            digest = self.hasher.digest(length=self.digest_size)
        else:
            digest = self.hasher.digest()
        
        if as_hex:
            return digest.hex()
        else:
            return base64.b64encode(digest).decode('ascii')


def hash_file(file_path: str, chunk_size: int = 8192, 
              digest_size: int = 32, as_hex: bool = True) -> str:
    """
    Generate a hash for a file using chunked reading.
    
    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read (bytes)
        digest_size: Size of digest in bytes
        as_hex: Return as hex string (True) or base64 (False)
        
    Returns:
        str: Hash digest of file contents
    """
    hasher = incremental_hasher(digest_size)
    
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    
    return hasher.finalize(as_hex)


def verify_hash(data: Any, expected_hash: str, 
               digest_size: int = 32, as_hex: bool = True) -> bool:
    """
    Verify that data matches an expected hash.
    
    Args:
        data: Data to verify
        expected_hash: Expected hash value
        digest_size: Size of digest in bytes
        as_hex: Whether expected_hash is hex (True) or base64 (False)
        
    Returns:
        bool: True if hashes match
    """
    actual_hash = hash_data(data, digest_size, as_hex)
    return actual_hash == expected_hash


def algorithm_info() -> Dict[str, Any]:
    """
    Get information about the currently used hash algorithm.
    
    Returns:
        Dict: Information about hash algorithm
    """
    return {
        "primary_algorithm": "BLAKE3" if HAS_BLAKE3 else "BLAKE2b",
        "available_algorithms": ["BLAKE3", "BLAKE2b"] if HAS_BLAKE3 else ["BLAKE2b"],
        "default_digest_size": 32,
        "max_digest_size": 64 if HAS_BLAKE3 else 64,
        "security_bits": 256 if HAS_BLAKE3 else 256,
        "using_fallback": not HAS_BLAKE3
    }


if __name__ == "__main__":
    # Example usage
    print("Hash Algorithm Info:", algorithm_info())
    
    # Simple data hashing
    test_data = {"key": "value", "nested": {"data": [1, 2, 3]}}
    hash1 = hash_data(test_data)
    print(f"Hash of test data: {hash1}")
    
    # Verify hash
    print(f"Hash verification: {verify_hash(test_data, hash1)}")
    
    # Incremental hashing
    hasher = incremental_hasher()
    hasher.update("part1")
    hasher.update("part2")
    print(f"Incremental hash: {hasher.finalize()}")
    
    # Try both hex and base64 output
    print(f"Hex hash: {hash_data('test', as_hex=True)}")
    print(f"Base64 hash: {hash_data('test', as_hex=False)}")
