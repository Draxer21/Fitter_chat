"""
Crea un superusuario (is_admin=True) en la base de datos de Fitter.

Uso:
    python create_superuser.py
    python create_superuser.py --username admin --email admin@fitter.cl --password MiClave123 --name "Admin"
"""
import argparse
import sys

from backend.app import create_app
from backend.extensions import db
from backend.login.models import User


def prompt(label: str, secret: bool = False) -> str:
    import getpass
    fn = getpass.getpass if secret else input
    while True:
        val = fn(f"{label}: ").strip()
        if val:
            return val
        print("  ⚠  No puede estar vacío.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea un superusuario para Fitter.")
    parser.add_argument("--username", default="")
    parser.add_argument("--email",    default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--name",     default="")
    args = parser.parse_args()

    username = args.username or prompt("Username")
    email    = args.email    or prompt("Email")
    full_name = args.name    or prompt("Nombre completo")
    password  = args.password or prompt("Contraseña", secret=True)

    app = create_app()
    with app.app_context():
        if User.query.filter_by(username=username.lower().strip()).first():
            print(f"✗  Ya existe un usuario con username '{username}'.")
            sys.exit(1)
        if User.query.filter_by(email=email.lower().strip()).first():
            print(f"✗  Ya existe un usuario con email '{email}'.")
            sys.exit(1)

        user = User.create(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            is_admin=True,
        )
        db.session.commit()
        print(f"\n✓  Superusuario creado:")
        print(f"   Username : {user.username}")
        print(f"   Email    : {user.email}")
        print(f"   is_admin : {user.is_admin}")
        print(f"   ID       : {user.id}")


if __name__ == "__main__":
    main()
