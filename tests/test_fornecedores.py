import pytest

pytestmark = pytest.mark.anyio


async def test_fornecedor_crud(client):
    create_response = await client.post(
        "/compras/fornecedores",
        json={
            "cnpj": "12.345.678/0001-99",
            "razao_social": "Fornecedor XPTO",
            "email": "contato@xpto.com",
            "prazo_entrega": 7,
        },
    )
    assert create_response.status_code == 201
    fornecedor_id = create_response.json()["id"]

    list_response = await client.get("/compras/fornecedores?page=1&size=10")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    update_response = await client.put(
        f"/compras/fornecedores/{fornecedor_id}",
        json={
            "cnpj": "12.345.678/0001-99",
            "razao_social": "Fornecedor Atualizado",
            "email": "novo@xpto.com",
            "prazo_entrega": 10,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["razao_social"] == "Fornecedor Atualizado"

    delete_response = await client.delete(f"/compras/fornecedores/{fornecedor_id}")
    assert delete_response.status_code == 204
