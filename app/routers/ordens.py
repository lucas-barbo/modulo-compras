from fastapi import APIRouter

from app.core.deps import CurrentUser, DBSession
from app.schemas.ordem import (
    OrdemCompraDetalheResponse,
    OrdemCompraListResponse,
    ReceberOrdemCompraRequest,
    ReceberOrdemCompraResponse,
)
from app.services import compras_service

router = APIRouter(
    prefix="/compras/ordens",
    tags=["Ordens de Compra"],
)


@router.get("", response_model=OrdemCompraListResponse, summary="Listar ordens de compra")
async def list_ordens(
    _: CurrentUser,
    db: DBSession,
    page: int = 1,
    size: int = 10,
    status_filtro: str | None = None,
):
    return compras_service.list_ordens(db, page, size, status_filtro)


@router.get("/{ordem_id}", response_model=OrdemCompraDetalheResponse, summary="Detalhar ordem de compra")
async def get_ordem(ordem_id: int, _: CurrentUser, db: DBSession):
    return compras_service.get_ordem(db, ordem_id)


@router.post(
    "/{ordem_id}/receber",
    response_model=ReceberOrdemCompraResponse,
    summary="Registrar recebimento da ordem de compra",
)
async def receive_order(
    ordem_id: int,
    payload: ReceberOrdemCompraRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    return compras_service.receive_order(db, ordem_id, payload, current_user.get("token"))
