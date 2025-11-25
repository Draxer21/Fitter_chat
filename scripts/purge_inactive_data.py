#!/usr/bin/env python3
"""Purgar datos inactivos segun la politica de retencion."""

import argparse
import sys
from pathlib import Path

# Garantiza que el repo (raiz) este en sys.path al ejecutar el script desde CLI.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app
from backend.extensions import db
from backend.security.retention import purge_stale_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Purga contextos de chat inactivos y anonimiza perfiles segun DATA_RETENTION_DAYS."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Dias de retencion (por defecto usa DATA_RETENTION_DAYS o 730).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No escribe cambios, solo muestra las filas que se afectarían.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = create_app()
    with app.app_context():
        result = purge_stale_data(app, db, retention_days=args.days, dry_run=args.dry_run)
        print(
            f"[retencion] days={result['retention_days']} dry_run={result['dry_run']} "
            f"chat_contexts_deleted={result['chat_contexts_deleted']} "
            f"profiles_anonymized={result['profiles_anonymized']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
