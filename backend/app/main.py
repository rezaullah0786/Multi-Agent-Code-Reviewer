import logging
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_health, routes_index, routes_review, routes_webhooks
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("code_reviewer")

# Ensure required runtime directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Agent Enterprise Code Reviewer & PR Quality Gate API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the request.",
            "path": request.url.path,
        },
    )


# Register Routers
app.include_router(routes_health.router)
app.include_router(routes_review.router, prefix=settings.API_V1_STR)
app.include_router(routes_index.router, prefix=settings.API_V1_STR)
app.include_router(routes_webhooks.router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
