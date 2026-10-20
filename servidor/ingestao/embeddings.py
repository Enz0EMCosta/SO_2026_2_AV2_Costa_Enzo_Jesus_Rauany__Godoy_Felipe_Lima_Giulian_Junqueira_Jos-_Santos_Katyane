"""Vetores determinísticos, apropriados apenas para testes de infraestrutura."""

from __future__ import annotations

import hashlib
import math
import struct


def deterministic_embedding(text: str, dimension: int = 128) -> list[float]:
    """Retorna um vetor L2-normalizado e estável entre processos.

    O SHA-256 é expandido com um contador; ao contrário de ``hash()``, o
    resultado não depende da aleatorização do interpretador Python.
    """
    if dimension <= 0:
        raise ValueError("A dimensão do vetor deve ser positiva.")
    values: list[float] = []
    counter = 0
    encoded = text.encode("utf-8")
    while len(values) < dimension:
        digest = hashlib.sha256(encoded + counter.to_bytes(8, "big")).digest()
        for byte in digest:
            # Centraliza em zero e mantém a geração independente de plataforma.
            values.append((byte / 127.5) - 1.0)
            if len(values) == dimension:
                break
        counter += 1
    norm = math.sqrt(sum(value * value for value in values))
    return [value / norm for value in values] if norm else [0.0] * dimension


def vector_to_blob(vector: list[float]) -> bytes:
    return struct.pack("<" + "f" * len(vector), *vector)


def blob_to_vector(blob: bytes, dimension: int) -> list[float]:
    expected = dimension * 4
    if len(blob) != expected:
        raise ValueError(f"Blob de vetor inválido: {len(blob)} bytes; esperado {expected}.")
    return list(struct.unpack("<" + "f" * dimension, blob))
