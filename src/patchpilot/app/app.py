"""FastAPI application for PatchPilot web server."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="PatchPilot", version="1.0")


@app.get("/")
def greet():
    """Root endpoint returning server status."""
    return {
        "message": "Hello Patch Pilot",
        "version": "1.0",
        "status": "OK",
        "server_status": "running"
    }


class TokenUsageResponse(BaseModel):
    """Response model for token usage endpoint."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


# Import here to avoid circular dependency
from patchpilot.main import get_token_logger


@app.get("/tokens", response_model=TokenUsageResponse)
def get_token_usage():
    """Get current token usage summary.

    Returns cumulative token counts across all LLM calls in this session.
    """
    logger = get_token_logger()
    usage = logger.get_total_usage()
    return TokenUsageResponse(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
    )


@app.post("/tokens/reset")
def reset_token_usage():
    """Reset token usage counters."""
    logger = get_token_logger()
    logger.reset_usage()
    return {"message": "Token counters reset"}