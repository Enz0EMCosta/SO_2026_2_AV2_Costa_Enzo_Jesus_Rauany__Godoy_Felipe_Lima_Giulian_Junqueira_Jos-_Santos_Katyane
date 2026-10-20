"""Recuperação lexical do índice do Fagner e resposta simulada."""

import re
import time
import unicodedata
from pathlib import Path

from servidor.armazenamento.sqlite_index import SQLiteIndex


def termos(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    ignoradas = {"o", "a", "os", "as", "um", "uma", "de", "do",
                 "da", "e", "em", "que", "como", "quais"}
    return set(re.findall(r"\w+", texto)) - ignoradas


def criar_processador(banco):
    banco = Path(banco)
    if not banco.is_file():
        raise FileNotFoundError(f"Índice não encontrado: {banco}")

    # Carrega antes das threads e fecha a conexão SQLite.
    indice = SQLiteIndex(banco)
    try:
        trechos = tuple(
            (item["chunk_id"], item["relative_path"], item["text"])
            for lote in indice.iter_chunk_vectors()
            for item in lote
        )
    finally:
        indice.close()

    if not trechos:
        raise ValueError("O índice não contém trechos.")

    def processar(consulta):
        inicio = time.perf_counter()
        palavras = termos(consulta)
        classificados = sorted(
            (
                (len(palavras & termos(texto)), identificador, origem, texto)
                for identificador, origem, texto in trechos
            ),
            key=lambda item: (-item[0], item[1]),
        )

        partes = []
        fontes = []
        restante = 700

        for pontuacao, identificador, origem, texto in classificados[:2]:
            if pontuacao == 0:
                continue
            separador = "\n" if partes else ""
            if restante <= len(separador):
                break
            trecho = texto[:restante - len(separador)]
            partes.append(separador + trecho)
            fontes.append({"arquivo": origem, "trecho_id": identificador})
            restante -= len(separador) + len(trecho)

        contexto = "".join(partes)
        recuperacao = time.perf_counter() - inicio

        inicio_geracao = time.perf_counter()
        time.sleep(0.05 + len(contexto) * 0.0002)
        resposta = (
            f"[Resposta simulada] Contexto recuperado: {contexto}"
            if contexto else
            "[Resposta simulada] Nenhum contexto relevante encontrado."
        )

        return {
            "consulta": consulta,
            "resposta": resposta,
            "simulado": True,
            "fontes": fontes,
            "contexto": contexto,
            "contexto_bytes": len(contexto.encode("utf-8")),
            "tempo_recuperacao_s": recuperacao,
            "tempo_geracao_s": time.perf_counter() - inicio_geracao,
        }

    return processar
