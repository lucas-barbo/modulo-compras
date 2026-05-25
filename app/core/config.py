from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Modulo Compras"
    app_version: str = "1.0.0"
    app_description: str = (
        "Microserviço de compras do ERP responsável por fornecedores, "
        "solicitações, cotações e ordens de compra."
    )
    api_prefix: str = "/compras"
    database_url: str = "sqlite:///./compras.db"
    core_base_url: str = "http://localhost:8000"
    cors_origins: str = Field(default="http://localhost:3000")
    request_timeout: float = 5.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def auth_verify_url(self) -> str:
        return f"{self.core_base_url.rstrip('/')}/auth/verify"

    @property
    def estoque_entrada_url(self) -> str:
        return f"{self.core_base_url.rstrip('/')}/estoque/movimentacoes/entrada"

    @property
    def financeiro_contas_pagar_url(self) -> str:
        return f"{self.core_base_url.rstrip('/')}/financeiro/contas-pagar"


@lru_cache
def get_settings() -> Settings:
    return Settings()
