from datetime import timedelta
from decimal import Decimal

from fastapi import Response, status
from sqlalchemy.orm import Session, joinedload

from app.core.errors import api_error
from app.core.utils import compute_pages, quantize_money, utc_now
from app.models.models import Cotacao, Fornecedor, HistoricoStatusOC, OrdemCompra, SolicitacaoCompra
from app.schemas.cotacao import CotacaoCreate, CotacaoResponse
from app.schemas.fornecedor import FornecedorCreate, FornecedorResponse, FornecedorUpdate
from app.schemas.ordem import (
    IntegracaoResponse,
    OrdemCompraDetalheResponse,
    OrdemCompraResponse,
    ReceberOrdemCompraRequest,
    ReceberOrdemCompraResponse,
)
from app.schemas.solicitacao import SolicitacaoCompraCreate, SolicitacaoCompraResponse
from app.services import integration_client

STATUS_COTACAO_VALIDOS = {"pendente", "aprovada", "recusada"}
STATUS_OC_VALIDOS = {"aberta", "parcial", "encerrada", "cancelada"}


def _paginate(query, page: int, size: int):
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total, compute_pages(total, size)


def _get_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor:
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise api_error(status.HTTP_404_NOT_FOUND, "Fornecedor não encontrado.", "FORNECEDOR_NAO_ENCONTRADO")
    return fornecedor


def _get_solicitacao(db: Session, solicitacao_id: int) -> SolicitacaoCompra:
    solicitacao = db.query(SolicitacaoCompra).filter(SolicitacaoCompra.id == solicitacao_id).first()
    if not solicitacao:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            "Solicitação de compra não encontrada.",
            "SOLICITACAO_NAO_ENCONTRADA",
        )
    return solicitacao


def _get_cotacao(db: Session, cotacao_id: int) -> Cotacao:
    cotacao = (
        db.query(Cotacao)
        .options(joinedload(Cotacao.fornecedor), joinedload(Cotacao.solicitacao))
        .filter(Cotacao.id == cotacao_id)
        .first()
    )
    if not cotacao:
        raise api_error(status.HTTP_404_NOT_FOUND, "Cotação não encontrada.", "COTACAO_NAO_ENCONTRADA")
    return cotacao


def _get_ordem(db: Session, ordem_id: int) -> OrdemCompra:
    ordem = (
        db.query(OrdemCompra)
        .options(
            joinedload(OrdemCompra.fornecedor),
            joinedload(OrdemCompra.cotacao).joinedload(Cotacao.solicitacao),
            joinedload(OrdemCompra.historico),
        )
        .filter(OrdemCompra.id == ordem_id)
        .first()
    )
    if not ordem:
        raise api_error(status.HTTP_404_NOT_FOUND, "Ordem de compra não encontrada.", "ORDEM_NAO_ENCONTRADA")
    return ordem


def list_fornecedores(db: Session, page: int, size: int):
    query = db.query(Fornecedor).order_by(Fornecedor.razao_social.asc())
    items, total, pages = _paginate(query, page, size)
    return {
        "items": [FornecedorResponse.model_validate(item) for item in items],
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
    }


def create_fornecedor(db: Session, payload: FornecedorCreate) -> FornecedorResponse:
    existing = db.query(Fornecedor).filter(Fornecedor.cnpj == payload.cnpj).first()
    if existing:
        raise api_error(status.HTTP_409_CONFLICT, "Já existe fornecedor com este CNPJ.", "CNPJ_DUPLICADO")

    fornecedor = Fornecedor(**payload.model_dump())
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return FornecedorResponse.model_validate(fornecedor)


def get_fornecedor(db: Session, fornecedor_id: int) -> FornecedorResponse:
    return FornecedorResponse.model_validate(_get_fornecedor(db, fornecedor_id))


def update_fornecedor(db: Session, fornecedor_id: int, payload: FornecedorUpdate) -> FornecedorResponse:
    fornecedor = _get_fornecedor(db, fornecedor_id)
    duplicate = (
        db.query(Fornecedor)
        .filter(Fornecedor.cnpj == payload.cnpj, Fornecedor.id != fornecedor_id)
        .first()
    )
    if duplicate:
        raise api_error(status.HTTP_409_CONFLICT, "Já existe fornecedor com este CNPJ.", "CNPJ_DUPLICADO")

    for field, value in payload.model_dump().items():
        setattr(fornecedor, field, value)

    db.commit()
    db.refresh(fornecedor)
    return FornecedorResponse.model_validate(fornecedor)


def delete_fornecedor(db: Session, fornecedor_id: int) -> Response:
    fornecedor = _get_fornecedor(db, fornecedor_id)

    possui_vinculos = (
        db.query(Cotacao).filter(Cotacao.fornecedor_id == fornecedor.id).first()
        or db.query(OrdemCompra).filter(OrdemCompra.fornecedor_id == fornecedor.id).first()
    )
    if possui_vinculos:
        raise api_error(
            status.HTTP_409_CONFLICT,
            "Fornecedor possui vínculos com cotações ou ordens de compra.",
            "FORNECEDOR_EM_USO",
        )

    db.delete(fornecedor)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def list_solicitacoes(db: Session, page: int, size: int):
    query = db.query(SolicitacaoCompra).order_by(SolicitacaoCompra.criado_em.desc())
    items, total, pages = _paginate(query, page, size)
    return {
        "items": [SolicitacaoCompraResponse.from_model(item) for item in items],
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
    }


def create_solicitacao(db: Session, payload: SolicitacaoCompraCreate) -> SolicitacaoCompraResponse:
    solicitacao = SolicitacaoCompra(**payload.model_dump())
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return SolicitacaoCompraResponse.from_model(solicitacao)


def list_cotacoes(db: Session, page: int, size: int, status_filtro: str | None = None):
    query = db.query(Cotacao).options(joinedload(Cotacao.fornecedor), joinedload(Cotacao.solicitacao))

    if status_filtro:
        if status_filtro not in STATUS_COTACAO_VALIDOS:
            raise api_error(status.HTTP_400_BAD_REQUEST, "Status de cotação inválido.", "STATUS_INVALIDO")
        query = query.filter(Cotacao.status == status_filtro)

    query = query.order_by(Cotacao.criado_em.desc())
    items, total, pages = _paginate(query, page, size)
    return {
        "items": [CotacaoResponse.from_model(item) for item in items],
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
    }


def create_cotacao(db: Session, payload: CotacaoCreate) -> CotacaoResponse:
    solicitacao = _get_solicitacao(db, payload.solicitacao_id)
    fornecedor = _get_fornecedor(db, payload.fornecedor_id)

    quantidade = payload.quantidade or solicitacao.quantidade
    if quantidade != solicitacao.quantidade:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "A quantidade da cotação deve ser igual à quantidade da solicitação.",
            "QUANTIDADE_INVALIDA",
        )

    existing = (
        db.query(Cotacao)
        .filter(
            Cotacao.solicitacao_id == payload.solicitacao_id,
            Cotacao.fornecedor_id == payload.fornecedor_id,
        )
        .first()
    )
    if existing:
        raise api_error(
            status.HTTP_409_CONFLICT,
            "Já existe cotação deste fornecedor para a solicitação informada.",
            "COTACAO_DUPLICADA",
        )

    cotacao = Cotacao(
        solicitacao_id=solicitacao.id,
        fornecedor_id=fornecedor.id,
        preco_unitario=payload.preco_unitario,
        quantidade=quantidade,
    )
    db.add(cotacao)
    db.commit()
    db.refresh(cotacao)
    cotacao = _get_cotacao(db, cotacao.id)
    return CotacaoResponse.from_model(cotacao)


def approve_cotacao(db: Session, cotacao_id: int) -> OrdemCompraDetalheResponse:
    cotacao = _get_cotacao(db, cotacao_id)

    if cotacao.status != "pendente":
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "Apenas cotações pendentes podem ser aprovadas.",
            "COTACAO_JA_PROCESSADA",
        )

    existing_order = db.query(OrdemCompra).filter(OrdemCompra.cotacao_id == cotacao.id).first()
    if existing_order:
        raise api_error(
            status.HTTP_409_CONFLICT,
            "Esta cotação já possui uma ordem de compra associada.",
            "ORDEM_JA_EXISTE",
        )

    cotacao.status = "aprovada"
    (
        db.query(Cotacao)
        .filter(Cotacao.solicitacao_id == cotacao.solicitacao_id, Cotacao.id != cotacao.id)
        .update({"status": "recusada"})
    )

    emissao = utc_now().date()
    previsao = emissao + timedelta(days=cotacao.fornecedor.prazo_entrega)
    ordem = OrdemCompra(
        cotacao_id=cotacao.id,
        fornecedor_id=cotacao.fornecedor_id,
        valor_total=quantize_money(cotacao.valor_total),
        quantidade_recebida=Decimal("0.00"),
        status="aberta",
        data_emissao=emissao,
        data_previsao=previsao,
    )
    db.add(ordem)
    db.flush()

    historico = HistoricoStatusOC(
        ordem_compra_id=ordem.id,
        status_anterior=None,
        status_novo="aberta",
    )
    db.add(historico)
    db.commit()
    return OrdemCompraDetalheResponse.from_model(_get_ordem(db, ordem.id))


def list_ordens(db: Session, page: int, size: int, status_filtro: str | None = None):
    query = db.query(OrdemCompra).options(
        joinedload(OrdemCompra.fornecedor),
        joinedload(OrdemCompra.cotacao).joinedload(Cotacao.solicitacao),
    )

    if status_filtro:
        if status_filtro not in STATUS_OC_VALIDOS:
            raise api_error(status.HTTP_400_BAD_REQUEST, "Status da ordem inválido.", "STATUS_INVALIDO")
        query = query.filter(OrdemCompra.status == status_filtro)

    query = query.order_by(OrdemCompra.criado_em.desc())
    items, total, pages = _paginate(query, page, size)
    return {
        "items": [OrdemCompraResponse.from_model(item) for item in items],
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
    }


def get_ordem(db: Session, ordem_id: int) -> OrdemCompraDetalheResponse:
    return OrdemCompraDetalheResponse.from_model(_get_ordem(db, ordem_id))


def receive_order(
    db: Session,
    ordem_id: int,
    payload: ReceberOrdemCompraRequest,
    token: str | None,
) -> ReceberOrdemCompraResponse:
    ordem = _get_ordem(db, ordem_id)

    if ordem.status not in {"aberta", "parcial"}:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "Somente ordens abertas ou parciais podem receber mercadoria.",
            "ORDEM_NAO_RECEBIVEL",
        )

    quantidade_total = Decimal(ordem.cotacao.quantidade)
    quantidade_recebida = Decimal(ordem.quantidade_recebida)
    quantidade_lote = Decimal(payload.quantidade_recebida)
    quantidade_restante = quantidade_total - quantidade_recebida

    if quantidade_lote > quantidade_restante:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "Quantidade recebida maior que o saldo pendente da ordem.",
            "QUANTIDADE_EXCEDENTE",
        )

    valor_lote = quantize_money(
        Decimal(ordem.cotacao.preco_unitario) * quantidade_lote
    )
    recebido_em = utc_now()

    estoque_payload = {
        "id_produto": ordem.cotacao.solicitacao.id_produto,
        "produto_nome": ordem.cotacao.solicitacao.produto_nome,
        "quantidade": str(quantidade_lote),
        "fornecedor_id": ordem.fornecedor_id,
        "fornecedor_nome": ordem.fornecedor.razao_social,
        "nota_fiscal": payload.nota_fiscal,
        "ordem_compra_id": ordem.id,
        "recebido_em": recebido_em.replace(tzinfo=None).isoformat() + "Z",
    }
    financeiro_payload = {
        "fornecedor_id": ordem.fornecedor_id,
        "fornecedor_nome": ordem.fornecedor.razao_social,
        "valor": str(valor_lote),
        "vencimento": recebido_em.date().isoformat(),
        "descricao": f"Recebimento da ordem de compra {ordem.id}",
        "documento_referencia": payload.nota_fiscal or f"OC-{ordem.id:06d}",
    }

    try:
        estoque_result = integration_client.notificar_estoque(estoque_payload, token)
        financeiro_result = integration_client.notificar_financeiro(financeiro_payload, token)
    except Exception as exc:
        db.rollback()
        if hasattr(exc, "status_code"):
            raise exc
        raise api_error(
            status.HTTP_502_BAD_GATEWAY,
            f"Falha ao integrar recebimento com os módulos externos: {exc}",
            "FALHA_INTEGRACAO",
        )

    status_anterior = ordem.status
    ordem.quantidade_recebida = quantize_money(quantidade_recebida + quantidade_lote)
    ordem.status = "encerrada" if ordem.quantidade_recebida == quantidade_total else "parcial"

    if ordem.status != status_anterior:
        historico = HistoricoStatusOC(
            ordem_compra_id=ordem.id,
            status_anterior=status_anterior,
            status_novo=ordem.status,
        )
        db.add(historico)

    db.commit()
    ordem = _get_ordem(db, ordem.id)
    return ReceberOrdemCompraResponse(
        message="Recebimento registrado com sucesso.",
        ordem=OrdemCompraDetalheResponse.from_model(ordem),
        integracoes=IntegracaoResponse(
            estoque=estoque_result,
            financeiro=financeiro_result,
        ),
    )
