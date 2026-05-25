from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.solicitacao import (
    SolicitacaoCompraCreate,
    SolicitacaoCompraResponse,
    SolicitacaoListResponse,
)
from app.services import compras_service

router = APIRouter(
    prefix="/compras/solicitacoes",
    tags=["Solicitações"],
)


@router.get("", response_model=SolicitacaoListResponse, summary="Listar solicitações")
async def list_solicitacoes(_: CurrentUser, db: DBSession, page: int = 1, size: int = 10):
    return compras_service.list_solicitacoes(db, page, size)


@router.post(
    "",
    response_model=SolicitacaoCompraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar solicitação de compra",
)
async def create_solicitacao(payload: SolicitacaoCompraCreate, _: CurrentUser, db: DBSession):
    return compras_service.create_solicitacao(db, payload)
