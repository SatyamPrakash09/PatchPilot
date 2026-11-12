"""Utility modules for PatchPilot."""

from patchpilot.utils.token_logger import (
    TokenLogger,
    TokenUsage,
    create_token_logger,
)


def reset_token_logger() -> None:
    """Reset the global token logger for a new session.

    Convenience function that wraps the main module's reset_token_logger.
    """
    from patchpilot.main import reset_token_logger as _reset
    _reset()


__all__ = [
    "TokenLogger",
    "TokenUsage",
    "create_token_logger",
    "reset_token_logger",
]