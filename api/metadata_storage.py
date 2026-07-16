import json
import logging
import os
import uuid
from datetime import datetime, timezone

import psycopg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("METADATA_DATABASE_URL", "postgresql://postgres:123456789@localhost:5432/data_migration_meta")


async def init_db():
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.commit()
        logger.info("Metadata database initialized: %s", DATABASE_URL)
    finally:
        await conn.close()


async def save_connection(name: str, source_type: str, config: dict) -> str:
    conn_id = str(uuid.uuid4())
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO connections (id, name, source_type, config) VALUES (%s, %s, %s, %s)",
            (conn_id, name, source_type, json.dumps(config)),
        )
        await conn.commit()
        logger.info("Saved connection: id=%s name=%s type=%s", conn_id[:8], name, source_type)
        return conn_id
    finally:
        await conn.close()


async def list_connections() -> list[dict]:
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
    try:
        rows = await conn.execute(
            "SELECT id, name, source_type, config, created_at FROM connections ORDER BY created_at DESC"
        )
        results = await rows.fetchall()
        out = []
        for r in results:
            config = json.loads(r[3])
            if "password" in config:
                config["password"] = "****"
            out.append({
                "id": r[0],
                "name": r[1],
                "source_type": r[2],
                "config": config,
                "created_at": r[4].isoformat() if r[4] else None,
            })
        return out
    finally:
        await conn.close()


async def get_connection(conn_id: str) -> dict | None:
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
    try:
        rows = await conn.execute(
            "SELECT id, name, source_type, config, created_at FROM connections WHERE id = %s",
            (conn_id,),
        )
        r = await rows.fetchone()
        if not r:
            return None
        return {
            "id": r[0],
            "name": r[1],
            "source_type": r[2],
            "config": json.loads(r[3]),
            "created_at": r[4].isoformat() if r[4] else None,
        }
    finally:
        await conn.close()
