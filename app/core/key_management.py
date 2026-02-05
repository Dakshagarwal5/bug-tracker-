
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_keys(private_path: str, public_path: str) -> dict:
    """
    Strictly loads RSA keys from the provided absolute paths.
    Fails immediately if keys are missing or unreadable.
    NEVER generates keys.
    """
    priv_p = Path(private_path)
    pub_p = Path(public_path)

    # 1. Fail fast if files don't exist
    if not priv_p.exists():
        msg = f"CRITICAL: Private key missing at {priv_p}. Keys must be pre-generated and mounted."
        logger.critical(msg)
        raise RuntimeError(msg)
        
    if not pub_p.exists():
        msg = f"CRITICAL: Public key missing at {pub_p}. Keys must be pre-generated and mounted."
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
