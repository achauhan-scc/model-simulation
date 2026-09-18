import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any


LOGGER = logging.getLogger("model_simulator")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def emit_event(event_type: str, **values: Any) -> None:
    event = {
        "schemaVersion": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "model-simulator",
        "eventType": event_type,
        **values,
    }
    LOGGER.info(json.dumps(event, separators=(",", ":"), sort_keys=True))


def content_hash(value: Any) -> str:
    canonical = json.dumps(
        value, separators=(",", ":"), sort_keys=True, default=str
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"
