"""
Minimal FastAPI example with structured logging.

This shows the simplest possible setup - just 2 lines of code!
All logs (app, uvicorn, libraries) will be formatted as JSON automatically.
"""

from fastapi import FastAPI
from structured_logger import get_logger

# That's it! Everything is automatic now!
logger = get_logger(__name__)
app = FastAPI()


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@app.get("/error")
async def error():
    logger.error("Test error", extra={"error_type": "test"})
    return {"error": "Check logs"}


if __name__ == "__main__":
    import uvicorn

    # All logs are now structured JSON:
    # ✓ Your app logs (logger.info, logger.error)
    # ✓ Uvicorn logs (access, error)
    # ✓ Library logs (httpx, sqlalchemy, starlette, etc.) - automatic!
    uvicorn.run(app, host="0.0.0.0", port=8000)
