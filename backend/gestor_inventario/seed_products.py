"""
Utility script to preload a curated catalog of fitness products into the database.

Usage (inside the virtualenv):
    python -m backend.gestor_inventario.seed_products

Pass --only-new to avoid updating rows that already exist (matched by nombre).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Sequence, Tuple

from ..app import create_app
from ..extensions import db
from .models import Categoria, Producto


@dataclass(frozen=True)
class ProductPayload:
    nombre: str
    categoria: str
    categorias: Sequence[str]
    precio: str  # stored as string to keep precision when converted to Decimal
    descripcion: str
    stock: int
    imagen_filename: str | None = None


BASE_PRODUCTS: Tuple[ProductPayload, ...] = (
    ProductPayload(
        nombre="Proteina Hidrolizada Elite 1.5kg",
        categoria="Suplementos",
        categorias=("Suplementos", "Proteina", "Recuperacion"),
        precio="38990.00",
        descripcion="Aislado hidrolizado con enzimas digestivas, 30 g de proteina y 6 g de BCAA por porcion.",
        stock=24,
    ),
    ProductPayload(
        nombre="Gainer Ultra Mass 5lb",
        categoria="Suplementos",
        categorias=("Suplementos", "Calorias", "Volumen"),
        precio="32990.00",
        descripcion="Gainer con 50 g de proteina y 250 g de carbohidratos complejos ideal para fase de volumen.",
        stock=19,
    ),
    ProductPayload(
        nombre="Glutamina Micronizada Recovery 400g",
        categoria="Suplementos",
        categorias=("Suplementos", "Recuperacion"),
        precio="16990.00",
        descripcion="Glutamina micronizada grado farmaceutico para apoyar sistema inmune y reparar tejido muscular.",
        stock=41,
    ),
    ProductPayload(
        nombre="Chaleco Lastrado CoreLoad 10kg",
        categoria="Equipamiento",
        categorias=("Equipamiento", "Fuerza", "Calistenia"),
        precio="59990.00",
        descripcion="Chaleco con pesos removibles y ajuste cruzado para entrenamientos de peso corporal avanzados.",
        stock=15,
    ),
    ProductPayload(
        nombre="Barra Olimpica Titan 20kg",
        categoria="Equipamiento",
        categorias=("Equipamiento", "Halterofilia"),
        precio="159990.00",
        descripcion="Barra olimpica 20 kg con mangos moleteados dual grip y rodamientos de aguja para levantamientos rapidos.",
        stock=7,
    ),
    ProductPayload(
        nombre="Discos Bumper Color Set 5 Pares",
        categoria="Equipamiento",
        categorias=("Equipamiento", "Halterofilia"),
        precio="189990.00",
        descripcion="Set de discos bumper 10 a 25 kg con codificacion por color y caucho de rebote controlado.",
        stock=6,
    ),
    ProductPayload(
        nombre="Kit Suspension Trainer Force",
        categoria="Accesorios",
        categorias=("Accesorios", "Entrenamiento Funcional"),
        precio="34990.00",
        descripcion="Sistema de entrenamiento en suspension con anclajes reforzados y guia digital de 40 ejercicios.",
        stock=38,
    ),
    ProductPayload(
        nombre="Bicicleta Spinning AirRide Pro",
        categoria="Equipamiento",
        categorias=("Equipamiento", "Cardio", "Gimnasio en Casa"),
        precio="429990.00",
        descripcion="Bike con resistencia magnetica, monitor LCD y conectividad bluetooth para clases virtuales.",
        stock=5,
    ),
    ProductPayload(
        nombre="Cafe Proteico Ready To Go Pack x12",
        categoria="Snacks Saludables",
        categorias=("Snacks Saludables", "Suplementos"),
        precio="23990.00",
        descripcion="Bebida lista para tomar con 15 g de proteina y 120 mg de cafeina natural por botella.",
        stock=44,
    ),
    ProductPayload(
        nombre="Peptidos de Colageno Active 500g",
        categoria="Suplementos",
        categorias=("Suplementos", "Salud General"),
        precio="27990.00",
        descripcion="Colageno hidrolizado tipo I y III con vitamina C añadida para articulaciones y piel.",
        stock=37,
    ),
    ProductPayload(
        nombre="Leggings Compresion MoveFree",
        categoria="Indumentaria",
        categorias=("Indumentaria", "Entrenamiento Funcional"),
        precio="27990.00",
        descripcion="Leggings de compresion con costuras planas, cintura alta y paneles de mesh para ventilacion.",
        stock=32,
    ),
    ProductPayload(
        nombre="Smartwatch Fitness Pulse HR",
        categoria="Tecnologia",
        categorias=("Tecnologia", "Cardio"),
        precio="119990.00",
        descripcion="Reloj con GPS integrado, sensor de frecuencia cardiaca y seguimiento de VO2 max.",
        stock=18,
    ),
)


def _ensure_categoria(nombre: str) -> Categoria:
    categoria = Categoria.query.filter_by(nombre=nombre).one_or_none()
    if categoria is None:
        categoria = Categoria(nombre=nombre)
        db.session.add(categoria)
    return categoria


def _assign_categories(producto: Producto, etiquetas: Iterable[str]) -> None:
    uniq_labels = list(dict.fromkeys(label.strip() for label in etiquetas if label.strip()))
    producto.categorias = [_ensure_categoria(label) for label in uniq_labels]


def _apply_payload(producto: Producto, payload: ProductPayload) -> None:
    producto.categoria = payload.categoria
    producto.precio = Decimal(payload.precio)
    producto.descripcion = payload.descripcion
    producto.stock = int(payload.stock)
    if payload.imagen_filename is not None:
        producto.imagen_filename = payload.imagen_filename or None
    _assign_categories(producto, payload.categorias)


def seed_products(overwrite_existing: bool = True) -> Tuple[int, int, int]:
    """Insert or update the base catalog.

    Returns:
        tuple(created, updated, skipped)
    """
    created = 0
    updated = 0
    skipped = 0

    for payload in BASE_PRODUCTS:
        producto = Producto.query.filter_by(nombre=payload.nombre).one_or_none()
        if producto is None:
            producto = Producto(nombre=payload.nombre)
            db.session.add(producto)
            _apply_payload(producto, payload)
            created += 1
            continue

        if overwrite_existing:
            _apply_payload(producto, payload)
            updated += 1
        else:
            skipped += 1

    db.session.commit()
    return created, updated, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed catalogo base de productos para Fitter.")
    parser.add_argument(
        "--only-new",
        action="store_true",
        help="Inserta solo productos que no existen (identificados por nombre).",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        created, updated, skipped = seed_products(overwrite_existing=not args.only_new)
        print(f"Productos creados: {created}")
        print(f"Productos actualizados: {updated}")
        if args.only_new:
            print(f"Productos omitidos (existentes): {skipped}")


if __name__ == "__main__":
    main()
