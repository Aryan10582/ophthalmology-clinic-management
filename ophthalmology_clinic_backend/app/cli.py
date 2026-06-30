import argparse

from app.core.logging import configure_logging
from app.db.init_db import seed_default_admin
from app.db.session import SessionLocal


def seed_admin() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        seed_default_admin(db)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ophthalmology clinic backend management commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("seed-admin", help="Create the default admin account if the database is empty")

    args = parser.parse_args()
    if args.command == "seed-admin":
        seed_admin()


if __name__ == "__main__":
    main()
