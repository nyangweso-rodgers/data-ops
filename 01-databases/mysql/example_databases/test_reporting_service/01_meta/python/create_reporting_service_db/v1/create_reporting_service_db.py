"""
Create a MySQL test database and grant privileges to a user.

Reads defaults from .env:
    LOCAL_MYSQL_REPORTING_SERVICE_DB_HOST   - MySQL host (default: localhost)
    LOCAL_MYSQL_REPORTING_SERVICE_DB_NAME   - Database name (default: none, must be supplied via --db-name)
    LOCAL_MYSQL_REPORTING_SERVICE_DB_USER   - User to grant privileges to (default: mysql_user)
    LOCAL_MYSQL_DB_PASSWORD                 - Root/admin password used to create the DB and run GRANT

Usage:
    python create_mysql_test_db.py                          # uses LOCAL_MYSQL_REPORTING_SERVICE_DB_NAME
    python create_mysql_test_db.py --db-name test_myproject
    python create_mysql_test_db.py --db-name test_myproject --grant-user none
"""

import argparse
import os
import sys

import pymysql
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PORT = 3306
DEFAULT_ROOT_USER = "root"
DEFAULT_CHARSET = "utf8mb4"
DEFAULT_COLLATION = "utf8mb4_unicode_ci"

# Sourced from .env
_ENV_HOST = os.getenv("LOCAL_MYSQL_REPORTING_SERVICE_DB_HOST", "localhost")
_ENV_DB_NAME = os.getenv("LOCAL_MYSQL_REPORTING_SERVICE_DB_NAME", "")
_ENV_GRANT_USER = os.getenv("LOCAL_MYSQL_REPORTING_SERVICE_DB_USER", "mysql_user")
_ENV_ROOT_PASSWORD = os.getenv("LOCAL_MYSQL_DB_PASSWORD", "")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a MySQL test database and grant privileges."
    )
    parser.add_argument(
        "--db-name",
        default=_ENV_DB_NAME or None,
        help=(
            "Name of the database to create "
            "(default: LOCAL_MYSQL_REPORTING_SERVICE_DB_NAME)"
        ),
    )
    parser.add_argument(
        "--host",
        default=_ENV_HOST,
        help=f"MySQL host (default: LOCAL_MYSQL_REPORTING_SERVICE_DB_HOST → '{_ENV_HOST}')",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"MySQL port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--root-user",
        default=DEFAULT_ROOT_USER,
        help=f"Root/admin user used to create DB and run GRANT (default: {DEFAULT_ROOT_USER})",
    )
    parser.add_argument(
        "--root-password",
        default=_ENV_ROOT_PASSWORD,
        help="Root password (default: LOCAL_MYSQL_DB_PASSWORD env var)",
    )
    parser.add_argument(
        "--grant-user",
        default=_ENV_GRANT_USER,
        help=(
            f"User to grant ALL PRIVILEGES to "
            f"(default: LOCAL_MYSQL_REPORTING_SERVICE_DB_USER → '{_ENV_GRANT_USER}'). "
            "Pass 'none' to skip."
        ),
    )
    parser.add_argument(
        "--charset",
        default=DEFAULT_CHARSET,
        help=f"Character set (default: {DEFAULT_CHARSET})",
    )
    parser.add_argument(
        "--collation",
        default=DEFAULT_COLLATION,
        help=f"Collation (default: {DEFAULT_COLLATION})",
    )
    args = parser.parse_args()

    if not args.db_name:
        parser.error(
            "--db-name is required (or set LOCAL_MYSQL_REPORTING_SERVICE_DB_NAME in .env)"
        )

    return args


def connect(host, port, user, password):
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        print(f"✓ Connected to MySQL at {host}:{port} as '{user}'")
        return conn
    except pymysql.Error as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)


def create_database(conn, db_name, charset, collation):
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            f"CHARACTER SET {charset} COLLATE {collation}"
        )
    conn.commit()
    print(f"✓ Database '{db_name}' created (or already exists)")


def grant_privileges(conn, db_name, grant_user):
    with conn.cursor() as cur:
        # Check user exists before granting
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM mysql.user WHERE User = %s",
            (grant_user,),
        )
        row = cur.fetchone()
        if not row or row["cnt"] == 0:
            print(f"⚠  User '{grant_user}' does not exist — skipping GRANT")
            return
        cur.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{grant_user}'@'%'")
        cur.execute("FLUSH PRIVILEGES")
    conn.commit()
    print(f"✓ Granted ALL PRIVILEGES on '{db_name}' to '{grant_user}'@'%'")


def print_summary(db_name, host, port, grant_user):
    print()
    print("=" * 55)
    print("  Database ready")
    print("=" * 55)
    print(f"  Name     : {db_name}")
    print(f"  Host     : {host}:{port}")
    if grant_user and grant_user.lower() != "none":
        print(f"  User     : {grant_user}")
    print("=" * 55)
    print()
    print("  Env vars used:")
    print(f"    LOCAL_MYSQL_REPORTING_SERVICE_DB_HOST → {host}")
    print(f"    LOCAL_MYSQL_REPORTING_SERVICE_DB_NAME → {db_name}")
    print(f"    LOCAL_MYSQL_REPORTING_SERVICE_DB_USER → {grant_user}")
    print(f"    LOCAL_MYSQL_DB_PASSWORD               → (set)" if _ENV_ROOT_PASSWORD else "    LOCAL_MYSQL_DB_PASSWORD               → (not set)")
    print("=" * 55)


def main():
    args = parse_args()

    conn = connect(args.host, args.port, args.root_user, args.root_password)
    try:
        create_database(conn, args.db_name, args.charset, args.collation)

        if args.grant_user and args.grant_user.lower() != "none":
            grant_privileges(conn, args.db_name, args.grant_user)

        print_summary(args.db_name, args.host, args.port, args.grant_user)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
