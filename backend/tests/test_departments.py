import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_departments(async_client: AsyncClient):
    response = await async_client.get("/api/v1/departments/")
    assert response.status_code == 200
    depts = response.json()
    assert isinstance(depts, list)


@pytest.mark.asyncio
async def test_list_wards(async_client: AsyncClient):
    response = await async_client.get("/api/v1/departments/wards")
    assert response.status_code == 200
    wards = response.json()
    assert isinstance(wards, list)
