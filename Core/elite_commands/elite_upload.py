#!/usr/bin/env python3
"""
Elite Upload Command - Advanced file upload with integrity checking
Handles chunked uploads with resume capability
"""

import os
import hashlib
import zlib
import base64
import time
import secrets

def elite_upload(upload_data, destination_path, overwrite=False):
    """
    Upload file with advanced features:
    - Integrity verification
    - Atomic write (temp file then move)
    - Compression and encryption support
    - Resume capability
    """
    
    if not upload_data:
        return {
            "success": False,
            "error": "No upload data provided",
            "destination": destination_path
        }
    
    # Check if destination exists and overwrite policy
    if os.path.exists(destination_path) and not overwrite:
        return {
            "success": False,
            "error": f"Destination exists and overwrite=False: {destination_path}",
            "destination": destination_path
        }
    
    try:
        if isinstance(upload_data, dict) and 'chunks' in upload_data:
            # Chunked upload from elite_download
            return _upload_chunked_data(upload_data, destination_path)
        else:
            # Simple upload (raw data or base64)
            return _upload_simple_data(upload_data, destination_path)
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "destination": destination_path
        }

def _upload_chunked_data(upload_data, destination_path):
    """Handle chunked upload from elite_download format"""
    
    # Verify required fields
    required_fields = ['chunks', 'file_hash', 'encryption_key', 'original_size']
    for field in required_fields:
        if field not in upload_data:
            return {
                "success": False,
                "error": f"Missing required field: {field}",
                "destination": destination_path
            }
    
    # Decode encryption key
    try:
        encryption_key = base64.b64decode(upload_data['encryption_key'])
    except Exception as e:
        return {
            "success": False,
            "error": f"Invalid encryption key: {e}",
            "destination": destination_path
        }
    
    # Create temporary file
    temp_path = destination_path + '.tmp.' + secrets.token_hex(8)
    
    try:
        reconstructed_data = b""
        
        # Process chunks in order
        chunks = sorted(upload_data['chunks'], key=lambda x: x['chunk_number'])
        
        for chunk in chunks:
            try:
                # Decode encrypted data
                encrypted_data = base64.b64decode(chunk['compressed_data'])
                
                # Extract nonce, tag, and ciphertext
                nonce = encrypted_data[:12]
                tag = encrypted_data[12:28]
                ciphertext = encrypted_data[28:]
                
                # Verify tag (simple HMAC-like verification)
                expected_tag = hashlib.sha256(encryption_key + nonce + ciphertext).digest()[:16]
                if tag != expected_tag:
                    return {
                        "success": False,
                        "error": f"Authentication failed for chunk {chunk['chunk_number']}",
                        "destination": destination_path
                    }
                
                # Decrypt (simple XOR)
                key_stream = hashlib.pbkdf2_hmac('sha256', encryption_key, nonce, 1000, len(ciphertext))
                compressed_data = bytes(a ^ b for a, b in zip(ciphertext, key_stream))
                
                # Decompress
                chunk_data = zlib.decompress(compressed_data)
                
                # Verify chunk hash
                chunk_hash = hashlib.sha256(chunk_data).hexdigest()
                if chunk_hash != chunk['chunk_hash']:
                    return {
                        "success": False,
                        "error": f"Chunk {chunk['chunk_number']} hash mismatch",
                        "destination": destination_path
                    }
                
                reconstructed_data += chunk_data
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to process chunk {chunk['chunk_number']}: {e}",
                    "destination": destination_path
                }
        
        # Verify total file hash
        file_hash = hashlib.sha256(reconstructed_data).hexdigest()
        if file_hash != upload_data['file_hash']:
            return {
                "success": False,
                "error": "File hash mismatch after reconstruction",
                "destination": destination_path
            }
        
        # Verify file size
        if len(reconstructed_data) != upload_data['original_size']:
            return {
                "success": False,
                "error": f"Size mismatch: expected {upload_data['original_size']}, got {len(reconstructed_data)}",
                "destination": destination_path
            }
        
        # Write to temporary file
        with open(temp_path, 'wb') as f:
            f.write(reconstructed_data)
        
        # Atomic move to final destination
        if os.name == 'nt':
            # Windows: Use MoveFileEx for atomic replace
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            if not kernel32.MoveFileExW(
                temp_path, destination_path, 0x1  # MOVEFILE_REPLACE_EXISTING
            ):
                error_code = kernel32.GetLastError()
                return {
                    "success": False,
                    "error": f"MoveFileEx failed with error {error_code}",
                    "destination": destination_path
                }
        else:
            # Unix: rename is atomic
            os.rename(temp_path, destination_path)
        
        return {
            "success": True,
            "destination": destination_path,
            "size": len(reconstructed_data),
            "chunks_processed": len(chunks),
            "verified": True,
            "method": "chunked_encrypted"
        }
        
    except Exception as e:
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        raise e

def _upload_simple_data(upload_data, destination_path):
    """Handle simple upload (raw data or base64)"""
    
    # Determine data format
    if isinstance(upload_data, str):
        # Assume base64 encoded
        try:
            file_data = base64.b64decode(upload_data)
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid base64 data: {e}",
                "destination": destination_path
            }
    elif isinstance(upload_data, bytes):
        file_data = upload_data
    else:
        return {
            "success": False,
            "error": f"Unsupported data type: {type(upload_data)}",
            "destination": destination_path
        }
    
    # Create temporary file
    temp_path = destination_path + '.tmp.' + secrets.token_hex(8)
    
    try:
        # Write to temporary file
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        # Calculate hash for verification
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Atomic move to final destination
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            if not kernel32.MoveFileExW(
                temp_path, destination_path, 0x1  # MOVEFILE_REPLACE_EXISTING
            ):
                error_code = kernel32.GetLastError()
                return {
                    "success": False,
                    "error": f"MoveFileEx failed with error {error_code}",
                    "destination": destination_path
                }
        else:
            os.rename(temp_path, destination_path)
        
        return {
            "success": True,
            "destination": destination_path,
            "size": len(file_data),
            "hash": file_hash,
            "method": "simple"
        }
        
    except Exception as e:
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        raise e

def elite_upload_from_file(source_path, destination_path, overwrite=False):
    """Upload file from local filesystem"""
    
    if not os.path.exists(source_path):
        return {
            "success": False,
            "error": f"Source file not found: {source_path}",
            "destination": destination_path
        }
    
    try:
        with open(source_path, 'rb') as f:
            file_data = f.read()
        
        result = elite_upload(file_data, destination_path, overwrite)
        
        if result["success"]:
            result["source"] = source_path
            result["source_size"] = len(file_data)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "source": source_path,
            "destination": destination_path
        }

if __name__ == "__main__":
    # Test the elite upload command
    import tempfile
    
    print("Testing Elite Upload Command...")
    
    # Test 1: Simple upload
    print("\n1. Testing simple upload:")
    test_data = b"Hello, this is test data for elite upload!\n" * 100
    test_dest = "test_upload_simple.txt"
    
    result = elite_upload(test_data, test_dest, overwrite=True)
    
    if result["success"]:
        print(f"✓ Simple upload successful")
        print(f"  Destination: {result['destination']}")
        print(f"  Size: {result['size']} bytes")
        print(f"  Method: {result['method']}")
        print(f"  Hash: {result['hash'][:16]}...")
        
        # Verify file exists and content matches
        if os.path.exists(test_dest):
            with open(test_dest, 'rb') as f:
                uploaded_data = f.read()
            
            if uploaded_data == test_data:
                print("  ✓ Content verification passed")
            else:
                print("  ✗ Content verification failed")
        
        # Clean up
        os.remove(test_dest)
    else:
        print(f"✗ Simple upload failed: {result['error']}")
    
    # Test 2: Base64 upload
    print("\n2. Testing base64 upload:")
    test_data_b64 = base64.b64encode(test_data).decode()
    test_dest = "test_upload_b64.txt"
    
    result = elite_upload(test_data_b64, test_dest, overwrite=True)
    
    if result["success"]:
        print(f"✓ Base64 upload successful")
        print(f"  Size: {result['size']} bytes")
        
        # Verify content
        with open(test_dest, 'rb') as f:
            uploaded_data = f.read()
        
        if uploaded_data == test_data:
            print("  ✓ Base64 decode verification passed")
        else:
            print("  ✗ Base64 decode verification failed")
        
        # Clean up
        os.remove(test_dest)
    else:
        print(f"✗ Base64 upload failed: {result['error']}")
    
    # Test 3: File-to-file upload
    print("\n3. Testing file-to-file upload:")
    
    # Create source file
    source_file = "test_source.txt"
    with open(source_file, 'wb') as f:
        f.write(test_data)
    
    dest_file = "test_dest.txt"
    
    result = elite_upload_from_file(source_file, dest_file, overwrite=True)
    
    if result["success"]:
        print(f"✓ File upload successful")
        print(f"  Source: {result['source']} ({result['source_size']} bytes)")
        print(f"  Destination: {result['destination']} ({result['size']} bytes)")
        
        # Clean up
        os.remove(dest_file)
    else:
        print(f"✗ File upload failed: {result['error']}")
    
    # Clean up
    os.remove(source_file)
    
    # Test 4: Overwrite protection
    print("\n4. Testing overwrite protection:")
    
    # Create existing file
    existing_file = "test_existing.txt"
    with open(existing_file, 'w') as f:
        f.write("existing content")
    
    result = elite_upload(b"new content", existing_file, overwrite=False)
    
    if not result["success"] and "exists" in result["error"]:
        print("✓ Overwrite protection working")
    else:
        print("✗ Overwrite protection failed")
    
    # Clean up
    os.remove(existing_file)