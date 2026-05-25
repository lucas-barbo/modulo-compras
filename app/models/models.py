from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, Text, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id            = Column(Integer, primary_key=True, index=True)
    cnpj          = Column(String(18), unique=True, nullable=False, index=True)
    razao_social  = Column(String(255), nullable=False)
    email         = Column(String(255), nullable=True)
    prazo_entrega = Column(Integer, nullable=False)

    cotacoes      = relationship("Cotacao", back_populates="fornecedor")
    ordens_compra = relationship("OrdemCompra", back_populates="fornecedor")

    def __repr__(self):
        return f"<Fornecedor id={self.id} razao_social={self.razao_social!r}>"


class SolicitacaoCompra(Base):
    __tablename__ = "solicitacoes_compra"

    id            = Column(Integer, primary_key=True, index=True)
    id_produto    = Column(Integer, nullable=False,
                           comment="Referência ao produto no módulo Estoque (externo)")
    produto_nome  = Column(String(255), nullable=False)
    quantidade    = Column(Numeric(15, 2), nullable=False)
    justificativa = Column(Text, nullable=False)
    criado_em     = Column(DateTime, nullable=False, default=utc_now)

    cotacoes = relationship("Cotacao", back_populates="solicitacao")

    def __repr__(self):
        return f"<SolicitacaoCompra id={self.id} produto={self.produto_nome!r}>"


class Cotacao(Base):
    __tablename__ = "cotacoes"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes_compra.id"), nullable=False)
    fornecedor_id  = Column(Integer, ForeignKey("fornecedores.id"), nullable=False)
    preco_unitario = Column(Numeric(15, 2), nullable=False)
    quantidade = Column(Numeric(15, 2), nullable=False)
    status = Column(String(10), nullable=False, default="pendente",
                            comment="pendente | aprovada | recusada")
    criado_em = Column(DateTime, nullable=False, default=utc_now)

    solicitacao = relationship("SolicitacaoCompra", back_populates="cotacoes")
    fornecedor = relationship("Fornecedor", back_populates="cotacoes")
    ordem_compra = relationship("OrdemCompra", back_populates="cotacao", uselist=False)

    @property
    def valor_total(self):
        return self.preco_unitario * self.quantidade

    def __repr__(self):
        return f"<Cotacao id={self.id} status={self.status!r}>"


class OrdemCompra(Base):
    __tablename__ = "ordens_compra"

    id = Column(Integer, primary_key=True, index=True)
    cotacao_id = Column(Integer, ForeignKey("cotacoes.id"), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"), nullable=False)
    valor_total = Column(Numeric(15, 2), nullable=False)
    quantidade_recebida = Column(Numeric(15, 2), nullable=False, default=0)
    status = Column(String(10), nullable=False, default="aberta",
                           comment="aberta | parcial | encerrada | cancelada")
    data_emissao  = Column(Date, nullable=False)
    data_previsao = Column(Date, nullable=True)
    criado_em = Column(DateTime, nullable=False, default=utc_now)

    cotacao = relationship("Cotacao", back_populates="ordem_compra")
    fornecedor = relationship("Fornecedor", back_populates="ordens_compra")
    historico = relationship("HistoricoStatusOC", back_populates="ordem_compra",
                                 cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OrdemCompra id={self.id} status={self.status!r}>"


class HistoricoStatusOC(Base):
    __tablename__ = "historico_status_oc"

    id = Column(Integer, primary_key=True, index=True)
    ordem_compra_id = Column(Integer, ForeignKey("ordens_compra.id"), nullable=False)
    status_anterior = Column(String(10), nullable=True,
                             comment="aberta | parcial | encerrada | cancelada")
    status_novo = Column(String(10), nullable=False)
    alterado_em = Column(DateTime, nullable=False, default=utc_now)

    ordem_compra = relationship("OrdemCompra", back_populates="historico")

    def __repr__(self):
        return (f"<HistoricoStatusOC oc_id={self.ordem_compra_id} "
                f"{self.status_anterior!r} → {self.status_novo!r}>")
