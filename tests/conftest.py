import importlib
import os
import sys
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
async def client(tmp_path, monkeypatch):
    database_path = tmp_path / "compras_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("CORE_BASE_URL", "http://core.test")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    modules_to_reset = [
        name
        for name in list(sys.modules)
        if name == "app" or name.startswith("app.")
    ]
    for module_name in modules_to_reset:
        sys.modules.pop(module_name, None)

    app_main = importlib.import_module("app.main")
    deps = importlib.import_module("app.core.deps")
    db_module = importlib.import_module("app.core.db")
    models = importlib.import_module("app.models.models")

    app = app_main.create_app()

    async def fake_current_user():
        return {"sub": "test-user", "token": "fake-token"}

    app.dependency_overrides[deps.get_current_user] = fake_current_user

    models.Base.metadata.drop_all(bind=db_module.engine)
    models.Base.metadata.create_all(bind=db_module.engine)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    models.Base.metadata.drop_all(bind=db_module.engine)

    if database_path.exists():
        os.remove(database_path)
