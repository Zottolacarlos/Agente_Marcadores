from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False


def setup_logging() -> logging.Logger:
    """Configura el logger 'app' (consola, legible). Idempotente: se puede llamar
    desde main.py (web) y cli.py sin duplicar handlers. Nivel vía LOG_LEVEL."""
    global _CONFIGURED
    logger = logging.getLogger("app")
    if _CONFIGURED:
        return logger

    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # evita logs duplicados con el logger raíz de uvicorn
    _CONFIGURED = True
    return logger
