import json
import threading
from dataclasses import asdict
from pathlib import Path

import integracao_cache
from servidor.armazenamento.sqlite_index import SQLiteIndex
from servidor.resposta import criar_gerador_resposta

RAIZ = Path(__file__).resolve().parents[2]


def main():
    banco = (
        RAIZ / "experimentos/resultados/venisson_integrado/indice.sqlite3"
    )
    if not banco.is_file():
        raise SystemExit("Gere o índice SQLite antes de executar.")

    eventos = []
    trava = threading.Lock()

    def registrar(resultado):
        with trava:
            eventos.append(asdict(resultado))

    indice = SQLiteIndex(banco)
    try:
        if indice.counts()["chunks"] == 0:
            raise ValueError("O índice está vazio.")
        gerar = criar_gerador_resposta(indice, registrador=registrar)
    finally:
        indice.close()

    # Adapta a resposta textual ao contrato da demonstração da fila.
    def processar(consulta):
        return {
            "consulta": consulta,
            "resposta": gerar(consulta),
            "simulado": True,
        }

    integracao_cache.PERGUNTAS = [
        "O que administra um sistema operacional?",
        "Quais recursos envolvem memória e arquivos?",
    ] * 3
    integracao_cache.processar_consulta = processar
    integracao_cache.main()

    # O registrador é chamado somente quando há geração, não nos hits.
    assert len(eventos) == integracao_cache.cache.metricas.erros
    print("\nMÉTRICAS DAS GERAÇÕES — RAUANY")
    for evento in eventos:
        print(json.dumps(evento, ensure_ascii=False))


if __name__ == "__main__":
    main()
