"""Resposta — GenResearch-Servidor (bloco 4 — Rauany)

Gera (ou simula) a resposta a partir do contexto montado pelo pacote
`servidor.recuperacao`.

Contrato de integração (confirmado no c4_cache.py do Filipe): uma função
que recebe `str` (a consulta) e devolve `str` (a resposta). `gerar_resposta`,
devolvida por `criar_gerador_resposta`, cumpre esse contrato e pode ser
passada direto para `CacheCompartilhado.obter_ou_gerar` ou para o consumidor
da fila do Vênisson.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable

from servidor.recuperacao import DIMENSAO_PADRAO, TOP_K_PADRAO, Recuperador, montar_contexto


def gerar_simulado(contexto: str) -> str:
    """Simula o custo computacional da geração (autorizado pelo enunciado,
    Parte B — "Resposta": "gerar por modelo local OU simular custo
    computacional").

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
