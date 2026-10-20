from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servidor.ingestao.embeddings import deterministic_embedding
from servidor.ingestao.pipeline import ingest, split_text
from servidor.armazenamento.sqlite_index import SQLiteIndex


class IngestionTests(unittest.TestCase):
    def test_chunks_overlap_and_validation(self):
        self.assertEqual(split_text("a b c d e", 3, 1), ["a b c", "c d e", "e"])
        with self.assertRaises(ValueError): split_text("a", 2, 2)

    def test_reproducible_embedding(self):
        self.assertEqual(deterministic_embedding("consulta", 8), deterministic_embedding("consulta", 8))
        self.assertAlmostEqual(sum(x*x for x in deterministic_embedding("consulta", 8)), 1.0)

    def test_storage_idempotence_mmap_and_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "corpus"; root.mkdir(); (root / "a.txt").write_text("um dois tres quatro cinco", encoding="utf-8")
            (root / "empty.txt").write_text("", encoding="utf-8"); db = Path(temporary) / "index.sqlite3"
            first = ingest(root, db, chunk_words=3, overlap_words=1)
            second = ingest(root, db, read_mode="mmap", chunk_words=3, overlap_words=1)
            self.assertEqual(first["index_counts"], second["index_counts"])
            self.assertEqual(second["processed"], 0); self.assertEqual(second["ignored"], 2)
            index = SQLiteIndex(db); batches = list(index.iter_chunk_vectors()); index.close()
            self.assertEqual(sum(map(len, batches)), 3)

    def test_standard_and_mmap_produce_equal_index_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "corpus"; root.mkdir()
            (root / "a.txt").write_text("um dois trÃªs quatro cinco seis", encoding="utf-8")
            standard_db, mmap_db = Path(temporary) / "standard.sqlite3", Path(temporary) / "mmap.sqlite3"
            ingest(root, standard_db, read_mode="standard", chunk_words=3, overlap_words=1)
            ingest(root, mmap_db, read_mode="mmap", chunk_words=3, overlap_words=1)
            standard, mapped = SQLiteIndex(standard_db), SQLiteIndex(mmap_db)
            try:
                self.assertEqual(list(standard.iter_chunk_vectors()), list(mapped.iter_chunk_vectors()))
            finally:
                standard.close(); mapped.close()

    def test_missing_corpus(self):
        with self.assertRaises(FileNotFoundError): ingest(Path("corpus-que-nao-existe"), Path("any.sqlite3"))

    def test_subdirectory_modified_file_configuration_and_read_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); root = base / "corpus"; nested = root / "nested"; nested.mkdir(parents=True)
            document = nested / "doc.txt"; document.write_text("um dois trÃªs quatro", encoding="utf-8")
            (root / "invalido.txt").write_bytes(b"\xff\xfe")
            db = base / "index.sqlite3"
            first = ingest(root, db, chunk_words=3, overlap_words=1)
            self.assertEqual(first["processed"], 1); self.assertEqual(first["errors"], 1)
            document.write_text("um dois trÃªs quatro cinco seis", encoding="utf-8")
            changed = ingest(root, db, chunk_words=3, overlap_words=1)
            self.assertEqual(changed["processed"], 1)
            with self.assertRaises(ValueError): ingest(root, db, chunk_words=4, overlap_words=1)
            rebuilt = ingest(root, db, chunk_words=4, overlap_words=1, rebuild=True)
            self.assertEqual(rebuilt["index_counts"]["documents"], 1)
            with self.assertRaises(ValueError): ingest(root, db, dimension=0, rebuild=True)
