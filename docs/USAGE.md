# How to use this thing

This tool moves data from one place to another. You got databases like PostgreSQL, MongoDB, or just files sitting in a folder. You want that data in S3 as CSV, Parquet, or JSONL. Thats what this does.

There are two ways to use it:

1. **Via the API** — send HTTP requests to a server
2. **Via Python imports** — call the functions directly in your code

---

# Part 1: Using the API

First, start the server:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` and you can click buttons to test stuff.

## All the endpoints

| Method | URL | What it does |
|--------|-----|-------------|
| `GET` | `/health` | Check if server is alive |
| `GET` | `/sources` | See what sources you can pick |
| `GET` | `/targets` | See what targets you can pick |
| `POST` | `/migrate` | Start a migration (get a task_id back) |
| `GET` | `/migrate/{task_id}` | Check if your migration finished |

## POST /migrate — the main one

You send a JSON body with these fields:

| Field | Required? | What it is |
|-------|-----------|------------|
| `source` | **Yes** | Where to read from: `postgresql`, `mongodb`, `sql`, `file_upload` |
| `target` | **Yes** | Where to write to: `s3` |
| `tables` | **Yes** | List of table names or collection names |
| `source_config` | Depends | Settings for the source (see below) |
| `target_config` | Depends | Settings for the target (see below) |

### source_config for PostgreSQL

| Field | Required? | What it is | Default |
|-------|-----------|------------|---------|
| `host` | **Yes** | Where your DB lives | `localhost` |
| `port` | No | Port number | `5432` |
| `database` | **Yes** | Database name | — |
| `username` | **Yes** | Username | — |
| `password` | **Yes** | Password | — |
| `ssl_mode` | No | `disable`, `require`, etc | `prefer` |
| `incremental_column` | No | Column to track progress (like `id`) | `null` |
| `checkpoint_file` | No | Path to save progress (e.g. `C:/cp.json`) | `null` |
| `batch_size` | No | Rows per batch | `20000` |

### source_config for MongoDB

| Field | Required? | What it is | Default |
|-------|-----------|------------|---------|
| `connection_string` | **Yes** | Full MongoDB connection string | — |
| `database` | **Yes** | Database name | — |
| `collection` | **Yes** | Collection name (must match one of `tables`) | — |
| `incremental_field` | No | Field for incremental sync | `null` |
| `checkpoint_file` | No | Path to save progress | `null` |
| `batch_size` | No | Documents per batch | `20000` |

### source_config for SQL (PostgreSQL, MySQL, MSSQL, Oracle, SQLite)

| Field | Required? | What it is | Default |
|-------|-----------|------------|---------|
| `dialect` | **Yes** | `postgresql`, `mysql`, `mssql`, `oracle`, `sqlite` | `postgresql` |
| `host` | **Yes** | Server address | `localhost` |
| `port` | No | Port number | `5432` |
| `database` | **Yes** | Database name | — |
| `username` | **Yes** | Username | — |
| `password` | **Yes** | Password | — |
| `incremental_column` | No | Column for incremental sync | `null` |
| `checkpoint_file` | No | Path to save progress | `null` |
| `batch_size` | No | Rows per batch | `20000` |

### source_config for File Upload (read files from your computer)

| Field | Required? | What it is | Default |
|-------|-----------|------------|---------|
| `input_dir` | **Yes** | Full path to your folder | — |
| `file_pattern` | No | `"*"` for all, `"*.pdf"` for PDFs only | `"*"` |
| `files` | No | Pick specific files (overrides pattern) | `null` |
| `recursive` | No | Scan subfolders too? | `false` |
| `batch_size` | No | Files per batch | `100` |
| `checkpoint_file` | No | Path to save which files are done | `null` |
| `include_content` | No | Read file text into CSV? | `true` |

### target_config for S3

| Field | Required? | What it is | Default |
|-------|-----------|------------|---------|
| `bucket_name` | **Yes** | Your S3 bucket | — |
| `region` | No | AWS region | `us-east-1` |
| `file_format` | No | `csv`, `parquet`, or `jsonl` | `parquet` |
| `compression` | No | `none`, `snappy`, or `gzip` | `snappy` |

AWS credentials come from your `.env` file. No need to put them in the API request.

### What you get back

When you POST, you get a task_id:

```json
{
  "task_id": "abc12345-...",
  "status": "running",
  "message": "Migration started"
}
```

Then check status with `GET /migrate/{task_id}`.

**When running:**
```json
{
  "status": "running",
  "result": null,
  "error": null
}
```

**When done:**
```json
{
  "status": "completed",
  "result": [
    {
      "table_name": "users",
      "rows_loaded": 50000,
      "batch_count": 1
    }
  ],
  "error": null
}
```

**When it failed:**
```json
{
  "status": "failed",
  "result": null,
  "error": "relation \"users\" does not exist"
}
```

## Full examples — copy and paste these

### PostgreSQL to S3

```json
{
  "source": "postgresql",
  "target": "s3",
  "tables": ["users"],
  "source_config": {
    "host": "pg-1234.aivencloud.com",
    "port": 27726,
    "database": "defaultdb",
    "username": "avnadmin",
    "password": "your-password",
    "ssl_mode": "require"
  },
  "target_config": {
    "bucket_name": "my-bucket",
    "file_format": "csv",
    "compression": "none"
  }
}
```

### MongoDB to S3

```json
{
  "source": "mongodb",
  "target": "s3",
  "tables": ["jobs"],
  "source_config": {
    "connection_string": "mongodb+srv://user:pass@cluster.mongodb.net/",
    "database": "classroom",
    "collection": "jobs"
  },
  "target_config": {
    "bucket_name": "my-bucket",
    "file_format": "csv",
    "compression": "none"
  }
}
```

### File Upload (all files in a folder) to S3

```json
{
  "source": "file_upload",
  "target": "s3",
  "tables": ["my-uploads"],
  "source_config": {
    "input_dir": "C:/Users/hp/Downloads",
    "file_pattern": "*",
    "include_content": true
  },
  "target_config": {
    "bucket_name": "my-bucket",
    "file_format": "csv",
    "compression": "none"
  }
}
```

### File Upload (specific files) to S3

```json
{
  "source": "file_upload",
  "target": "s3",
  "tables": ["documents"],
  "source_config": {
    "input_dir": "C:/Users/hp/Downloads",
    "files": ["invoice.pdf", "report.docx", "notes.txt"],
    "include_content": true
  },
  "target_config": {
    "bucket_name": "my-bucket",
    "file_format": "csv",
    "compression": "none"
  }
}
```

## Quick reference: what you must include

| Part | Required fields |
|------|----------------|
| PostgreSQL source | `host`, `database`, `username`, `password` |
| MongoDB source | `connection_string`, `database`, `collection` |
| SQL source | `dialect`, `host`, `database`, `username`, `password` |
| File Upload source | `input_dir` |
| S3 target | `bucket_name` |

---

## Retry behavior (incremental sync)

Every table gets **3 automatic retries**. If batch 2 fails, it waits 0 seconds, then retries. If it fails again, waits 2 seconds, retries. Third fail? Error comes back to you.

To make retries smart (skip already-uploaded data), add two fields to your source config:

- `incremental_column` — which column goes up (like `id` or `created_at`)
- `checkpoint_file` — path to a local JSON file

The query changes from:
```sql
SELECT * FROM users ORDER BY id
```
to:
```sql
SELECT * FROM users WHERE id > 50000 ORDER BY id
```

For file_upload, the checkpoint stores filenames already processed. Next run skips them.

Checkpoint is saved after each batch is successfully uploaded to S3. If a batch fails, checkpoint stays where it was, so retry only fetches what was missed.

---

# Part 2: Using Python imports directly

You don't need the API at all. Just import the package and call functions.

## Install

```bash
uv add file
```

Or:

```bash
pip install file
```

## migrate_all() — the one function you need

Import it, call it, done.

```python
from file import migrate_all

results = await migrate_all(
    source_name="postgresql",
    target_name="s3",
    tables=["customers"],
    source_kwargs={
        "host": "db.example.com",
        "port": 5432,
        "database": "mydb",
        "username": "admin",
        "password": "secret123",
    },
    target_kwargs={
        "bucket_name": "my-bucket",
        "file_format": "csv",
        "compression": "none",
    },
)

print(f"Done. Moved {results[0].rows_loaded} rows")
```

It connects, reads data in batches, writes to S3, disconnects. If something fails, it closes connections properly.

## Source by source

### PostgreSQL

```python
from file import migrate_all

await migrate_all(
    source_name="postgresql",
    target_name="s3",
    tables=["orders"],
    source_kwargs={
        "host": "localhost",
        "port": 5432,
        "database": "shop",
        "username": "postgres",
        "password": "pass",
        "ssl_mode": "require",
        "batch_size": 50000,
    },
    target_kwargs={"bucket_name": "my-bucket", "file_format": "csv", "compression": "none"},
)
```

### MongoDB

```python
await migrate_all(
    source_name="mongodb",
    target_name="s3",
    tables=["products"],
    source_kwargs={
        "connection_string": "mongodb://localhost:27017",
        "database": "shop",
        "collection": "products",
    },
    target_kwargs={"bucket_name": "my-bucket", "file_format": "csv", "compression": "none"},
)
```

### SQL (MySQL, MSSQL, Oracle, SQLite too)

```python
await migrate_all(
    source_name="sql",
    target_name="s3",
    tables=["users"],
    source_kwargs={
        "dialect": "mysql",
        "host": "db.example.com",
        "port": 3306,
        "database": "shop",
        "username": "root",
        "password": "pass",
    },
    target_kwargs={"bucket_name": "my-bucket", "file_format": "csv", "compression": "none"},
)
```

### File Upload (read files from your computer)

Scans a folder, lists each file as a row (filename, size, type, content). Writes that list to S3.

```python
await migrate_all(
    source_name="file_upload",
    target_name="s3",
    tables=["invoices"],
    source_kwargs={
        "input_dir": "/home/user/documents",
        "file_pattern": "*.pdf",
        "recursive": False,
    },
    target_kwargs={"bucket_name": "my-bucket", "file_format": "csv", "compression": "none"},
)
```

The CSV on S3 looks like:

| filename     | size | type |
|--------------|------|------|
| invoice1.pdf | 2450 | .pdf |
| note.txt     | 120  | .txt |

## Using incremental sync (same as API)

Just add `incremental_column` and `checkpoint_file` to source_kwargs:

```python
results = await migrate_all(
    source_name="postgresql",
    target_name="s3",
    tables=["users"],
    source_kwargs={
        "host": "db.example.com",
        "database": "mydb",
        "username": "admin",
        "password": "secret123",
        "incremental_column": "id",
        "checkpoint_file": "C:/checkpoints/pg_users.json",
    },
    target_kwargs={"bucket_name": "my-bucket", "file_format": "csv"},
)
```

## More control: create_source and create_target

If you want to do things yourself step by step:

```python
from file import create_source, create_target

# Build connectors
pg, pg_cfg = create_source("postgresql",
    host="localhost",
    database="shop",
    username="postgres",
    password="pass",
)

s3, s3_cfg = create_target("s3",
    bucket_name="my-bucket",
    file_format="csv",
    compression="none",
)

# Connect
await pg.connect(pg_cfg)
await s3.connect(s3_cfg)

# Extract
result = await pg.extract("orders", pg_cfg)

# Load
load_result = await s3.load(result.batches, "orders")

# Disconnect
await pg.disconnect()
await s3.disconnect()

print(f"Moved {load_result.rows_loaded} rows")
```

Useful when you want custom filters, transform data in between, or reuse connections for many tables.

## File formats

| Format   | Extension | Notes |
|----------|-----------|-------|
| csv      | .csv      | Opens in Excel |
| parquet  | .parquet  | Fast, compressed |
| jsonl    | .jsonl    | One JSON per line |

Set `file_format` in target config. Compression: `none`, `snappy`, or `gzip`.
