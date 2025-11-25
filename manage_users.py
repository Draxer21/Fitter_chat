#!/usr/bin/env python
"""Script para gestionar usuarios (listar y borrar)"""

import sys
from backend.app import create_app
from backend.extensions import db
from backend.login.models import User

app = create_app()

def list_users():
    """Listar todos los usuarios"""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("❌ No hay usuarios en la BD")
            return
        
        print("\n📋 Usuarios registrados:")
        print("-" * 80)
        for user in users:
            print(f"ID: {user.id:3} | Username: {user.username:15} | Email: {user.email:30} | Admin: {user.is_admin}")
        print("-" * 80)
        print(f"Total: {len(users)} usuario(s)\n")

def make_admin(username):
    """Convertir un usuario en administrador"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ Usuario '{username}' no encontrado")
            return False
        
        try:
            user.is_admin = True
            db.session.commit()
            print(f"✓ Usuario '{username}' ahora es administrador")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return False

def remove_admin(username):
    """Remover permisos de administrador"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ Usuario '{username}' no encontrado")
            return False
        
        try:
            user.is_admin = False
            db.session.commit()
            print(f"✓ Usuario '{username}' ya no es administrador")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python manage_users.py list                    # Listar usuarios")
        print("  python manage_users.py delete <username>       # Borrar usuario")
        print("  python manage_users.py make-admin <username>   # Hacer admin")
        print("  python manage_users.py remove-admin <username> # Remover admin")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    elif command == "delete" and len(sys.argv) > 2:
        username = sys.argv[2]
        delete_user(username)
    elif command == "make-admin" and len(sys.argv) > 2:
        username = sys.argv[2]
        make_admin(username)
    elif command == "remove-admin" and len(sys.argv) > 2:
        username = sys.argv[2]
        remove_admin(username)
    else:
        print("❌ Comando no reconocido")
        sys.exit(1)
