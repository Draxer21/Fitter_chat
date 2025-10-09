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
        nombre="Proteina Whey Isolate Fitter 1kg",
        categoria="Suplementos",
        categorias=("Suplementos", "Proteina", "Recuperacion"),
        precio="34990.00",
        descripcion="Aislado de suero con 27 g de proteina por porcion, endulzado con stevia y de facil disolucion.",
        stock=28,
    ),
    ProductPayload(
        nombre="Creatina Monohidratada Creaforce 300g",
        categoria="Suplementos",
        categorias=("Suplementos", "Fuerza", "Rendimiento"),
        precio="15990.00",
        descripcion="Creatina monohidratada micronizada para mejorar fuerza y potencia sin aditivos.",
        stock=42,
    ),
    ProductPayload(
        nombre="BCAA Recovery Blend 2-1-1",
        categoria="Suplementos",
        categorias=("Suplementos", "Recuperacion"),
        precio="12990.00",
        descripcion="Mezcla de aminoacidos esenciales 2-1-1 con electrolitos para apoyar la recuperacion muscular.",
        stock=38,
    ),
    ProductPayload(
        nombre="Banda de Resistencia Pro Set",
        categoria="Accesorios",
        categorias=("Accesorios", "Entrenamiento Funcional"),
        precio="19990.00",
        descripcion="Set de 3 bandas (ligera, media, fuerte) con costuras reforzadas ideal para gluteos y tren inferior.",
        stock=25,
    ),
    ProductPayload(
        nombre="Mat Yoga EcoGrip 6mm",
        categoria="Accesorios",
        categorias=("Accesorios", "Mindfulness"),
        precio="24990.00",
        descripcion="Mat antideslizante de caucho natural 6 mm, incluye correa de transporte y textura de doble cara.",
        stock=30,
    ),
    ProductPayload(
        nombre="Kettlebell Ajustable IronFlex 10-18kg",
        categoria="Equipamiento",
        categorias=("Equipamiento", "Fuerza"),
        precio="89990.00",
        descripcion="Kettlebell ajustable con 6 discos intercambiables y mango texturizado para agarre seguro.",
        stock=12,
    ),
    ProductPayload(
        nombre="Set Mancuernas Hexagonales 5-25kg",
        categoria="Equipamiento",
        categorias=("Equipamiento", "Fuerza", "Gimnasio en Casa"),
        precio="349990.00",
        descripcion="Pack de 10 pares de mancuernas recubiertas en goma con soporte vertical incluido.",
        stock=5,
    ),
    ProductPayload(
        nombre="Rueda Abdominal CoreGlide",
        categoria="Accesorios",
        categorias=("Accesorios", "Core"),
        precio="13990.00",
        descripcion="Rueda doble con freno parcial y rodilleras acolchadas para entrenamientos de core controlado.",
        stock=45,
    ),
    ProductPayload(
        nombre="Foam Roller Recovery 2 en 1",
        categoria="Recuperacion",
        categorias=("Recuperacion", "Fisioterapia"),
        precio="17990.00",
        descripcion="Rodillo de espuma de doble densidad con nucleo interior rigido para liberar tensiones post entreno.",
        stock=33,
    ),
    ProductPayload(
        nombre="Smart Bottle Hydratrack 1L",
        categoria="Hidratacion",
        categorias=("Hidratacion", "Accesorios"),
        precio="14990.00",
        descripcion="Botella inteligente de 1 litro con recordatorios luminosos y sensor para seguimiento de agua.",
        stock=50,
    ),
    ProductPayload(
        nombre="Barra Proteica FitBar Pack x12",
        categoria="Snacks Saludables",
        categorias=("Snacks Saludables", "Suplementos"),
        precio="19990.00",
        descripcion="Caja con 12 barras de 20 g de proteina, sabor chocolate almendra y sin azucares anadidos.",
        stock=60,
    ),
    ProductPayload(
        nombre="Omega 3 UltraPure 120 capsulas",
        categoria="Suplementos",
        categorias=("Suplementos", "Salud General"),
        precio="18990.00",
        descripcion="Concentrado de EPA y DHA grado farmaceutico con certificacion IFOS, libre de metales pesados.",
        stock=34,
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
