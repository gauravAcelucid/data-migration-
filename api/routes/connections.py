import logging

from fastapi import APIRouter, HTTPException

from file import create_source, list_targets, migrate_all

from ..metadata_storage import get_connection, list_connections, save_connection
from ..schemas import (
    ConnectionCreate,
    ConnectionListResponse,
    ConnectionMigrateRequest,
    ConnectionResponse,
    DatabaseListResponse,
    MigrationResponse,
    TableListResponse,
)
from ..tasks import run_migration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connections", tags=["connections"])


def _build_config(req: ConnectionCreate) -> dict:
    source_fields = {
        "postgresql": {
            "host", "port", "database", "username", "password",
            "ssl_mode", "ssl_cert", "ssl_key", "ssl_root_cert",
            "pool_min_size", "pool_max_size", "pool_timeout",
            "batch_size", "incremental_column", "cursor_name", "checkpoint_file",
        },
        "mongodb": {
            "connection_string", "database", "max_pool_size",
            "batch_size", "incremental_field", "checkpoint_file",
        },
        "sql": {
            "host", "port", "database", "username", "password",
            "dialect", "driver", "extra_params", "pool_size", "max_overflow",
            "batch_size", "incremental_column", "checkpoint_file",
        },
        "file_upload": {
            "input_dir", "file_pattern", "recursive", "include_content", "files",
            "batch_size", "checkpoint_file",
        },
    }
    allowed = source_fields.get(req.source_type, set())
    config = {}
    for f in allowed:
        val = getattr(req, f, None)
        if val is not None:
            config[f] = val
    return config


@router.post("", response_model=ConnectionResponse)
async def create_connection(req: ConnectionCreate):
    logger.info("POST /connections: name=%s type=%s", req.name, req.source_type)
    config = _build_config(req)
    connector, cfg = create_source(req.source_type, **config)
    try:
        await connector.connect(cfg)
        if not await connector.test_connection():
            raise HTTPException(status_code=400, detail="Connection failed: ping returned false")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {e}")
    finally:
        await connector.disconnect()
    conn_id = await save_connection(req.name, req.source_type, config)
    return ConnectionResponse(
        id=conn_id,
        name=req.name,
        source_type=req.source_type,
        config=config,
        created_at=None,
    )


@router.get("", response_model=ConnectionListResponse)
async def list_all_connections():
    logger.info("GET /connections")
    connections = await list_connections()
    return ConnectionListResponse(connections=connections)


@router.post("/{conn_id}/tables", response_model=TableListResponse)
async def get_tables(conn_id: str):
    logger.info("POST /connections/%s/tables", conn_id[:8])
    record = await get_connection(conn_id)
    if not record:
        raise HTTPException(status_code=404, detail="Connection not found")

    source_type = record["source_type"]
    config = record["config"]

    connector, cfg = create_source(source_type, **config)
    try:
        await connector.connect(cfg)
        tables = await connector.list_tables(cfg)
        logger.info("Found %d tables for connection %s", len(tables), conn_id[:8])
        return TableListResponse(tables=tables)
    finally:
        await connector.disconnect()


@router.post("/{conn_id}/databases", response_model=DatabaseListResponse)
async def get_databases(conn_id: str):
    logger.info("POST /connections/%s/databases", conn_id[:8])
    record = await get_connection(conn_id)
    if not record:
        raise HTTPException(status_code=404, detail="Connection not found")
    source_type = record["source_type"]
    config = record["config"]
    connector, cfg = create_source(source_type, **config)
    try:
        await connector.connect(cfg)
        databases = await connector.list_databases(cfg)
        logger.info("Found %d databases for connection %s", len(databases), conn_id[:8])
        return DatabaseListResponse(databases=databases)
    finally:
        await connector.disconnect()


@router.post("/{conn_id}/migrate", response_model=MigrationResponse, status_code=202)
async def migrate_from_connection(conn_id: str, req: ConnectionMigrateRequest):
    logger.info("POST /connections/%s/migrate: tables=%s", conn_id[:8], req.tables)
    record = await get_connection(conn_id)
    if not record:
        raise HTTPException(status_code=404, detail="Connection not found")

    source_type = record["source_type"]
    source_config = record["config"]

    task_id = await run_migration(
        source=source_type,
        target="s3",
        tables=req.tables,
        source_config=source_config,
        target_config=req.target_config,
    )
    return MigrationResponse(
        task_id=task_id,
        status="running",
        message="Migration started",
    )
