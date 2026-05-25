from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.fornecedor import (
    FornecedorCreate,
    FornecedorListResponse,
    FornecedorResponse,
    FornecedorUpdate,
)
from app.services import compras_service

router = APIRouter(
    prefix="/compras/fornecedores",
    tags=["Fornecedores"],
)


@router.get("", response_model=FornecedorListResponse, summary="Listar fornecedores")
async def list_fornecedores(_: CurrentUser, db: DBSession, page: int = 1, size: int = 10):
    return compras_service.list_fornecedores(db, page, size)


@router.post(
    "",
    response_model=FornecedorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar fornecedor",
)
async def create_fornecedor(payload: FornecedorCreate, _: CurrentUser, db: DBSession):
    return compras_service.create_fornecedor(db, payload)


@router.get("/{fornecedor_id}", response_model=FornecedorResponse, summary="Detalhar fornecedor")
async def get_fornecedor(fornecedor_id: int, _: CurrentUser, db: DBSession):
    return compras_service.get_fornecedor(db, fornecedor_id)


@router.put("/{fornecedor_id}", response_model=FornecedorResponse, summary="Atualizar fornecedor")
async def update_fornecedor(
    fornecedor_id: int,
    payload: FornecedorUpdate,
    _: CurrentUser,
    db: DBSession,
):
    return compras_service.update_fornecedor(db, fornecedor_id, payload)


@router.delete(
    "/{fornecedor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir fornecedor",
)
async def delete_fornecedor(fornecedor_id: int, _: CurrentUser, db: DBSession):
    return compras_service.delete_fornecedor(db, fornecedor_id)
