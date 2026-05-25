import httpx
from fastapi import status

from app.core.config import get_settings
from app.core.errors import api_error


def _post_gateway(url: str, payload: dict, token: str | None = None) -> dict:
    settings = get_settings()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.request_timeout,
        )
    except httpx.HTTPError as exc:
        raise api_error(
            status.HTTP_502_BAD_GATEWAY,
            f"Falha de comunicação com serviço externo: {exc}",
            "FALHA_INTEGRACAO",
        )

    if response.status_code >= 400:
        detail = response.text or "Serviço externo retornou erro."
        raise api_error(
            status.HTTP_502_BAD_GATEWAY,
            detail,
            "FALHA_INTEGRACAO",
        )

    if response.content:
        try:
            return response.json()
        except ValueError:
            return {"status": "ok", "raw": response.text}
    return {"status": "ok"}


def notificar_estoque(payload: dict, token: str | None = None) -> dict:
    return _post_gateway(get_settings().estoque_entrada_url, payload, token)


def notificar_financeiro(payload: dict, token: str | None = None) -> dict:
    return _post_gateway(get_settings().financeiro_contas_pagar_url, payload, token)
