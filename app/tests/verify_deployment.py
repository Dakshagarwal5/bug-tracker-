
import sys
import os
import logging

# Ensure we can import app modules
sys.path.append(os.getcwd())

from app.core.key_management import ensure_keys_exist, load_keys
from app.core.config import settings
from app.core import security
from jose import jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_deployment():
    logger.info("1. Testing Key Generation and Loading...")
    try:
        # This should generate keys if missing
        ensure_keys_exist("keys/test_private.pem", "keys/test_public.pem")
        keys = load_keys("keys/test_private.pem", "keys/test_public.pem")
        
        if not keys["private_key"].startswith("-----BEGIN PRIVATE KEY-----"):
            raise ValueError("Private key has invalid header")
        if not keys["public_key"].startswith("-----BEGIN PUBLIC KEY-----"):
            raise ValueError("Public key has invalid header")
            
        logger.info("   [PASS] Keys generated and loaded invalid PEM format.")
        
        # Clean up test keys
        # os.remove("keys/test_private.pem")
        # os.remove("keys/test_public.pem")
    except Exception as e:
        logger.error(f"   [FAIL] Key management failed: {e}")
        return

    logger.info("2. Testing Config Integration...")
    try:
        # Force reload to use real keys
        settings.load_keys()
        if not settings.PRIVATE_KEY:
            raise ValueError("Settings failed to load PRIVATE_KEY")
        logger.info("   [PASS] Settings loaded keys successfully.")
    except Exception as e:
        logger.error(f"   [FAIL] Config loading failed: {e}")
        return

    logger.info("3. Testing JWT Signing (RS256)...")
    try:
        user_id = 123
        token = security.create_access_token(user_id)
        logger.info(f"   Generated Token: {token[:20]}...")
        
        # Decode
        payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=["RS256"])
        if payload["sub"] != str(user_id):
            raise ValueError(f"Subject mismatch: {payload['sub']} != {user_id}")
            
        logger.info("   [PASS] JWT Signed and Verified successfully with RS256.")
    except Exception as e:
        logger.error(f"   [FAIL] JWT operations failed: {e}")
        return

    logger.info("\nSUCCESS: All systems operational.")

if __name__ == "__main__":
    verify_deployment()
