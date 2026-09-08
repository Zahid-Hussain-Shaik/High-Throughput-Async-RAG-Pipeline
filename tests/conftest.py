import pytest
from app.core.config import Settings

@pytest.fixture
def settings():
    return Settings(database_url="postgresql+asyncpg://test:test@localhost/test", embedding_dimension=16, chunk_size=10, chunk_overlap=2)
