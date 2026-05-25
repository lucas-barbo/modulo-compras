import httpx
from fastapi import status

from app.core.config import get_settings
from app.core.errors import api_error


def verify_token_with_core(token: str) -> dict:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"token": token}

    try:
        response = httpx.post(
            settings.auth_verify_url,
            json=payload,
            headers=headers,
            timeout=settings.request_timeout,
        )
    except httpx.HTTPError as exc:
        raise api_error(
            status.HTTP_502_BAD_GATEWAY,
            f"Não foi possível validar o token no CORE: {exc}",
            "CORE_INDISPONIVEL",
        )

    if response.status_code >= 400:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "Token JWT inválido ou expirado.",
            "TOKEN_INVALIDO",
        )

    data = response.json() if response.content else {}
    if isinstance(data, dict):
        return data
    return {"valid": True}
