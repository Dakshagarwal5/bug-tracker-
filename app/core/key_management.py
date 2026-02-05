import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

PRIVATE_KEY_PATH = "keys/private.pem"
PUBLIC_KEY_PATH = "keys/public.pem"

def ensure_keys_exist(private_path: str = PRIVATE_KEY_PATH, public_path: str = PUBLIC_KEY_PATH) -> None:
    """
    Ensures that RSA keys exist at the specified paths.
    If they do not exist, they are generated.
    """
    # Ensure keys directory exists
    key_dir = os.path.dirname(private_path)
    if key_dir and not os.path.exists(key_dir):
        os.makedirs(key_dir, mode=0o700)
        logger.info(f"Created key directory: {key_dir}")

    if not os.path.exists(private_path) or not os.path.exists(public_path):
        logger.warning(f"Keys missing at {private_path} or {public_path}. Generating new RSA keys...")
        _generate_keys(private_path, public_path)
    else:
        logger.info("RSA keys found on disk.")
        # Optional: Validate them?
        try:
            load_keys(private_path, public_path)
        except Exception as e:
             logger.error(f"Existing keys are invalid: {e}. Regenerating...")
             _generate_keys(private_path, public_path)

def _generate_keys(private_path: str, public_path: str) -> None:
    """
    Generates a new 2048-bit RSA key pair and saves them to disk.
    """
    try:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Save private key
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(private_path, "wb") as f:
            f.write(pem_private)
        
        # Save public key
        public_key = private_key.public_key()
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(public_path, "wb") as f:
            f.write(pem_public)
            
        logger.info(f"Successfully generated keys at {private_path} and {public_path}")
        
    except Exception as e:
        logger.critical(f"Failed to generate keys: {e}")
        raise RuntimeError(f"Critical: Could not generate RSA keys. {e}")

def load_keys(private_path: str, public_path: str) -> dict:
    """
    Loads the private and public keys from disk and returns them as bytes.
    Validates that they are valid PEMs.
    """
    try:
        with open(private_path, "rb") as f:
            private_bytes = f.read()
            
        with open(public_path, "rb") as f:
            public_bytes = f.read()
            
        # Validate by loading them with cryptography
        serialization.load_pem_private_key(private_bytes, password=None, backend=default_backend())
        serialization.load_pem_public_key(public_bytes, backend=default_backend())
        
        return {
            "private_key": private_bytes.decode('utf-8'),
            "public_key": public_bytes.decode('utf-8')
        }
    except FileNotFoundError as e:
        logger.error(f"Key file not found: {e}")
        raise RuntimeError("Keys not found. Ensure ensure_keys_exist() is called.")
    except Exception as e:
        logger.critical(f"Failed to load/validate keys: {e}")
        raise RuntimeError(f"Invalid RSA Keys: {e}")
