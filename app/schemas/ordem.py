from decimal import Decimal

from pydantic import BaseModel, Field, condecimal

from app.core.utils import build_order_number, isoformat_date, isoformat_utc
from app.schemas.common import PaginatedResponse

PositiveQuantity = condecimal(gt=0, max_digits=15, decimal_places=2)


class HistoricoStatusResponse(BaseModel):
    id: int
    status_anterior: str | None
    status_novo: str
    alterado_em: str

    @classmethod
    def from_model(cls, historico):
        return cls(
            id=historico.id,
            status_anterior=historico.status_anterior,
            status_novo=historico.status_novo,
            alterado_em=isoformat_utc(historico.alterado_em),
        )


class OrdemCompraResponse(BaseModel):
    id: int
    numero: str
    cotacao_id: int
    fornecedor_id: int
    fornecedor_nome: str
    solicitacao_id: int
    id_produto: int
    produto_nome: str
    quantidade_solicitada: Decimal
    quantidade_recebida: Decimal
    quantidade_pendente: Decimal
    valor_total: Decimal
    status: str
    data_emissao: str
    data_previsao: str | None
    criado_em: str

    @classmethod
    def from_model(cls, ordem):
        quantidade_solicitada = ordem.cotacao.quantidade
        quantidade_recebida = ordem.quantidade_recebida
        quantidade_pendente = quantidade_solicitada - quantidade_recebida
        return cls(
            id=ordem.id,
            numero=build_order_number(ordem.id),
            cotacao_id=ordem.cotacao_id,
            fornecedor_id=ordem.fornecedor_id,
            fornecedor_nome=ordem.fornecedor.razao_social,
            solicitacao_id=ordem.cotacao.solicitacao_id,
            id_produto=ordem.cotacao.solicitacao.id_produto,
            produto_nome=ordem.cotacao.solicitacao.produto_nome,
            quantidade_solicitada=quantidade_solicitada,
            quantidade_recebida=quantidade_recebida,
            quantidade_pendente=quantidade_pendente,
            valor_total=ordem.valor_total,
            status=ordem.status,
            data_emissao=isoformat_date(ordem.data_emissao),
            data_previsao=isoformat_date(ordem.data_previsao),
            criado_em=isoformat_utc(ordem.criado_em),
        )


class OrdemCompraDetalheResponse(OrdemCompraResponse):
    historico: list[HistoricoStatusResponse]

    @classmethod
    def from_model(cls, ordem):
        base = OrdemCompraResponse.from_model(ordem).model_dump()
        base["historico"] = [
            HistoricoStatusResponse.from_model(item)
            for item in sorted(ordem.historico, key=lambda registro: registro.alterado_em)
        ]
        return cls(**base)


class OrdemCompraListResponse(PaginatedResponse):
    items: list[OrdemCompraResponse]


class ReceberOrdemCompraRequest(BaseModel):
    quantidade_recebida: PositiveQuantity
    nota_fiscal: str | None = Field(default=None, max_length=50)


class IntegracaoResponse(BaseModel):
    estoque: dict
    financeiro: dict


class ReceberOrdemCompraResponse(BaseModel):
    message: str
    ordem: OrdemCompraDetalheResponse
    integracoes: IntegracaoResponse
