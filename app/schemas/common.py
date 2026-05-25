from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Página atual")
    size: int = Field(default=10, ge=1, le=100, description="Itens por página")


class PaginatedResponse(BaseModel):
    page: int
    size: int
    total: int
    pages: int


class MessageResponse(BaseModel):
    message: str
