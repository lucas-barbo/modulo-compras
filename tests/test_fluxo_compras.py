import httpx
import pytest

pytestmark = pytest.mark.anyio


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {"status": "ok"}
        self.text = text
        self.content = b"{}"

    def json(self):
        return self._payload


async def criar_fornecedor(client):
    response = await client.post(
        "/compras/fornecedores",
        json={
            "cnpj": "98.765.432/0001-10",
            "razao_social": "Fornecedor Central",
            "email": "central@fornecedor.com",
            "prazo_entrega": 5,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def criar_solicitacao(client):
    response = await client.post(
        "/compras/solicitacoes",
        json={
            "id_produto": 101,
            "produto_nome": "Teclado Mecânico",
            "quantidade": "10.00",
            "justificativa": "Reposição do estoque mínimo",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def criar_cotacao(client, fornecedor_id, solicitacao_id):
    response = await client.post(
        "/compras/cotacoes",
        json={
            "solicitacao_id": solicitacao_id,
            "fornecedor_id": fornecedor_id,
            "preco_unitario": "99.90",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_aprovar_cotacao_gera_ordem(client):
    fornecedor_id = await criar_fornecedor(client)
    solicitacao_id = await criar_solicitacao(client)
    cotacao_id = await criar_cotacao(client, fornecedor_id, solicitacao_id)

    approve_response = await client.post(f"/compras/cotacoes/{cotacao_id}/aprovar")
    assert approve_response.status_code == 201
    body = approve_response.json()
    assert body["status"] == "aberta"
    assert body["numero"].startswith("OC-")
    assert body["historico"][0]["status_novo"] == "aberta"

    orders_response = await client.get("/compras/ordens?status_filtro=aberta")
    assert orders_response.status_code == 200
    assert orders_response.json()["total"] == 1


async def test_receber_ordem_parcial_e_total(client, monkeypatch):
    fornecedor_id = await criar_fornecedor(client)
    solicitacao_id = await criar_solicitacao(client)
    cotacao_id = await criar_cotacao(client, fornecedor_id, solicitacao_id)
    ordem_response = await client.post(f"/compras/cotacoes/{cotacao_id}/aprovar")
    ordem_id = ordem_response.json()["id"]

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: FakeResponse(payload={"status": "ok", "url": args[0]}),
    )

    partial_response = await client.post(
        f"/compras/ordens/{ordem_id}/receber",
        json={"quantidade_recebida": "4.00", "nota_fiscal": "NF-001"},
    )
    assert partial_response.status_code == 200
    partial_body = partial_response.json()
    assert partial_body["ordem"]["status"] == "parcial"
    assert partial_body["ordem"]["quantidade_recebida"] == "4.00"

    final_response = await client.post(
        f"/compras/ordens/{ordem_id}/receber",
        json={"quantidade_recebida": "6.00", "nota_fiscal": "NF-002"},
    )
    assert final_response.status_code == 200
    final_body = final_response.json()
    assert final_body["ordem"]["status"] == "encerrada"
    assert final_body["ordem"]["quantidade_recebida"] == "10.00"


async def test_receber_ordem_com_falha_externa_nao_altera_status(client, monkeypatch):
    fornecedor_id = await criar_fornecedor(client)
    solicitacao_id = await criar_solicitacao(client)
    cotacao_id = await criar_cotacao(client, fornecedor_id, solicitacao_id)
    ordem_response = await client.post(f"/compras/cotacoes/{cotacao_id}/aprovar")
    ordem_id = ordem_response.json()["id"]

    chamada = {"total": 0}

    def fake_post(*args, **kwargs):
        chamada["total"] += 1
        if chamada["total"] == 1:
            return FakeResponse(payload={"status": "ok", "url": args[0]})
        raise RuntimeError("financeiro indisponível")

    monkeypatch.setattr(httpx, "post", fake_post)

    response = await client.post(
        f"/compras/ordens/{ordem_id}/receber",
        json={"quantidade_recebida": "2.00", "nota_fiscal": "NF-ERRO"},
    )
    assert response.status_code == 502

    detail_response = await client.get(f"/compras/ordens/{ordem_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "aberta"
    assert detail_response.json()["quantidade_recebida"] == "0.00"
