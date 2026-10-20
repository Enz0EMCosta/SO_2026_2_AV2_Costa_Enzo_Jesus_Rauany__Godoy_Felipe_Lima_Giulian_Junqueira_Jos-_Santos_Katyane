
""" Recuperação + Geração — métricas de desempenho
GenResearch-Servidor — bloco 4 — Rauany """
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

from servidor.armazenamento.sqlite_index import SQLiteIndex  # noqa: E402
from servidor.resposta import ResultadoResposta, criar_gerador_resposta  # noqa: E402

RESULTADOS = RAIZ / "experimentos" / "resultados"
CORPORA_DIR = RAIZ / "experimentos" / "recuperacao_corpora"

CORPUS_ALVOS = {"pequeno": 32 * 1024, "medio": 256 * 1024, "grande": 1024 * 1024}

VOCABULARIO = [
    "processo", "memoria", "pagina", "arquivo", "sistema", "operacional",
    "vetor", "indice", "leitura", "armazenamento", "fila", "mutex",
    "semaforo", "cache", "deadlock", "concorrencia",
]
TEMAS = [
    "memoria virtual", "paginacao", "cache de paginas", "mmap",
    "fila de requisicoes", "mutex e semaforos", "condicao de corrida",
    "indice vetorial", "embeddings", "RAG",
]
MOLDES = [
    "o que e {}", "explique {} em detalhes", "como funciona {} no linux",
    "qual a relacao entre {} e desempenho",
]


# ======================================================================
# Log com escrita concorrente protegida (mesmo padrão de c4_cache.py)
# ======================================================================
class LogProtegido:
    """PROVISÓRIO — substituir pela implementação oficial de servidor/logs
    quando ela existir (mesmo aviso usado em c4_cache.py)."""

    def __init__(self, caminho: Path) -> None:
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
# Corpus sintético e construção do índice (via CLI real da ingestão)
# ======================================================================
def criar_corpus(nome: str, alvo_bytes: int) -> Path:
    pasta = CORPORA_DIR / nome
    pasta.mkdir(parents=True, exist_ok=True)
    for item in pasta.glob("*.txt"):
        item.unlink()
    numero, escritos, indice = 0, 0, 0
    while escritos < alvo_bytes:
        texto = " ".join(VOCABULARIO[(indice + offset) % len(VOCABULARIO)] for offset in range(400))
        texto += f" documento {numero}.\n"
        caminho = pasta / f"doc-{numero:04d}.txt"
        caminho.write_text(texto, encoding="utf-8")
        escritos += caminho.stat().st_size
        indice += 3
        numero += 1
    return pasta


def construir_indice(nome_corpus: str, caminho_corpus: Path, dimensao: int = 128) -> Path:
    banco = CORPORA_DIR / f"{nome_corpus}.sqlite3"
    resumos = CORPORA_DIR / "resumos"
    resumos.mkdir(exist_ok=True)
    if banco.exists():
        banco.unlink()
    comando = [
        sys.executable, "-X", "utf8", "-m", "servidor.ingestao.pipeline",
        str(caminho_corpus.relative_to(RAIZ)),
        "--database", str(banco.relative_to(RAIZ)),
        "--summaries", str(resumos.relative_to(RAIZ)),
        "--read-mode", "standard",
        "--chunk-words", "200",
        "--overlap-words", "40",
        "--dimension", str(dimensao),
    ]
    subprocess.run(comando, cwd=RAIZ, check=True, capture_output=True, text=True, encoding="utf-8")
    return banco


def montar_consultas(quantidade: int, semente: int) -> list[str]:
    rng = random.Random(semente)
    return [f"{rng.choice(MOLDES).format(rng.choice(TEMAS))} caso {i}" for i in range(quantidade)]


def coletar_ambiente() -> dict:
    def shell(cmd: str) -> str:
        try:
            return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
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


# ======================================================================
# Execução de uma configuração
# ======================================================================
def executar(nome_corpus: str, banco: Path, top_k: int, trabalhadores: int,
             consultas: list[str], log: LogProtegido, repeticao: int) -> list[dict]:
    indice = SQLiteIndex(banco)
    eventos: list[ResultadoResposta] = []
    gerar_resposta = criar_gerador_resposta(indice, top_k=top_k, registrador=eventos.append)

    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
        list(pool.map(gerar_resposta, consultas))
    duracao_lote = time.perf_counter() - inicio
    indice.close()

    linhas = []
    for consulta, evento in zip(consultas, eventos):
        linhas.append({
            "horario": datetime.now().astimezone().isoformat(),
            "configuracao": "recuperacao_geracao",
            "corpus": nome_corpus,
            "top_k": top_k,
            "trabalhadores": trabalhadores,
            "repeticao": repeticao,
            "consulta": consulta[:60],
            "trechos_recuperados": evento.trechos_recuperados,
            "bytes_contexto": evento.bytes_contexto,
            "tempo_recuperacao_s": evento.tempo_recuperacao_s,
            "tempo_geracao_s": evento.tempo_geracao_s,
            "tempo_total_s": evento.tempo_total_s,
        })
    log.registrar(evento="execucao_concluida", corpus=nome_corpus, top_k=top_k,
                  trabalhadores=trabalhadores, repeticao=repeticao,
                  consultas=len(consultas), duracao_lote_s=round(duracao_lote, 4))
    return linhas


# ======================================================================
# Matriz experimental (mesmo padrão de c4_cache.py: um fator por vez a
# partir de uma configuração base — top_k=4, trabalhadores=4)
# ======================================================================
def montar_matriz() -> list[tuple[str, int, int]]:
    base_top_k, base_trab = 4, 4
    configs: list[tuple[str, int, int]] = []
    for corpus in CORPUS_ALVOS:
        for top_k in (2, 4, 8):
            configs.append((corpus, top_k, base_trab))
        for trab in (1, 2, 4):
            configs.append((corpus, base_top_k, trab))
    vistos, unicas = set(), []
    for c in configs:
        if c not in vistos:
            vistos.add(c)
            unicas.append(c)
    return unicas


def main() -> None:
    ap = argparse.ArgumentParser(description="Recuperação + geração — métricas de desempenho")
    ap.add_argument("--consultas", type=int, default=60, help="consultas por execução (padrão: 60)")
    ap.add_argument("--repeticoes", type=int, default=3, help="repetições por configuração (padrão: 3)")
    ap.add_argument("--semente", type=int, default=7)
    args = ap.parse_args()

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    CORPORA_DIR.mkdir(parents=True, exist_ok=True)
    csv_saida = RESULTADOS / "recuperacao_geracao_resultados.csv"
    log = LogProtegido(RESULTADOS / "recuperacao_geracao_eventos.jsonl")

    ambiente = coletar_ambiente()
    log.registrar(evento="inicio", ambiente=ambiente, parametros=vars(args))

    print("=" * 72)
    print("MÉTRICAS — RECUPERAÇÃO + GERAÇÃO (bloco 4)")
    print("=" * 72)
    for k, v in ambiente.items():
        print(f"  {k:10s} {v}")
    print()

    print("Construindo corpora e índices...")
    bancos: dict[str, Path] = {}
    for nome, alvo in CORPUS_ALVOS.items():
        caminho_corpus = criar_corpus(nome, alvo)
        bancos[nome] = construir_indice(nome, caminho_corpus)
        print(f"  {nome:8s} -> {bancos[nome].relative_to(RAIZ)}")
    print()

    matriz = montar_matriz()
    total = len(matriz) * args.repeticoes
    print(f"{len(matriz)} configurações x {args.repeticoes} repetições = {total} execuções\n")

    todas_linhas: list[dict] = []
    n = 0
    for corpus, top_k, trab in matriz:
        for rep in range(1, args.repeticoes + 1):
            n += 1
            consultas = montar_consultas(args.consultas, semente=args.semente + rep)
            linhas = executar(corpus, bancos[corpus], top_k, trab, consultas, log, rep)
            todas_linhas.extend(linhas)
            tempos_ms = [l["tempo_total_s"] * 1000 for l in linhas]
            print(f"[{n:3d}/{total}] corpus={corpus:8s} top_k={top_k} trab={trab} "
                  f"rep={rep}  media_total={statistics.mean(tempos_ms):7.2f}ms")

    with open(csv_saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(todas_linhas[0].keys()))
        w.writeheader()
        w.writerows(todas_linhas)
    log.registrar(evento="fim", execucoes=len(todas_linhas))
    log.fechar()

    print(f"\nCSV: {csv_saida}")

    # resumo com média, mediana e p95 — item 10 do enunciado
    print("\n" + "=" * 72)
    print("RESUMO — tempo total por consulta (ms): média, mediana, p95")
    print("=" * 72)
    chaves = sorted({(l["corpus"], l["top_k"], l["trabalhadores"]) for l in todas_linhas})
    estat = []
    for chave in chaves:
        grupo = [l for l in todas_linhas if (l["corpus"], l["top_k"], l["trabalhadores"]) == chave]
        tempos_ms = sorted(l["tempo_total_s"] * 1000 for l in grupo)
        p95 = tempos_ms[min(int(0.95 * len(tempos_ms)), len(tempos_ms) - 1)]
        d = {
            "corpus": chave[0], "top_k": chave[1], "trabalhadores": chave[2],
            "n": len(tempos_ms),
            "media_ms": round(statistics.mean(tempos_ms), 3),
            "mediana_ms": round(statistics.median(tempos_ms), 3),
            "p95_ms": round(p95, 3),
            "media_trechos": round(statistics.mean(l["trechos_recuperados"] for l in grupo), 2),
            "media_bytes_contexto": round(statistics.mean(l["bytes_contexto"] for l in grupo), 1),
        }
        estat.append(d)
        print(f"corpus={d['corpus']:8s} top_k={d['top_k']} trab={d['trabalhadores']}  "
              f"media={d['media_ms']:7.2f}  mediana={d['mediana_ms']:7.2f}  p95={d['p95_ms']:7.2f}  "
              f"trechos={d['media_trechos']:.1f}  contexto={d['media_bytes_contexto']:.0f}B")

    csv_estat = RESULTADOS / "recuperacao_geracao_estatisticas.csv"
    with open(csv_estat, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(estat[0].keys()))
        w.writeheader()
        w.writerows(estat)
    print(f"\nEstatísticas: {csv_estat}")


if __name__ == "__main__":
    main()
