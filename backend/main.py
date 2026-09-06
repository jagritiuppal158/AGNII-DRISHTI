"""
main.py — Agni-Drishti FastAPI application entry point.

Responsibilities:
  - Create and configure the FastAPI app instance.
  - Register CORS middleware (allow http://localhost:5173 in dev).
  - Install a global exception handler that always returns clean JSON errors.
  - Mount the /health liveness probe.
  - Mount versioned API routers (added as the project grows).
"""

import traceback

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import hotspots, infra, landcover

# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agni-Drishti API",
    description="Satellite-based thermal anomaly detection and classification platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,   # e.g. ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler so every unhandled error returns a JSON envelope
    instead of an HTML traceback or an empty 500 response.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
            # Only expose the detail in non-production environments.
            # In production, remove or gate this behind a DEBUG flag.
            "detail": traceback.format_exc(),
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "not_found",
            "message": f"The requested resource was not found: {request.url.path}",
        },
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={
            "error": "method_not_allowed",
            "message": f"Method {request.method} is not allowed on {request.url.path}.",
        },
    )

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["Meta"],
    summary="Liveness probe",
    response_description="Service is up and running.",
)
async def health_check() -> dict:
    """
    Liveness probe used by load balancers, Docker health checks, and CI pipelines.
    Returns HTTP 200 with `{"status": "ok"}` whenever the process is alive.
    """
    return {"status": "ok"}


# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(hotspots.router, prefix="/v1")

# Future routers (uncomment as implemented):
#   app.include_router(locations.router,       prefix="/v1")
#   app.include_router(cases.router,           prefix="/v1")

app.include_router(infra.router, prefix="/v1")
app.include_router(landcover.router, prefix="/v1")
