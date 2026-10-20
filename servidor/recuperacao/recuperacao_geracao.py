"""Recuperação + Geração — GenResearch-Servidor (bloco 4 — Rauany) """

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass
from typing import Callable, Iterable

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
    rodar/testar este arquivo isolado, fora da árvore do projeto).
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
    cache (Filipe) chamam `gerar_resposta` a partir de múltiplos
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


def gerar_simulado(contexto: str) -> str:
    """Simula o custo computacional da geração (autorizado pelo enunciado).

    O tempo cresce com o tamanho do CONTEXTO montado, não da consulta,
    porque é o contexto que representaria o custo real de um modelo local
    processando os trechos recuperados.
    """
    custo_base = 0.01
    custo_por_caractere_contexto = 0.00015
    jitter = random.uniform(0.0, 0.004)
    time.sleep(custo_base + len(contexto) * custo_por_caractere_contexto + jitter)
    resumo = contexto[:80].replace("\n", " ")
    return f"[resposta simulada | contexto={len(contexto)} chars | base='{resumo}...']"


@dataclass
class ResultadoResposta:
    """Métricas de uma chamada — item 10 do enunciado ("registrar tempo e
    resultado resumido"). Ponto de integração com servidor/logs quando ele
    existir (mesmo padrão provisório que o Filipe usou em c4_cache.py)."""
    consulta: str
    resposta: str
    trechos_recuperados: int
    bytes_contexto: int
    tempo_recuperacao_s: float
    tempo_geracao_s: float
    tempo_total_s: float


def criar_gerador_resposta(
    indice,
    dimensao: int = DIMENSAO_PADRAO,
    top_k: int = TOP_K_PADRAO,
    registrador: Callable[[ResultadoResposta], None] | None = None,
) -> Callable[[str], str]:
    """Fábrica: devolve `gerar_resposta(consulta) -> str`, no formato que o
    cache (Filipe) e a fila (Vênisson) já sabem chamar.

    `registrador`, se fornecido, recebe um `ResultadoResposta` a cada
    chamada, com as métricas da recuperação e da geração.
    """
    recuperador = Recuperador(indice, dimensao=dimensao, top_k=top_k)

    def gerar_resposta(consulta: str) -> str:
        inicio = time.perf_counter()
        trechos = recuperador.recuperar(consulta)
        tempo_recuperacao = time.perf_counter() - inicio

        contexto = montar_contexto(trechos)

        inicio_geracao = time.perf_counter()
        resposta = gerar_simulado(contexto)
        tempo_geracao = time.perf_counter() - inicio_geracao

        if registrador is not None:
            registrador(ResultadoResposta(
                consulta=consulta,
                resposta=resposta,
                trechos_recuperados=len(trechos),
                bytes_contexto=len(contexto.encode("utf-8")),
                tempo_recuperacao_s=round(tempo_recuperacao, 6),
                tempo_geracao_s=round(tempo_geracao, 6),
                tempo_total_s=round(tempo_recuperacao + tempo_geracao, 6),
            ))
        return resposta

    return gerar_resposta


# ======================================================================
# Teste manual — roda sem depender do SQLiteIndex real do Fagner
# ======================================================================
class _IndiceFalsoParaTeste:
    """Índice mínimo só para validar a lógica deste módulo isoladamente.
    Imita o formato real de servidor/armazenamento/sqlite_index.py
    (dicts com chaves text/relative_path/position/vector)."""

    def __init__(self, trechos: Iterable[tuple[str, str, int]], dimensao: int = DIMENSAO_PADRAO):
        self._itens = [
            {"chunk_id": i, "relative_path": origem, "position": posicao,
             "text": texto, "vector": vetor_texto(texto, dimensao)}
            for i, (texto, origem, posicao) in enumerate(trechos)
        ]

    def iter_chunk_vectors(self, batch_size: int = 128):
        for inicio in range(0, len(self._itens), batch_size):
            yield self._itens[inicio: inicio + batch_size]


if __name__ == "__main__":
    indice_teste = _IndiceFalsoParaTeste([
        ("Memoria virtual permite que processos usem mais endereco do que a RAM fisica.", "doc1.txt", 0),
        ("O cache de paginas mantem dados de arquivos recentemente lidos na RAM.", "doc1.txt", 1),
        ("mmap mapeia um arquivo diretamente no espaco de enderecamento do processo.", "doc2.txt", 0),
        ("Semaforos e mutexes evitam condicoes de corrida entre threads.", "doc3.txt", 0),
    ])

    eventos: list[ResultadoResposta] = []
    gerar_resposta = criar_gerador_resposta(indice_teste, registrador=eventos.append)

    for pergunta in ["o que e memoria virtual?", "como funciona sincronizacao com mutex?"]:
        print(f"\nConsulta: {pergunta}")
        print("Resposta:", gerar_resposta(pergunta))

    print("\nMétricas registradas:")
    for evento in eventos:
        print(evento)
  
