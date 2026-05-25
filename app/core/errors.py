from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

DEFAULT_ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "REQUISICAO_INVALIDA",
    status.HTTP_401_UNAUTHORIZED: "NAO_AUTENTICADO",
    status.HTTP_403_FORBIDDEN: "ACESSO_NEGADO",
    status.HTTP_404_NOT_FOUND: "NAO_ENCONTRADO",
    status.HTTP_409_CONFLICT: "CONFLITO",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "DADOS_INVALIDOS",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "ERRO_INTERNO",
    status.HTTP_502_BAD_GATEWAY: "ERRO_INTEGRACAO",
}


def api_error(status_code: int, detail: str, code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"detail": detail, "code": code},
    )


def register_exception_handlers(app) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "detail" in detail and "code" in detail:
            content = detail
        else:
            content = {
                "detail": str(detail),
                "code": DEFAULT_ERROR_CODES.get(exc.status_code, "ERRO_HTTP"),
            }
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc: RequestValidationError):
        first_error = exc.errors()[0]
        location = ".".join(str(part) for part in first_error["loc"] if part != "body")
        message = first_error["msg"]
        if location:
            message = f"{location}: {message}"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": message, "code": "DADOS_INVALIDOS"},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_, __):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Ocorreu um erro interno no módulo de compras.",
                "code": "ERRO_INTERNO",
            },
        )
