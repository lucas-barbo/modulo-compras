from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.cotacao import CotacaoCreate, CotacaoListResponse, CotacaoResponse
from app.schemas.ordem import OrdemCompraDetalheResponse
from app.services import compras_service

router = APIRouter(
    prefix="/compras/cotacoes",
    tags=["Cotações"],
)


@router.get("", response_model=CotacaoListResponse, summary="Listar cotações")
async def list_cotacoes(
    _: CurrentUser,
    db: DBSession,
    page: int = 1,
    size: int = 10,
    status_filtro: str | None = None,
):
    return compras_service.list_cotacoes(db, page, size, status_filtro)


@router.post(
    "",
    response_model=CotacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cotação",
)
async def create_cotacao(payload: CotacaoCreate, _: CurrentUser, db: DBSession):
    return compras_service.create_cotacao(db, payload)


@router.post(
    "/{cotacao_id}/aprovar",
    response_model=OrdemCompraDetalheResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovar cotação e gerar ordem de compra",
)
async def approve_cotacao(cotacao_id: int, _: CurrentUser, db: DBSession):
    return compras_service.approve_cotacao(db, cotacao_id)
