"""Token counting and logging for PatchPilot LLM interactions.

This module provides token counting functionality similar to Codex or Claude.
It acts as a dynamic cumulative counter that silently accumulates tokens
across all API calls in a session, and displays a summary at the end.
"""

from typing import Dict, Any, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from dataclasses import dataclass
from datetime import datetime
import json

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Shared console for rich output
_console = Console()


@dataclass
class TokenUsage:
    """Tracks token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


class TokenLogger(BaseCallbackHandler):
    """Callback handler that accumulates token usage across LLM calls.

    This is a dynamic cumulative counter: it silently adds tokens from
    every API call to a running total, and displays a summary only when
    the session ends. No per-call output — just a growing counter.

    Example session summary:
        📊 Session Summary:
           Input:  5,678 tokens
           Output: 3,456 tokens
           Total:  9,134 tokens
    """

    def __init__(self, log_file: str | None = None, verbose: bool = True):
        self.log_file = log_file or self._get_default_log_path()
        self.verbose = verbose
        self.token_usage = TokenUsage()

    def _get_default_log_path(self) -> str:
        """Get default log file path in the project root."""
        return "patchpilot_token_usage.jsonl"

    def on_llm_start(
        self,
        llm: Any,
        prompts: list[Any],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts — no per-call output, just prepare."""
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends — silently accumulate tokens into the counter."""
        input_tokens = 0
        output_tokens = 0

        # Extract token counts from various response formats
        if hasattr(response, 'llm_output') and response.llm_output:
            llm_output = response.llm_output
            usage = llm_output.get('usage', {})
            if usage:
                input_tokens = usage.get('prompt_tokens', 0) or 0
                output_tokens = usage.get('completion_tokens', 0) or 0

        # Check for token metadata in generations
        if input_tokens == 0 and hasattr(response, 'generations'):
            for generation in response.generations:
                if generation and hasattr(generation[0], 'message'):
                    msg = generation[0].message
                    if hasattr(msg, 'usage_metadata'):
                        usage_meta = msg.usage_metadata
                        input_tokens = usage_meta.get('input_tokens', 0) or 0
                        output_tokens = usage_meta.get('output_tokens', 0) or 0
                        break

        # Accumulate into the running counter (dynamic, never resets)
        self.token_usage.input_tokens += input_tokens
        self.token_usage.output_tokens += output_tokens
        self.token_usage.total_tokens = (
            self.token_usage.input_tokens + self.token_usage.output_tokens
        )

        # Log each call to file for detailed history
        self._log_to_file(input_tokens, output_tokens)

    def _log_to_file(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> None:
        """Log token usage to JSONL file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": self.token_usage.total_tokens,
            "cumulative": self.token_usage.to_dict(),
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def get_total_usage(self) -> TokenUsage:
        """Get total token usage accumulated so far."""
        return self.token_usage

    def reset_usage(self) -> None:
        """Reset token usage counters for a new session."""
        self.token_usage = TokenUsage()

    def display_session_summary(self) -> None:
        """Display a final summary when the session ends."""
        total = self.token_usage

        # Build rich panel content
        content = Text()
        content.append("🪙 ", style="bold")
        content.append("Tokens: ", style="bold")
        content.append(f"{total.input_tokens:,}", style="cyan")
        content.append(" input  •  ", style="dim")
        content.append(f"{total.output_tokens:,}", style="magenta")
        content.append(" output  •  ", style="dim")
        content.append(f"{total.total_tokens:,}", style="bold green")
        content.append(" total", style="dim")

        _console.print()
        _console.print(Panel(
            content,
            title="[bold]📊 Session Summary[/bold]",
            border_style="blue",
            expand=False,
        ))

        # Log final summary
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "session_summary",
            "input_tokens": total.input_tokens,
            "output_tokens": total.output_tokens,
            "total_tokens": total.total_tokens,
        }
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass


def create_token_logger(log_file: str | None = None, verbose: bool = True) -> TokenLogger:
    """Factory function to create a TokenLogger instance.

    Usage:
        logger = create_token_logger(verbose=True)
        result = agent.invoke(
            {...},
            config={"callbacks": [logger]}
        )
        logger.display_session_summary()  # Called at session end
    """
    return TokenLogger(log_file=log_file, verbose=verbose)