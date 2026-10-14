"""
Ember Backend — In-process metrics (Phase 11)

A tiny, dependency-free metrics registry: counters and latency histograms,
rendered as Prometheus text (`/metrics`) or JSON (`/metrics?format=json`).

Each histogram keeps (a) cumulative buckets, which Prometheus can aggregate
across instances, and (b) a ring buffer of the last RESERVOIR samples, from
which we report P50/P95/P99 directly (recent-window quantiles, nearest-rank).

Limits you should know about: state is per PROCESS. With several Cloud Run
instances each reports its own numbers (scrape every instance, or use a
managed collector); counters reset when an instance restarts. That is the
normal Prometheus model and fine for this scale.
"""

import threading
import time
from collections import deque
from contextlib import contextmanager

BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
RESERVOIR = 2048

_lock = threading.Lock()
_counters: dict[tuple[str, tuple], float] = {}
_histograms: dict[tuple[str, tuple], "_Histogram"] = {}


def _key(name: str, labels: dict | None) -> tuple[str, tuple]:
    return name, tuple(sorted((labels or {}).items()))


class _Histogram:
    def __init__(self) -> None:
        self.count = 0
        self.total = 0.0
        self.max = 0.0
        self.bucket_counts = [0] * len(BUCKETS)
        self.recent: deque[float] = deque(maxlen=RESERVOIR)

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.max = max(self.max, value)
        for i, bound in enumerate(BUCKETS):
            if value <= bound:
                self.bucket_counts[i] += 1
        self.recent.append(value)

    def quantile(self, q: float) -> float:
        if not self.recent:
            return 0.0
        data = sorted(self.recent)
        rank = max(1, -(-int(q * 1000) * len(data) // 1000))  # ceil(q*n) without float error
        return data[min(rank, len(data)) - 1]


def inc(name: str, labels: dict | None = None, n: float = 1) -> None:
    k = _key(name, labels)
    with _lock:
        _counters[k] = _counters.get(k, 0) + n


def observe(name: str, seconds: float, labels: dict | None = None) -> None:
    k = _key(name, labels)
    with _lock:
        hist = _histograms.get(k)
        if hist is None:
            hist = _histograms[k] = _Histogram()
        hist.add(seconds)


@contextmanager
def timed(name: str, labels: dict | None = None):
    start = time.perf_counter()
    try:
        yield
    finally:
        observe(name, time.perf_counter() - start, labels)


def reset() -> None:
    with _lock:
        _counters.clear()
        _histograms.clear()


def snapshot() -> dict:
    with _lock:
        counters = [{"name": n, "labels": dict(l), "value": v} for (n, l), v in sorted(_counters.items())]
        hists = [
            {
                "name": n,
                "labels": dict(l),
                "count": h.count,
                "sum": round(h.total, 6),
                "max": round(h.max, 6),
                "p50": round(h.quantile(0.50), 6),
                "p95": round(h.quantile(0.95), 6),
                "p99": round(h.quantile(0.99), 6),
            }
            for (n, l), h in sorted(_histograms.items())
        ]
    return {"counters": counters, "histograms": hists}


def _fmt_labels(labels: tuple, extra: tuple = ()) -> str:
    items = list(labels) + list(extra)
    if not items:
        return ""
    esc = lambda v: str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")  # noqa: E731
    return "{" + ",".join(f'{k}="{esc(v)}"' for k, v in items) + "}"


def render_prometheus() -> str:
    lines: list[str] = []
    with _lock:
        for (name, labels), value in sorted(_counters.items()):
            lines.append(f"{name}{_fmt_labels(labels)} {value:g}")
        for (name, labels), h in sorted(_histograms.items()):
            for bound, cnt in zip(BUCKETS, h.bucket_counts):
                lines.append(f"{name}_bucket{_fmt_labels(labels, (('le', f'{bound:g}'),))} {cnt}")
            lines.append(f"{name}_bucket{_fmt_labels(labels, (('le', '+Inf'),))} {h.count}")
            lines.append(f"{name}_sum{_fmt_labels(labels)} {h.total:.6f}")
            lines.append(f"{name}_count{_fmt_labels(labels)} {h.count}")
            for q in (0.5, 0.95, 0.99):
                lines.append(f"{name}_recent{_fmt_labels(labels, (('quantile', f'{q:g}'),))} {h.quantile(q):.6f}")
    return "\n".join(lines) + "\n"
