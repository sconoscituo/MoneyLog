"""MoneyLog 기본 헬스체크 테스트"""
import os
import pytest
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_moneylog.db")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_app_is_created():
    """앱 인스턴스가 정상적으로 생성되는지 확인"""
    from app.main import app
    assert app is not None
    assert app.title == "MoneyLog"


@pytest.mark.anyio
async def test_openapi_schema():
    """OpenAPI 스키마 엔드포인트가 응답하는지 확인"""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "MoneyLog"


@pytest.mark.anyio
async def test_docs_endpoint():
    """Swagger UI 문서 페이지가 응답하는지 확인"""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/docs")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_expenses_api_exists():
    """지출 API 엔드포인트가 등록되어 있는지 확인"""
    from app.main import app
    routes = [route.path for route in app.routes]
    assert any("/api/expenses" in r or "/expenses" in r for r in routes)


@pytest.mark.anyio
async def test_categories_api_exists():
    """카테고리 API 엔드포인트가 등록되어 있는지 확인"""
    from app.main import app
    routes = [route.path for route in app.routes]
    assert any("/api/categories" in r or "/categories" in r for r in routes)
