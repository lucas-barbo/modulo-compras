# Módulo de Compras ERP

Microserviço em FastAPI responsável por fornecedores, solicitações de compra, cotações e ordens de compra do ERP. As integrações com outros módulos passam pelo CORE, conforme a especificação da pasta `Referencias`.

## Funcionalidades

- CRUD de fornecedores
- Criação e listagem de solicitações de compra
- Registro e listagem de cotações
- Aprovação de cotação com geração de ordem de compra
- Recebimento parcial ou total de ordem de compra
- Integração com Estoque e Financeiro via CORE
- Histórico de mudança de status da ordem de compra
- Documentação automática em `/docs` e `/redoc`

## Estrutura

```text
app/
├── core/
├── models/
├── routers/
├── schemas/
├── services/
└── main.py
alembic/
tests/
requirements.txt
README.md
```

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores:

```env
DATABASE_URL=sqlite:///./compras.db
CORE_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000
REQUEST_TIMEOUT=5
```

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8004
```

## Endpoints principais

- `GET /health`
- `GET|POST /compras/fornecedores`
- `GET|PUT|DELETE /compras/fornecedores/{id}`
- `GET|POST /compras/solicitacoes`
- `GET|POST /compras/cotacoes`
- `POST /compras/cotacoes/{id}/aprovar`
- `GET /compras/ordens`
- `GET /compras/ordens/{id}`
- `POST /compras/ordens/{id}/receber`

## Regras de integração

- Todas as rotas de negócio exigem JWT validado pelo CORE via `POST /auth/verify`
- Recebimento de OC envia:
  - `POST /estoque/movimentacoes/entrada`
  - `POST /financeiro/contas-pagar`
- As chamadas externas usam a URL base do CORE como gateway

## Testes

```bash
pytest --cov=app
```

Os testes usam SQLite isolado e sobrescrevem a autenticação para não depender do CORE em tempo de execução.
