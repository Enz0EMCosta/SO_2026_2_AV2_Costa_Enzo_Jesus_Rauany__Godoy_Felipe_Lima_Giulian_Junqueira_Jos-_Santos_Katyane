"""CLI de ingestÃ£o incremental do corpus GenResearch."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import mmap
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from servidor.ingestao.embeddings import deterministic_embedding, vector_to_blob
from servidor.armazenamento.sqlite_index import SQLiteIndex

LOG = logging.getLogger("genresearch.ingest")


def split_text(text: str, chunk_words: int, overlap_words: int) -> list[str]:
    if chunk_words <= 0 or overlap_words < 0 or overlap_words >= chunk_words:
        raise ValueError("chunk_words deve ser positivo e overlap_words deve ser menor que chunk_words.")
    words = text.split()
    step = chunk_words - overlap_words
    return [" ".join(words[start:start + chunk_words]) for start in range(0, len(words), step) if words[start:start + chunk_words]]


def read_utf8(path: Path, mode: str) -> bytes:
    if mode == "standard":
        return path.read_bytes()
    if path.stat().st_size == 0:
        return b""
    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
        return mapped[:]  # A decodificaÃ§Ã£o UTF-8 exige bytes; o ganho deve ser medido, nÃ£o presumido.


def ingest(corpus: Path, database: Path, *, read_mode: str = "standard", chunk_words: int = 200,
           overlap_words: int = 40, dimension: int = 128, rebuild: bool = False,
           summaries: Path | None = None) -> dict:
    if not corpus.is_dir():
        raise FileNotFoundError(f"Pasta do corpus inexistente: {corpus}")
    if read_mode not in {"standard", "mmap"}:
        raise ValueError("read_mode deve ser 'standard' ou 'mmap'.")
    if chunk_words <= 0 or overlap_words < 0 or overlap_words >= chunk_words or dimension <= 0:
        raise ValueError("ConfiguraÃ§Ã£o de trecho ou dimensÃ£o invÃ¡lida.")
    settings = {"read_mode": read_mode, "chunk_words": chunk_words, "overlap_words": overlap_words,
                "embedding": {"method": "sha256-deterministic-simulated", "dimension": dimension, "normalized": "L2"}}
    # modo de leitura nÃ£o altera o Ã­ndice; permite comparar ambos sem exigir reconstruÃ§Ã£o.
    fingerprint_settings = {key: value for key, value in settings.items() if key != "read_mode"}
    fingerprint = hashlib.sha256(json.dumps(fingerprint_settings, sort_keys=True).encode()).hexdigest()
    started = time.perf_counter()
    timings = {"read_seconds": 0.0, "chunk_seconds": 0.0, "vector_seconds": 0.0, "write_seconds": 0.0}
    stats = {"processed": 0, "ignored": 0, "errors": 0, "chunks": 0, "vectors": 0, "corpus_bytes": 0}
    run_id, created_at = str(uuid.uuid4()), datetime.now(UTC).isoformat()
    summaries = summaries or database.parent / "ingestion_summaries"
    index = SQLiteIndex(database)
    try:
        with index.connection:
            index.configure(fingerprint, fingerprint_settings, rebuild)
            for path in sorted(corpus.rglob("*.txt")):
                relative = path.relative_to(corpus).as_posix()
                try:
                    began = time.perf_counter(); raw = read_utf8(path, read_mode); timings["read_seconds"] += time.perf_counter() - began
                    stats["corpus_bytes"] += len(raw)
                    if not raw:
                        stats["ignored"] += 1; LOG.warning("Ignorado arquivo vazio: %s", relative); continue
                    content_hash = hashlib.sha256(raw).hexdigest()
                    if index.document_hash(relative) == content_hash:
                        stats["ignored"] += 1; continue
                    text = raw.decode("utf-8")
                    began = time.perf_counter(); pieces = split_text(text, chunk_words, overlap_words); timings["chunk_seconds"] += time.perf_counter() - began
                    began = time.perf_counter(); blobs = [vector_to_blob(deterministic_embedding(piece, dimension)) for piece in pieces]; timings["vector_seconds"] += time.perf_counter() - began
                    began = time.perf_counter(); index.replace_document(relative, len(raw), content_hash, list(enumerate(pieces)), blobs, dimension); timings["write_seconds"] += time.perf_counter() - began
                    stats["processed"] += 1; stats["chunks"] += len(pieces); stats["vectors"] += len(blobs)
                except (OSError, UnicodeDecodeError, ValueError) as error:
                    stats["errors"] += 1; LOG.error("Falha ao processar %s: %s", relative, error)
            stats["index_counts"] = index.counts()
            vector_bytes = index.connection.execute("SELECT COALESCE(SUM(length(data)), 0) FROM vectors").fetchone()[0]
            summary = {"run_id": run_id, "created_at": created_at, "settings": settings, **stats,
                       "vector_volume_bytes_measured": vector_bytes, "storage_bytes": database.stat().st_size if database.exists() else 0,
                       "timings": {**timings, "total_seconds": time.perf_counter() - started},
                       "notes": {"storage_bytes": "tamanho total do SQLite (textos, metadados e vetores)", "vector_volume_bytes_measured": "soma medida dos BLOBs float32-le; nÃ£o Ã© E/S fÃ­sica"}}
            index.add_run(run_id, created_at, summary)
        summary["storage_bytes"] = database.stat().st_size
        summaries.mkdir(parents=True, exist_ok=True)
        (summaries / f"{run_id}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary
    finally:
        index.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingere .txt recursivamente no Ã­ndice SQLite GenResearch.")
    parser.add_argument("corpus", type=Path); parser.add_argument("--database", type=Path, default=Path("data/genresearch.sqlite3"))
    parser.add_argument("--read-mode", choices=("standard", "mmap"), default="standard")
    parser.add_argument("--chunk-words", type=int, default=200); parser.add_argument("--overlap-words", type=int, default=40)
    parser.add_argument("--dimension", type=int, default=128); parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--summaries", type=Path)
    args = parser.parse_args(); logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        result = ingest(args.corpus, args.database, read_mode=args.read_mode, chunk_words=args.chunk_words,
                        overlap_words=args.overlap_words, dimension=args.dimension, rebuild=args.rebuild, summaries=args.summaries)
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
