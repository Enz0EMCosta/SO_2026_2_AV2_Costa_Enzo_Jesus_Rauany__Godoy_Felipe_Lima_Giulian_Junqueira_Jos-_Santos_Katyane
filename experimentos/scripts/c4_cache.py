#!/usr/bin/env python3
"""
C4 — Cache compartilhado: consultas repetidas vs. semanticamente distintas
GenResearch-Servidor — bloco 5 — Filipe

Executa a configuração C4 do enunciado, variando quatro fatores:
  1. carga         — repetidas | distintas
  2. capacidade    — 8 | 32 | 128
  3. política      — lru | fifo
  4. trabalhadores — 1 | 2 | 4

Cada configuração roda 3 vezes (exigência do item 7). Cada execução processa
um lote de consultas, o que permite calcular média, mediana e p95 de latência
(item 10) — percentil sobre 3 pontos não existiria.

Saídas (em experimentos/resultados/):
  c4_resultados.csv   uma linha por execução
  c4_eventos.jsonl    log de eventos, com escrita concorrente protegida

Uso:
  python3 experimentos/scripts/c4_cache.py
  python3 experimentos/scripts/c4_cache.py --consultas 400 --repeticoes 5
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

# permite rodar o script a partir da raiz do repositório
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from servidor.cache import CacheCompartilhado  # noqa: E402

RESULTADOS = RAIZ / "experimentos" / "resultados"


# ======================================================================
# Log com escrita concorrente protegida (Parte B)
# ======================================================================
class LogProtegido:
    """Escreve eventos em JSONL serializando o acesso ao arquivo.

    PROVISÓRIO: o repositório prevê um pacote `servidor/logs` com essa
    responsabilidade. Quando ele existir, este escritor deve ser substituído
    pela implementação oficial da equipe.

    Sem o mutex, duas threads que escrevem ao mesmo tempo podem intercalar
    bytes na mesma linha, corrompendo o registro.
    """

    def __init__(self, caminho: Path) -> None:
        self._caminho = caminho
        self._lock = threading.Lock()
        self._arquivo = open(caminho, "a", encoding="utf-8")

    def registrar(self, **campos) -> None:
        linha = json.dumps({"ts": time.time(), **campos}, ensure_ascii=False)
        with self._lock:
            self._arquivo.write(linha + "\n")

    def fechar(self) -> None:
        with self._lock:
            self._arquivo.close()


# ======================================================================
# Geração simulada (substituível pela implementação do bloco 4)
# ======================================================================
def gerar_resposta(consulta: str) -> str:
    """Simula recuperação de contexto + geração da resposta.

    O custo cresce com o tamanho da consulta, imitando o efeito do tamanho
    do contexto sobre o tempo de geração. O enunciado autoriza explicitamente
    simular o custo computacional (Parte B, "Resposta").

    PARA INTEGRAR COM O BLOCO 4: troque o corpo desta função pela chamada à
    recuperação + geração reais. A assinatura — recebe str, devolve str — e
    todo o resto do experimento permanecem inalterados.
    """
    custo_base = 0.008
    custo_por_char = 0.00012
    jitter = random.uniform(0.0, 0.004)
    time.sleep(custo_base + len(consulta) * custo_por_char + jitter)
    return f"[resposta simulada para: {consulta[:40]}]"


# ======================================================================
# Cargas de trabalho
# ======================================================================
TEMAS = [
    "memoria virtual", "paginacao", "swap", "cache de paginas",
    "mmap", "leitura convencional", "falta de pagina", "RSS e VSZ",
    "fila de requisicoes", "produtor consumidor", "mutex", "semaforo",
    "condicao de corrida", "deadlock", "starvation", "escalonamento",
    "embeddings", "indice vetorial", "fragmentacao de documentos", "RAG",
]

MOLDES = [
    "o que e {}",
    "explique {} em detalhes",
    "como funciona {} no linux",
    "qual a relacao entre {} e desempenho",
    "cite um exemplo pratico de {}",
]


def montar_consultas(carga: str, quantidade: int, semente: int) -> list[str]:
    """Produz a sequência de consultas de uma execução.

    repetidas  — poucas consultas distintas, muito repetidas. Representa um
                 serviço com perguntas frequentes; é onde o cache deve render.
    distintas  — toda consulta é única. Representa exploração aberta; o cache
                 só acumula custo de manutenção, sem acerto possível.
    """
    rng = random.Random(semente)

    if carga == "repetidas":
        # Universo de 60 consultas distintas, sorteadas com distribuição
        # enviesada (peso 1/posição, estilo Zipf): poucas consultas muito
        # populares e uma cauda longa de raras. É o padrão típico de um
        # serviço real de perguntas, e é o que torna a comparação entre
        # políticas significativa — sob localidade, LRU preserva o conjunto
        # quente enquanto FIFO o descarta por antiguidade.
        pool = [
            f"{MOLDES[i % len(MOLDES)].format(TEMAS[i % len(TEMAS)])} v{i // 20}"
            for i in range(60)
        ]
        pesos = [1.0 / (i + 1) for i in range(len(pool))]
        return rng.choices(pool, weights=pesos, k=quantidade)

    if carga == "distintas":
        # cada consulta carrega um identificador único
        return [
            f"{rng.choice(MOLDES).format(rng.choice(TEMAS))} caso {i}"
            for i in range(quantidade)
        ]

    raise ValueError(f"carga desconhecida: {carga}")


# ======================================================================
# Execução de uma configuração
# ======================================================================
def executar(
    carga: str,
    capacidade: int,
    politica: str,
    trabalhadores: int,
    consultas: list[str],
    log: LogProtegido,
    repeticao: int,
) -> dict:
    cache = CacheCompartilhado(capacidade=capacidade, politica=politica)
    latencias: list[float] = []
    lat_acerto: list[float] = []
    lat_erro: list[float] = []
    trava_listas = threading.Lock()

    def tarefa(consulta: str) -> None:
        _, foi_acerto, latencia = cache.obter_ou_gerar(consulta, gerar_resposta)
        with trava_listas:
            latencias.append(latencia)
            (lat_acerto if foi_acerto else lat_erro).append(latencia)

    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
        list(pool.map(tarefa, consultas))
    duracao = time.perf_counter() - inicio

    m = cache.metricas
    ordenadas = sorted(latencias)
    p95 = ordenadas[min(int(0.95 * len(ordenadas)), len(ordenadas) - 1)]

    linha = {
        "horario": datetime.now().astimezone().isoformat(),
        "ambiente": platform.platform(),
        "python": platform.python_version(),
        "pid": os.getpid(),
        "configuracao": "C4",
        "carga": carga,
        "capacidade": capacidade,
        "politica": politica,
        "trabalhadores": trabalhadores,
        "repeticao": repeticao,
        "consultas": len(consultas),
        "consultas_distintas": len(set(consultas)),
        "acertos": m.acertos,
        "erros": m.erros,
        "taxa_acerto": round(m.taxa_acerto, 4),
        "taxa_erro": round(m.taxa_erro, 4),
        "substituicoes": m.substituicoes,
        "tamanho_final": m.tamanho_atual,
        "tempo_total_s": round(duracao, 4),
        "tempo_economizado_s": round(m.tempo_economizado_s, 4),
        "tempo_gerando_s": round(m.tempo_gerando_s, 4),
        "vazao_consultas_s": round(len(consultas) / duracao, 2),
        "lat_media_ms": round(statistics.mean(latencias) * 1000, 3),
        "lat_mediana_ms": round(statistics.median(latencias) * 1000, 3),
        "lat_p95_ms": round(p95 * 1000, 3),
        "lat_acerto_media_ms": round(
            statistics.mean(lat_acerto) * 1000, 3) if lat_acerto else 0.0,
        "lat_erro_media_ms": round(
            statistics.mean(lat_erro) * 1000, 3) if lat_erro else 0.0,
    }

    log.registrar(evento="execucao_concluida", **linha)
    return linha


# ======================================================================
# Matriz experimental
# ======================================================================
def montar_matriz() -> list[tuple[str, int, str, int]]:
    """Configurações a executar: (carga, capacidade, politica, trabalhadores).

    Varia um fator por vez a partir de uma configuração base
    (capacidade 32, LRU, 4 trabalhadores), sempre nas duas cargas.
    """
    base_cap, base_pol, base_trab = 32, "lru", 4
    configs: list[tuple[str, int, str, int]] = []

    for carga in ("repetidas", "distintas"):
        for cap in (8, 32, 128):                     # fator 1: capacidade
            configs.append((carga, cap, base_pol, base_trab))
        for pol in ("lru", "fifo"):                  # fator 2: política
            configs.append((carga, base_cap, pol, base_trab))
        for trab in (1, 2, 4):                       # fator 3: trabalhadores
            configs.append((carga, base_cap, base_pol, trab))

    # remove duplicatas preservando a ordem
    vistos, unicas = set(), []
    for c in configs:
        if c not in vistos:
            vistos.add(c)
            unicas.append(c)
    return unicas


def coletar_ambiente() -> dict:
    def shell(cmd: str) -> str:
        try:
            return subprocess.check_output(
                cmd, shell=True, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            return "indisponivel"

    return {
        "horario": datetime.now().astimezone().isoformat(timespec="seconds"),
        "kernel": platform.release(),
        "sistema": shell("grep PRETTY_NAME /etc/os-release | cut -d'\"' -f2"),
        "python": platform.python_version(),
        "cpus": os.cpu_count(),
        "memoria": shell("free -h | awk '/^Mem:/ {print $2}'"),
        "swap": shell("free -h | awk '/^Swap:/ {print $2}'"),
        "commit": shell("git rev-parse --short HEAD"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="C4 — cache compartilhado")
    ap.add_argument("--consultas", type=int, default=200,
                    help="consultas por execução (padrão: 200)")
    ap.add_argument("--repeticoes", type=int, default=3,
                    help="repetições por configuração (padrão: 3)")
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--validacao", action="store_true",
                    help="grava em c4_validacao.csv (execução de conferência)")
    args = ap.parse_args()

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    nome = "c4_validacao.csv" if args.validacao else "c4_cache_compartilhado.csv"
    csv_saida = RESULTADOS / nome
    log = LogProtegido(RESULTADOS / "c4_eventos.jsonl")

    ambiente = coletar_ambiente()
    log.registrar(evento="inicio", ambiente=ambiente, parametros=vars(args))

    print("=" * 72)
    print("C4 — CACHE COMPARTILHADO")
    print("=" * 72)
    for k, v in ambiente.items():
        print(f"  {k:10s} {v}")
    print(f"  {'consultas':10s} {args.consultas} por execução")
    print(f"  {'repeticoes':10s} {args.repeticoes} por configuração")
    print()

    matriz = montar_matriz()
    total = len(matriz) * args.repeticoes
    print(f"{len(matriz)} configurações × {args.repeticoes} repetições "
          f"= {total} execuções\n")

    linhas: list[dict] = []
    n = 0
    for carga, cap, pol, trab in matriz:
        for rep in range(1, args.repeticoes + 1):
            n += 1
            consultas = montar_consultas(
                carga, args.consultas, semente=args.semente + rep
            )
            linha = executar(carga, cap, pol, trab, consultas, log, rep)
            linhas.append(linha)
            print(
                f"[{n:3d}/{total}] {carga:9s} cap={cap:3d} {pol:4s} "
                f"trab={trab}  rep={rep}  "
                f"acerto={linha['taxa_acerto']:6.1%}  "
                f"subst={linha['substituicoes']:3d}  "
                f"total={linha['tempo_total_s']:6.2f}s  "
                f"econ={linha['tempo_economizado_s']:6.2f}s"
            )

    with open(csv_saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    log.registrar(evento="fim", execucoes=len(linhas))
    log.fechar()

    print(f"\nCSV:  {csv_saida}")
    print(f"Log:  {RESULTADOS / 'c4_eventos.jsonl'}")

    chaves = sorted({
        (l["carga"], l["capacidade"], l["politica"], l["trabalhadores"])
        for l in linhas
    })

    def grupo_de(k):
        return [
            l for l in linhas
            if (l["carga"], l["capacidade"], l["politica"],
                l["trabalhadores"]) == k
        ]

    # resumo por configuração (média das repetições)
    print("\n" + "=" * 72)
    print("RESUMO — média das repetições")
    print("=" * 72)
    print(f"{'carga':10s} {'cap':>4s} {'pol':>5s} {'trab':>5s} "
          f"{'acerto':>8s} {'subst':>6s} {'total_s':>8s} {'econ_s':>8s} "
          f"{'p95_ms':>8s}")
    for k in chaves:
        g = grupo_de(k)
        med = lambda c: statistics.mean(l[c] for l in g)  # noqa: E731
        print(f"{k[0]:10s} {k[1]:4d} {k[2]:>5s} {k[3]:5d} "
              f"{med('taxa_acerto'):7.1%} {med('substituicoes'):6.0f} "
              f"{med('tempo_total_s'):8.2f} {med('tempo_economizado_s'):8.2f} "
              f"{med('lat_p95_ms'):8.1f}")

    # dispersão dos tempos — mesmo tratamento usado em C5/C6
    print("\n" + "=" * 72)
    print("DISPERSÃO DOS TEMPOS — média, desvio-padrão, mínimo, máximo")
    print("=" * 72)
    print(f"{'configuracao':34s} {'media_s':>10s} {'desvio_s':>10s} "
          f"{'min_s':>9s} {'max_s':>9s}")
    estat: list[dict] = []
    for k in chaves:
        g = grupo_de(k)
        tempos = [l["tempo_total_s"] for l in g]
        rotulo = f"C4 — {k[0]}, cap {k[1]}, {k[2].upper()}, {k[3]} trab."
        d = {
            "configuracao": rotulo,
            "repeticoes": len(tempos),
            "media_s": round(statistics.mean(tempos), 6),
            "desvio_padrao_s": round(
                statistics.stdev(tempos), 6) if len(tempos) > 1 else 0.0,
            "minimo_s": round(min(tempos), 6),
            "maximo_s": round(max(tempos), 6),
        }
        estat.append(d)
        print(f"{rotulo:34s} {d['media_s']:10.6f} "
              f"{d['desvio_padrao_s']:10.6f} {d['minimo_s']:9.6f} "
              f"{d['maximo_s']:9.6f}")

    csv_estat = RESULTADOS / (
        "c4_validacao_estatisticas.csv" if args.validacao
        else "c4_estatisticas.csv"
    )
    with open(csv_estat, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(estat[0].keys()))
        w.writeheader()
        w.writerows(estat)
    print(f"\nEstatísticas: {csv_estat}")


if __name__ == "__main__":
    main()