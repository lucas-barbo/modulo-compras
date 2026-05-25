from decimal import Decimal

from pydantic import BaseModel, Field, condecimal

from app.core.utils import isoformat_utc
from app.schemas.common import PaginatedResponse

PositiveQuantity = condecimal(gt=0, max_digits=15, decimal_places=2)


class SolicitacaoCompraCreate(BaseModel):
    id_produto: int = Field(..., gt=0, description="ID do produto no módulo de estoque")
    produto_nome: str = Field(..., min_length=2, max_length=255)
    quantidade: PositiveQuantity
    justificativa: str = Field(..., min_length=5)


class SolicitacaoCompraResponse(BaseModel):
    id: int
    id_produto: int
    produto_nome: str
    quantidade: Decimal
    justificativa: str
    criado_em: str

    @classmethod
    def from_model(cls, solicitacao):
        return cls(
            id=solicitacao.id,
            id_produto=solicitacao.id_produto,
            produto_nome=solicitacao.produto_nome,
            quantidade=solicitacao.quantidade,
            justificativa=solicitacao.justificativa,
            criado_em=isoformat_utc(solicitacao.criado_em),
        )


class SolicitacaoListResponse(PaginatedResponse):
    items: list[SolicitacaoCompraResponse]
