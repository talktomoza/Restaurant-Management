import os

def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    from app.config import get_settings
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.database_url == "postgresql://u:p@localhost:5432/db"
    assert settings.jwt_secret == "test-secret"
    assert settings.openrouter_api_key == "test-key"
    assert settings.openrouter_model == "deepseek/deepseek-chat-v3-0324:free"
