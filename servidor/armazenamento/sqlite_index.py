"""Camada SQLite para documentos, trechos e vetores."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterator

from servidor.ingestao.embeddings import blob_to_vector


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS index_config (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    fingerprint TEXT NOT NULL,
    settings_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    relative_path TEXT NOT NULL UNIQUE,
    size_bytes INTEGER NOT NULL,
    content_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    text TEXT NOT NULL,
    UNIQUE(document_id, position)
);
CREATE TABLE IF NOT EXISTS vectors (
    chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    dimension INTEGER NOT NULL,
    format TEXT NOT NULL,
    data BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id, position);
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    summary_json TEXT NOT NULL
);
"""


class SQLiteIndex:
    def __init__(self, database: str | Path):
        self.path = Path(database)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def configure(self, fingerprint: str, settings: dict, rebuild: bool = False) -> None:
        existing = self.connection.execute("SELECT fingerprint FROM index_config WHERE singleton=1").fetchone()
        if existing and existing["fingerprint"] != fingerprint:
            if not rebuild:
                raise ValueError("A configuraÃ§Ã£o do Ã­ndice mudou. Execute novamente com --rebuild para reconstruÃ­-lo explicitamente.")
            self.connection.execute("DELETE FROM documents")
        self.connection.execute(
            "INSERT INTO index_config(singleton, fingerprint, settings_json) VALUES(1, ?, ?) "
            "ON CONFLICT(singleton) DO UPDATE SET fingerprint=excluded.fingerprint, settings_json=excluded.settings_json",
            (fingerprint, json.dumps(settings, ensure_ascii=False, sort_keys=True)),
        )

    def document_hash(self, relative_path: str) -> str | None:
        row = self.connection.execute("SELECT content_sha256 FROM documents WHERE relative_path=?", (relative_path,)).fetchone()
        return row["content_sha256"] if row else None

    def replace_document(self, relative_path: str, size_bytes: int, content_hash: str,
                         chunks: list[tuple[int, str]], vectors: list[bytes], dimension: int) -> None:
        row = self.connection.execute("SELECT id FROM documents WHERE relative_path=?", (relative_path,)).fetchone()
        if row:
            self.connection.execute("DELETE FROM documents WHERE id=?", (row["id"],))
        cursor = self.connection.execute(
            "INSERT INTO documents(relative_path, size_bytes, content_sha256) VALUES (?, ?, ?)",
            (relative_path, size_bytes, content_hash),
        )
        document_id = cursor.lastrowid
        for (position, text), vector in zip(chunks, vectors, strict=True):
            chunk_id = self.connection.execute(
                "INSERT INTO chunks(document_id, position, text) VALUES (?, ?, ?)",
                (document_id, position, text),
            ).lastrowid
            self.connection.execute(
                "INSERT INTO vectors(chunk_id, dimension, format, data) VALUES (?, ?, 'float32-le', ?)",
                (chunk_id, dimension, vector),
            )

    def add_run(self, run_id: str, created_at: str, summary: dict) -> None:
        self.connection.execute("INSERT INTO ingestion_runs VALUES (?, ?, ?)", (run_id, created_at, json.dumps(summary, ensure_ascii=False)))

    def counts(self) -> dict[str, int]:
        row = self.connection.execute("SELECT (SELECT COUNT(*) FROM documents) documents, (SELECT COUNT(*) FROM chunks) chunks, (SELECT COUNT(*) FROM vectors) vectors").fetchone()
        return dict(row)

    def iter_chunk_vectors(self, batch_size: int = 128) -> Iterator[list[dict]]:
        if batch_size <= 0:
            raise ValueError("batch_size deve ser positivo")
        cursor = self.connection.execute(
            "SELECT c.id AS chunk_id, d.relative_path, c.position, c.text, v.dimension, v.data "
            "FROM chunks c JOIN documents d ON d.id=c.document_id JOIN vectors v ON v.chunk_id=c.id "
            "ORDER BY c.id"
        )
        while rows := cursor.fetchmany(batch_size):
            yield [{"chunk_id": row["chunk_id"], "relative_path": row["relative_path"], "position": row["position"],
                    "text": row["text"], "vector": blob_to_vector(row["data"], row["dimension"])} for row in rows]
