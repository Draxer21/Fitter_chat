"""
Tests de rendimiento (RNF2).
Verifica que los endpoints criticos responden en menos de 2 segundos
y que el sistema de metricas opera correctamente.
"""
import time
import pytest
from backend.app import create_app, OperationalMetrics


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestHealthLatency:
    """Verificar que /health responde en menos de 2 segundos."""

    def test_health_under_2s(self, client):
        start = time.perf_counter()
        resp = client.get("/health")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"/health tardo {elapsed:.3f}s (limite: 2.0s)"

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        data = resp.get_json()
        assert data["ok"] is True


class TestMetricsLatency:
    """Verificar que /metrics responde en menos de 2 segundos."""

    def test_metrics_under_2s(self, client):
        start = time.perf_counter()
        resp = client.get("/metrics")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"/metrics tardo {elapsed:.3f}s (limite: 2.0s)"

    def test_metrics_returns_json(self, client):
        resp = client.get("/metrics")
        data = resp.get_json()
        assert "window_size" in data
        assert "p95_latency_ms" in data
        assert "fallback_rate" in data


class TestOperationalMetrics:
    """Verificar la clase OperationalMetrics directamente."""

    def test_empty_snapshot(self):
        m = OperationalMetrics(window_size=100)
        snap = m.snapshot()
        assert snap["window_size"] == 0
        assert snap["p95_latency_ms"] == 0.0
        assert snap["fallback_rate"] == 0.0

    def test_record_and_snapshot(self):
        m = OperationalMetrics(window_size=100)
        m.record(status_code=200, latency_ms=50.0, interaction_result="ok")
        m.record(status_code=200, latency_ms=100.0, interaction_result="ok")
        m.record(status_code=200, latency_ms=150.0, interaction_result="fallback")
        snap = m.snapshot()
        assert snap["window_size"] == 3
        assert snap["count_2xx"] == 3
        assert snap["fallback_rate"] > 0

    def test_p95_latency(self):
        m = OperationalMetrics(window_size=100)
        for i in range(100):
            m.record(status_code=200, latency_ms=float(i), interaction_result="ok")
        snap = m.snapshot()
        assert snap["p95_latency_ms"] >= 94.0  # p95 de 0..99

    def test_error_rates(self):
        m = OperationalMetrics(window_size=100)
        m.record(status_code=200, latency_ms=10, interaction_result="ok")
        m.record(status_code=400, latency_ms=10, interaction_result="ok")
        m.record(status_code=500, latency_ms=10, interaction_result="ok")
        snap = m.snapshot()
        assert snap["count_2xx"] == 1
        assert snap["count_4xx"] == 1
        assert snap["count_5xx"] == 1

    def test_window_size_limit(self):
        m = OperationalMetrics(window_size=5)
        for i in range(10):
            m.record(status_code=200, latency_ms=float(i), interaction_result="ok")
        snap = m.snapshot()
        assert snap["window_size"] == 5  # solo guarda las ultimas 5

    def test_handoff_rate(self):
        m = OperationalMetrics(window_size=100)
        m.record(status_code=200, latency_ms=10, interaction_result="handoff")
        m.record(status_code=200, latency_ms=10, interaction_result="ok")
        snap = m.snapshot()
        assert snap["handoff_rate"] == 0.5

    def test_blocked_rate(self):
        m = OperationalMetrics(window_size=100)
        m.record(status_code=200, latency_ms=10, interaction_result="blocked_no_consent")
        m.record(status_code=200, latency_ms=10, interaction_result="ok")
        snap = m.snapshot()
        assert snap["blocked_rate"] == 0.5


class TestStaticAssetsLatency:
    """Verificar que la app levanta rapido y sirve endpoints basicos."""

    def test_app_creation_under_5s(self):
        start = time.perf_counter()
        app = create_app()
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"create_app() tardo {elapsed:.3f}s (limite: 5.0s)"

    def test_multiple_health_calls(self, client):
        """10 llamadas consecutivas a /health deben promediar < 2s cada una."""
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = client.get("/health")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert resp.status_code == 200
        avg = sum(times) / len(times)
        assert avg < 2.0, f"Promedio de /health: {avg:.3f}s (limite: 2.0s)"
