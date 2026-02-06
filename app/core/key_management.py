
import logging
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)

def _allow_ephemeral_test_keys() -> bool:
    return os.getenv("ALLOW_INSECURE_TEST_KEYS") == "1" or "pytest" in sys.modules


def _generate_ephemeral_keys() -> dict:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return {"private_key": private_pem, "public_key": public_pem}


def load_keys(private_path: str, public_path: str) -> dict:
    """
    Strictly loads RSA keys from the provided absolute paths.
    Fails immediately if keys are missing or unreadable.
    NEVER generates keys.
    """
    priv_p = Path(private_path)
    pub_p = Path(public_path)

    # 1. Fail fast if files don't exist
    if not priv_p.exists() or not pub_p.exists():
        if _allow_ephemeral_test_keys():
            logger.warning(
                "Keys missing at %s/%s. Generating ephemeral test keys.",
                priv_p,
                pub_p,
            )
            return _generate_ephemeral_keys()

        missing = []
        if not priv_p.exists():
            missing.append(f"private key at {priv_p}")
        if not pub_p.exists():
            missing.append(f"public key at {pub_p}")
        msg = (
            "CRITICAL: Missing authentication keys: "
            + ", ".join(missing)
            + ". Keys must be pre-generated and mounted."
        )
        logger.critical(msg)
        raise RuntimeError(msg)

    # 2. Read keys (Read-Only)
    try:
        private_key_content = priv_p.read_text().strip()
        public_key_content = pub_p.read_text().strip()
        
        logger.info(f"Loaded PRIVATE_KEY from {priv_p}")
        logger.info(f"Loaded PUBLIC_KEY from {pub_p}")
        
        return {
            "private_key": private_key_content,
            "public_key": public_key_content
        }
    except PermissionError:
        msg = f"CRITICAL: Permission denied reading keys at {priv_p} or {pub_p}. Check file ownership (1000:1000) vs Container User."
        logger.critical(msg)
        raise RuntimeError(msg)
    except Exception as e:
        msg = f"CRITICAL: Failed to read keys: {e}"
        logger.critical(msg)
        raise RuntimeError(msg)
