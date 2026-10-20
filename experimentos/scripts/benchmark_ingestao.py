"""Gera corpus sintÃ©tico e coleta benchmark reprodutÃ­vel da ingestÃ£o GenResearch.

Uso: python experimentos/scripts/benchmark_ingestao.py
Os dados sÃ£o criados em experimentos/genresearch/evidencias/ e nÃ£o alteram o corpus do projeto.
"""
from __future__ import annotations

import csv
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experimentos" / "genresearch" / "evidencias"
CORPORA = {"pequeno": 32 * 1024, "medio": 256 * 1024, "grande": 1024 * 1024}
SEED = "genresearch-so-2026-2-seed-01"


def create_corpora() -> dict[str, dict]:
    corpus_root = OUT / "corpora"
    records = {}
    vocabulary = ["processo", "memoria", "pagina", "arquivo", "sistema", "operacional", "vetor", "indice", "leitura", "armazenamento"]
    for name, target in CORPORA.items():
        folder = corpus_root / name
        folder.mkdir(parents=True, exist_ok=True)
        for item in folder.glob("*.txt"): item.unlink()
        number, written, index = 0, 0, 0
        while written < target:
            text = " ".join(vocabulary[(index + offset) % len(vocabulary)] for offset in range(400)) + f" documento {number}.\n"
            path = folder / f"doc-{number:04d}.txt"; path.write_text(text, encoding="utf-8")
            written += path.stat().st_size; index += 3; number += 1
        records[name] = {"target_bytes": target, "actual_bytes": written, "documents": number, "path": str(folder.relative_to(ROOT))}
    return records


def system_metadata() -> dict:
    return {"timestamp_utc": datetime.now(UTC).isoformat(), "platform": platform.platform(),
            "python": sys.version, "machine": platform.machine(), "processor": platform.processor(),
            "cpu_count": os.cpu_count(), "swap_or_memory": "NÃ£o coletado: coleta executada no Windows sem ferramenta Linux /proc/free."}


def run() -> None:
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    corpora = create_corpora(); (OUT / "corpora.json").write_text(json.dumps({"seed": SEED, "corpora": corpora}, indent=2), encoding="utf-8")
    (OUT / "environment.json").write_text(json.dumps(system_metadata(), indent=2), encoding="utf-8")
    rows = []
    # AlternÃ¢ncia: standard/mmap, mmap/standard, standard/mmap para reduzir viÃ©s de ordem.
    order = [("standard", "mmap"), ("mmap", "standard"), ("standard", "mmap")]
    for size, metadata in corpora.items():
        for repeat, modes in enumerate(order, 1):
            for mode in modes:
                database = OUT / "databases" / f"{size}-{mode}-{repeat}.sqlite3"; summaries = OUT / "summaries"
                database.parent.mkdir(exist_ok=True)
                command = [sys.executable, "-X", "utf8", "-m", "servidor.ingestao.pipeline", metadata["path"], "--database", str(database.relative_to(ROOT)),
                           "--summaries", str(summaries.relative_to(ROOT)), "--read-mode", mode, "--chunk-words", "200", "--overlap-words", "40", "--dimension", "128"]
                began = time.perf_counter()
                process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
                wall = time.perf_counter() - began
                summary = json.loads(process.stdout)
                rows.append({"size": size, "repeat": repeat, "mode": mode, "command": " ".join(command), "wall_seconds": wall,
                             "read_seconds": summary["timings"]["read_seconds"], "chunk_seconds": summary["timings"]["chunk_seconds"],
                             "vector_seconds": summary["timings"]["vector_seconds"], "write_seconds": summary["timings"]["write_seconds"],
                             "ingest_seconds": summary["timings"]["total_seconds"], "corpus_bytes": summary["corpus_bytes"],
                             "documents": summary["index_counts"]["documents"], "chunks": summary["index_counts"]["chunks"],
                             "vectors": summary["index_counts"]["vectors"], "vector_volume_bytes_measured": summary["vector_volume_bytes_measured"],
                             "sqlite_bytes": summary["storage_bytes"], "rss_peak": "not_collected", "vsz": "not_collected",
                             "minor_faults": "not_available_windows", "major_faults": "not_available_windows", "io_counters": "not_collected"})
    fields = list(rows[0]);
    with (OUT / "raw_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    summary_rows = []
    for size in corpora:
        for mode in ("standard", "mmap"):
            group = [row for row in rows if row["size"] == size and row["mode"] == mode]
            values = [float(row["ingest_seconds"]) for row in group]
            summary_rows.append({"size": size, "mode": mode, "n": len(values), "mean_ingest_seconds": statistics.mean(values),
                                 "median_ingest_seconds": statistics.median(values), "stdev_ingest_seconds": statistics.stdev(values),
                                 "min_ingest_seconds": min(values), "max_ingest_seconds": max(values),
                                 "mean_read_seconds": statistics.mean(float(row["read_seconds"]) for row in group)})
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0])); writer.writeheader(); writer.writerows(summary_rows)
    (OUT / "commands.txt").write_text("python experimentos/scripts/benchmark_ingestao.py\npython -m unittest discover -s tests -v\n", encoding="utf-8")


if __name__ == "__main__": run()
