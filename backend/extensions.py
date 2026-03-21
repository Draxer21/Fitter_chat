# backend/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

try:
    from flask_socketio import SocketIO
    socketio = SocketIO()
except ImportError:
    SocketIO = None  # type: ignore[assignment,misc]
    socketio = None  # type: ignore[assignment]

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
