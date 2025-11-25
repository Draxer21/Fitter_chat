"""Colección simple de métricas en memoria con volcado a log."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Tuple

_EMPTY_TAGS: Tuple[Tuple[str, str], ...] = tuple()


def _tags_key(tags: Optional[Mapping[str, Any]]) -> Tuple[Tuple[str, str], ...]:
    if not tags:
        return _EMPTY_TAGS
    items = []
    for k, v in sorted(tags.items()):
        items.append((str(k), str(v)))
    return tuple(items)


class MetricsCollector:
    """Almacena contadores y tiempos agregados en memoria."""

    def __init__(self) -> None:
        self._counters: MutableMapping[Tuple[str, Tuple[Tuple[str, str], ...]], int] = defaultdict(int)
        self._latency: MutableMapping[
            Tuple[str, Tuple[Tuple[str, str], ...]], Dict[str, float]
        ] = defaultdict(lambda: {"count": 0, "total": 0.0, "max": 0.0})
        self._lock = threading.Lock()
        self._logger: Optional[logging.Logger] = None

    def set_logger(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _log_event(self, kind: str, name: str, value: float, tags: Tuple[Tuple[str, str], ...]) -> None:
        if not self._logger:
            return
        payload = {
            "ts": int(time.time() * 1000),
            "kind": kind,
            "name": name,
            "value": value,
            "tags": dict(tags),
        }
        try:
            self._logger.info(json.dumps(payload, ensure_ascii=False))
        except Exception:
            # No rompemos métricas por problemas de logging.
            pass

    def inc_counter(self, name: str, *, value: int = 1, tags: Optional[Mapping[str, Any]] = None) -> None:
        key_tags = _tags_key(tags)
        with self._lock:
            self._counters[(name, key_tags)] += value
        self._log_event("counter", name, value, key_tags)

    def observe_latency(self, name: str, ms: float, *, tags: Optional[Mapping[str, Any]] = None) -> None:
        key_tags = _tags_key(tags)
        with self._lock:
            stats = self._latency[(name, key_tags)]
            stats["count"] += 1
            stats["total"] += ms
            if ms > stats["max"]:
                stats["max"] = ms
        self._log_event("latency", name, ms, key_tags)

    def snapshot(self) -> Dict[str, Iterable[Dict[str, Any]]]:
        with self._lock:
            counters = [
                {"name": name, "value": value, "tags": dict(tags)}
                for (name, tags), value in self._counters.items()
            ]
            latency = []
            for (name, tags), stats in self._latency.items():
                count = max(1, stats["count"])
                latency.append(
                    {
                        "name": name,
                        "count": stats["count"],
                        "avg_ms": round(stats["total"] / count, 2),
                        "max_ms": round(stats["max"], 2),
                        "tags": dict(tags),
                    }
                )
        return {"counters": counters, "latency": latency}


metrics = MetricsCollector()


def setup_metrics_logger(app_logger: logging.Logger) -> None:
    logger = logging.getLogger("metrics")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = None
        try:
            handler = logging.FileHandler("backend/logs/metrics.log", encoding="utf-8")
        except Exception:
            handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    metrics.set_logger(logger)
