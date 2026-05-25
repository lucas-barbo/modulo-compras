from decimal import Decimal

from pydantic import BaseModel, Field, condecimal

from app.core.utils import isoformat_utc
from app.schemas.common import PaginatedResponse

MoneyValue = condecimal(gt=0, max_digits=15, decimal_places=2)


class CotacaoCreate(BaseModel):
    solicitacao_id: int = Field(..., gt=0)
    fornecedor_id: int = Field(..., gt=0)
    preco_unitario: MoneyValue
    quantidade: MoneyValue | None = Field(
        default=None,
        description="Se omitida, assume a quantidade da solicitação.",
    )


class CotacaoResponse(BaseModel):
    id: int
    solicitacao_id: int
    fornecedor_id: int
    fornecedor_nome: str
    produto_nome: str
    preco_unitario: Decimal
    quantidade: Decimal
    valor_total: Decimal
    status: str
    criado_em: str

    @classmethod
    def from_model(cls, cotacao):
        return cls(
            id=cotacao.id,
            solicitacao_id=cotacao.solicitacao_id,
            fornecedor_id=cotacao.fornecedor_id,
            fornecedor_nome=cotacao.fornecedor.razao_social,
            produto_nome=cotacao.solicitacao.produto_nome,
            preco_unitario=cotacao.preco_unitario,
            quantidade=cotacao.quantidade,
            valor_total=cotacao.valor_total,
            status=cotacao.status,
            criado_em=isoformat_utc(cotacao.criado_em),
        )


class CotacaoListResponse(PaginatedResponse):
    items: list[CotacaoResponse]
