from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import os
import base64

def generate_aes_key(length=32):
    """
    Generate a random AES key.

    :param length: Length of the key in bytes (16 for AES-128, 24 for AES-192, 32 for AES-256)
    :return: Base64-encoded AES key
    """
    if length not in (16, 24, 32):
        raise ValueError("Invalid key length. Use 16, 24, or 32 bytes.")
    
    # Generate a random key
    key = os.urandom(length)
    
    # Base64-encode the key
    base64_key = base64.urlsafe_b64encode(key).decode()
    
    # Optionally, base64 encode it again before outputting
    encoded_key = base64.b64encode(base64_key.encode()).decode()
    
    return encoded_key

