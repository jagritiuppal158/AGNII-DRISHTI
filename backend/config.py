"""
config.py — Application settings loaded from the .env file.

Uses pydantic-settings so every value is type-validated at startup.
Fields that are truly optional for local dev (API keys) default to None
and will raise a clear error only when the endpoint that needs them is called.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Supabase ──────────────────────────────────────────────────
    # Replace placeholder values in .env with real credentials from
    # your Supabase project settings before using any DB-backed endpoints.
    supabase_db_url: str = "postgresql://placeholder:placeholder@localhost:5432/agni_drishti"
    supabase_anon_key: str = "placeholder-anon-key"

    # ── External APIs ─────────────────────────────────────────────
    firms_api_key: str = "placeholder-firms-key"

    # ── Server / CORS ─────────────────────────────────────────────
    # Comma-separated list of allowed origins; add production URLs here.
    cors_origins: str = "http://localhost:5173"

    # ── Pydantic-settings config ──────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a proper list (split on commas)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def require_supabase(self) -> None:
        """
        Call this at the start of any endpoint that needs a real DB connection.
        Raises RuntimeError with a clear message if placeholder creds are still set.
        """
        if self.supabase_db_url.startswith("postgresql://placeholder"):
            raise RuntimeError(
                "SUPABASE_DB_URL is not configured. "
                "Set a real value in backend/.env before using DB-backed endpoints."
            )

    def require_firms(self) -> None:
        """Call this at the start of any endpoint that calls the FIRMS API."""
        if self.firms_api_key == "placeholder-firms-key":
            raise RuntimeError(
                "FIRMS_API_KEY is not configured. "
                "Set a real value in backend/.env before calling FIRMS endpoints."
            )


# Module-level singleton — import this everywhere instead of re-instantiating.
settings = Settings()
