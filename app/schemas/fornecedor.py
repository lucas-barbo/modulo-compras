from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import PaginatedResponse


class FornecedorBase(BaseModel):
    cnpj: str = Field(..., min_length=14, max_length=18, examples=["12.345.678/0001-99"])
    razao_social: str = Field(..., min_length=3, max_length=255)
    email: EmailStr | None = None
    prazo_entrega: int = Field(..., ge=0, le=365)


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorUpdate(FornecedorBase):
    pass


class FornecedorResponse(FornecedorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class FornecedorListResponse(PaginatedResponse):
    items: list[FornecedorResponse]
