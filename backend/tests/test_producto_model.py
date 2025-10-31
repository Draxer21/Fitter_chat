import pytest

from backend.app import create_app
from backend.extensions import db
from backend.gestor_inventario.models import Producto


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session


def test_producto_to_dict_includes_optional_fields(session):
    producto = Producto(
        nombre="Proteína Premium",
        categoria="Suplementos",
        precio=19990,
        descripcion="Proteína con alto contenido de BCAA",
        stock=25,
        gallery=["https://example.com/1.png", "https://example.com/2.png"],
        specifications=[{"label": "Peso", "value": "1kg"}],
        highlights=["Incluye scoop", "Endulzado con stevia"],
        brand="Fitter Labs",
        rating=4.7,
        rating_count=128,
    )
    session.add(producto)
    session.commit()

    data = producto.to_dict()
    assert data["brand"] == "Fitter Labs"
    assert data["rating"] == pytest.approx(4.7)
    assert data["rating_count"] == 128
    assert isinstance(data["gallery"], list) and data["gallery"][0].endswith("1.png")
    assert data["specifications"][0]["label"] == "Peso"
    assert data["highlights"][0] == "Incluye scoop"
