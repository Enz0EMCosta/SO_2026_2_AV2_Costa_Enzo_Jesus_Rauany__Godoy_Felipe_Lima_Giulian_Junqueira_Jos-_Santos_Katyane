"""Recuperação — GenResearch-Servidor (bloco 4 — Rauany)

Seleciona os trechos mais relevantes do índice vetorial da ingestão
(pacotes `servidor.ingestao` / `servidor.armazenamento`, do Fagner) e monta
o contexto que o pacote `servidor.resposta` usa para gerar a resposta.

Vetorização da consulta
    Confirmado em servidor/ingestao/embeddings.py: `deterministic_embedding`
    gera o vetor via SHA-256(texto_utf8 + contador_8_bytes_big_endian),
    expandido até a dimensão e normalizado em L2. `vetor_texto` abaixo
    importa essa função diretamente; o fallback local só entra em ação se o
    import falhar (ex.: módulo ainda não disponível no ambiente de quem
    rodar este pacote isolado) e replica o mesmo algoritmo.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

DIMENSAO_PADRAO = 128
TOP_K_PADRAO = 4
MAX_CONTEXTO_CARACTERES = 2000  # orçamento de contexto: evita montar um prompt enorme

try:
    from servidor.ingestao.embeddings import deterministic_embedding as _vetor_texto_real  # type: ignore
except ImportError:
    _vetor_texto_real = None


def vetor_texto(texto: str, dimensao: int = DIMENSAO_PADRAO) -> list[float]:
    """Vetor determinístico de um texto — idêntico ao usado na ingestão, pra
    que a similaridade de cosseno seja calculada contra o mesmo espaço
    vetorial dos vetores gravados no SQLite.

    Usa `deterministic_embedding` real se o pacote estiver disponível;
    caso contrário, replica o mesmo algoritmo localmente (fallback só para
    rodar/testar este pacote isolado, fora da árvore do projeto).
    """
    if _vetor_texto_real is not None:
        return _vetor_texto_real(texto, dimensao)

    if dimensao <= 0:
        raise ValueError("A dimensão do vetor deve ser positiva.")
    valores: list[float] = []
    contador = 0
    codificado = texto.encode("utf-8")
    while len(valores) < dimensao:
        digest = hashlib.sha256(codificado + contador.to_bytes(8, "big")).digest()
        for byte in digest:
            valores.append((byte / 127.5) - 1.0)
            if len(valores) == dimensao:
                break
        contador += 1
    norma = sum(v * v for v in valores) ** 0.5
    return [v / norma for v in valores] if norma else [0.0] * dimensao


def similaridade_cosseno(a: list[float], b: list[float]) -> float:
    produto = sum(x * y for x, y in zip(a, b))
    norma_a = sum(x * x for x in a) ** 0.5
    norma_b = sum(x * x for x in b) ** 0.5
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return produto / (norma_a * norma_b)


@dataclass
class Trecho:
    texto: str
    origem: str | None = None
    posicao: int | None = None
    score: float = 0.0


def _ler_item_do_lote(item) -> tuple[str, str | None, int | None, list[float]]:
    """Normaliza um item de `iter_chunk_vectors` (confirmado em
    servidor/armazenamento/sqlite_index.py): dict com chaves `text`,
    `relative_path`, `position`, `vector`. Mantém suporte a objeto com
    atributos ou tupla posicional como variação de segurança."""
    if isinstance(item, dict):
        return item["text"], item.get("relative_path"), item.get("position"), item["vector"]
    if hasattr(item, "text"):
        return item.text, getattr(item, "relative_path", None), getattr(item, "position", None), item.vector
    texto, origem, posicao, vetor = item
    return texto, origem, posicao, vetor


class Recuperador:
    """Busca os trechos mais similares a uma consulta no índice do Fagner.

    IMPORTANTE — thread-safety: `SQLiteIndex` usa uma conexão sqlite3, que só
    pode ser acessada pela thread que a criou. Como a fila (Vênisson) e o
    cache (Filipe) chamam a função de resposta a partir de múltiplos
    trabalhadores/threads, o índice é lido do SQLite UMA ÚNICA VEZ aqui no
    construtor (na thread que cria o Recuperador) e mantido em memória; cada
    chamada de `recuperar` depois só compara contra essa cópia, sem tocar o
    SQLite de novo — o que também é bem mais rápido que reler o índice a
    cada consulta.
    """

    def __init__(self, indice, dimensao: int = DIMENSAO_PADRAO, top_k: int = TOP_K_PADRAO,
                 tamanho_lote: int = 128):
        self.dimensao = dimensao
        self.top_k = top_k
        self._corpus: list[tuple[str, str | None, int | None, list[float]]] = []
        for lote in indice.iter_chunk_vectors(tamanho_lote):
            for item in lote:
                self._corpus.append(_ler_item_do_lote(item))

    def recuperar(self, consulta: str) -> list[Trecho]:
        vetor_consulta = vetor_texto(consulta, self.dimensao)
        candidatos = [
            Trecho(texto=texto, origem=origem, posicao=posicao,
                   score=similaridade_cosseno(vetor_consulta, vetor))
            for texto, origem, posicao, vetor in self._corpus
        ]
        candidatos.sort(key=lambda t: t.score, reverse=True)
        return candidatos[: self.top_k]


def montar_contexto(trechos: list[Trecho], limite_caracteres: int = MAX_CONTEXTO_CARACTERES) -> str:
    partes, total = [], 0
    for trecho in trechos:
        pedaco = trecho.texto.strip()
        if total + len(pedaco) > limite_caracteres:
            pedaco = pedaco[: max(0, limite_caracteres - total)]
        if not pedaco:
            break
        partes.append(pedaco)
        total += len(pedaco)
        if total >= limite_caracteres:
            break
    return "\n".join(partes)
