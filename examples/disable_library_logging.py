"""
Example showing how to disable library logger override.

By default, override_library_loggers=True, which formats third-party library
logs as JSON. If you want to leave library logs in their original format,
set override_library_loggers=False.
"""

from fastapi import FastAPI

from structured_logger import LoggerConfig, get_logger, setup_root_logger

# Disable library logger override - only format your app logs
config = LoggerConfig(
    override_uvicorn_loggers=True,  # Still format uvicorn logs
    override_library_loggers=False,  # Leave library logs unchanged
)

setup_root_logger(config=config)
logger = get_logger(__name__, config=config)

app = FastAPI()


@app.get("/")
async def root():
    logger.info("This will be JSON formatted")

    # Library logs will use their default format (not JSON)
    import logging

    httpx_logger = logging.getLogger("httpx")
    httpx_logger.info("This will NOT be JSON formatted")

    return {"message": "Check logs to see the difference"}


if __name__ == "__main__":
    import uvicorn

    # Result:
    # ✓ Your app logs: JSON formatted
    # ✓ Uvicorn logs: JSON formatted
    # ✗ Library logs: Original format (not JSON)
    uvicorn.run(app, host="0.0.0.0", port=8000)
