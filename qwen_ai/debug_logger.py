"""Debug Logger - Simple console debug logging for qwen_ai

Controlled by DEBUG_LOG_LEVEL env var:
    0 = off (default)
    1 = basic (chat creation, model info, errors)
    2 = verbose (stream phases, tool calls, details)

Usage:
    from .debug_logger import debug

    debug.info("message")
    debug.debug("verbose detail")
    debug.log_chat_create(model, chat_id, elapsed_ms)
"""

import os


class DebugLogger:
    """Simple debug logger that prints with [Debug] prefix.

    No external dependencies - just print() and flush.
    Controlled by the DEBUG_LOG_LEVEL environment variable.
    """

    def __init__(self):
        raw = os.environ.get('DEBUG_LOG_LEVEL', '0')
        try:
            self._level = int(raw)
        except (ValueError, TypeError):
            self._level = 0

    # ── Level checks ────────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        """True if any debug logging is active (level >= 1)."""
        return self._level >= 1

    @property
    def level(self) -> int:
        return self._level

    @property
    def is_verbose(self) -> bool:
        """True if verbose logging is active (level >= 2)."""
        return self._level >= 2

    # ── Core print helpers ──────────────────────────────────────────────────

    def info(self, *args, **kwargs):
        """Log at basic level (level >= 1)."""
        if self._level >= 1:
            print("[Debug]", *args, **kwargs, flush=True)

    def debug(self, *args, **kwargs):
        """Log at verbose level (level >= 2)."""
        if self._level >= 2:
            print("[Debug]", *args, **kwargs, flush=True)

    # ── Structured log methods ──────────────────────────────────────────────

    def log_chat_create(self, model: str, chat_id: str, elapsed_ms: float = 0):
        """Log when a new chat is created."""
        timing = f" ({elapsed_ms:.0f}ms)" if elapsed_ms else ""
        self.info(f"Chat created  model={model}  chat_id={chat_id}{timing}")

    def log_chat_completion(self, model: str, messages_count: int,
                            chat_id: str, stream: bool = True):
        """Log when a chat completion request is sent."""
        mode = "stream" if stream else "non-stream"
        self.info(
            f"Chat completion  model={model}  messages={messages_count}  "
            f"chat_id={chat_id}  mode={mode}"
        )

    def log_stream_phase(self, phase: str, chat_id: str,
                         details: str = ""):
        """Log a stream phase transition (think / answer / tool)."""
        msg = f"Stream phase={phase}  chat_id={chat_id}"
        if details:
            msg += f"  {details}"
        self.debug(msg)

    def log_tool_call(self, tool_name: str, chat_id: str, args: str = ""):
        """Log a tool call detected in the stream."""
        msg = f"Tool call  name={tool_name}  chat_id={chat_id}"
        if args:
            msg += f"  args={args[:300]}"
        self.info(msg)

    def log_error(self, context: str, error: BaseException):
        """Log an error with context."""
        self.info(f"ERROR [{context}]  {type(error).__name__}: {error}")

    def log_model_info(self, model: str, thinking_mode: str):
        """Log model mapping and thinking mode."""
        self.info(f"Model  resolved={model}  thinking_mode={thinking_mode}")

    def log_request_detail(self, chat_id: str, msg_count: int,
                           system_content_len: int = 0):
        """Log detailed request info (verbose level)."""
        self.debug(
            f"Request detail  chat_id={chat_id}  "
            f"messages={msg_count}  system_len={system_content_len}"
        )


# ── Module-level singleton ───────────────────────────────────────────────────

debug = DebugLogger()
"""Module-level singleton for easy import:

    from .debug_logger import debug
    debug.log_chat_create(model, chat_id, elapsed_ms)
"""
