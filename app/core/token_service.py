from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple
from uuid import uuid4

from jose import jwt, JWTError

from app.core.config import settings
from app.core.exceptions import AuthenticationFailedException
from app.core.rate_limit import redis_client


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def _get_session_version(user_id: int) -> int:
    version = await redis_client.get(f"session_version:{user_id}")
    return int(version) if version else 1


async def _bump_session_version(user_id: int) -> None:
    await redis_client.incr(f"session_version:{user_id}")


async def _set_active_refresh(user_id: int, jti: str, exp_seconds: int) -> None:
    await redis_client.set(f"refresh_active:{user_id}", jti, ex=exp_seconds)


async def _get_active_refresh(user_id: int) -> str | None:
    return await redis_client.get(f"refresh_active:{user_id}")


async def blacklist_jti(jti: str, exp_seconds: int) -> None:
    await redis_client.set(f"blacklist:{jti}", "revoked", ex=exp_seconds)


async def is_blacklisted(jti: str) -> bool:
    return await redis_client.exists(f"blacklist:{jti}") == 1


def _encode_token(payload: Dict[str, Any], expires_delta: timedelta) -> Tuple[str, int]:
    exp = _now() + expires_delta
    payload_with_exp = {**payload, "exp": exp}
    if not settings.PRIVATE_KEY:
        raise AuthenticationFailedException("Server misconfigured: missing signing key")
    token = jwt.encode(payload_with_exp, settings.PRIVATE_KEY, algorithm=settings.ALGORITHM)
    ttl = int(expires_delta.total_seconds())
    return token, ttl


async def generate_token_pair(user_id: int) -> Dict[str, str]:
    session_version = await _get_session_version(user_id)
    access_jti = str(uuid4())
    refresh_jti = str(uuid4())

    access_token, _ = _encode_token(
        {"sub": str(user_id), "type": "access", "jti": access_jti, "ver": session_version},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token, refresh_ttl = _encode_token(
        {"sub": str(user_id), "type": "refresh", "jti": refresh_jti, "ver": session_version},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    await _set_active_refresh(user_id, refresh_jti, refresh_ttl)
    return {"access_token": access_token, "refresh_token": refresh_token}


async def decode_and_validate(token: str, expected_type: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.PUBLIC_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
    except JWTError:
        raise AuthenticationFailedException("Could not validate credentials")

    if payload.get("type") != expected_type:
        raise AuthenticationFailedException("Invalid token type")

    jti = payload.get("jti")
    if not jti or await is_blacklisted(jti):
        raise AuthenticationFailedException("Token has been revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationFailedException("Invalid token: missing subject")

    # Session version check for logout-all
    current_version = await _get_session_version(int(user_id))
    if payload.get("ver") != current_version:
        raise AuthenticationFailedException("Session has been revoked")

    return payload


async def rotate_refresh_token(refresh_token: str) -> Dict[str, str]:
    payload = await decode_and_validate(refresh_token, expected_type="refresh")
    user_id = int(payload["sub"])

    active_jti = await _get_active_refresh(user_id)
    if not active_jti or active_jti != payload.get("jti"):
        raise AuthenticationFailedException("Refresh token is no longer valid")

    # Revoke old refresh token
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        ttl_seconds = max(int(exp_timestamp - datetime.now(tz=timezone.utc).timestamp()), 0)
        await blacklist_jti(payload["jti"], ttl_seconds)

    new_pair = await generate_token_pair(user_id)
    return new_pair


async def logout(refresh_token: str) -> None:
    payload = await decode_and_validate(refresh_token, expected_type="refresh")
    user_id = int(payload["sub"])
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        ttl_seconds = max(int(exp_timestamp - datetime.now(tz=timezone.utc).timestamp()), 0)
        await blacklist_jti(payload["jti"], ttl_seconds)
    await redis_client.delete(f"refresh_active:{user_id}")


async def logout_all_devices(user_id: int) -> None:
    await _bump_session_version(user_id)
    await redis_client.delete(f"refresh_active:{user_id}")
