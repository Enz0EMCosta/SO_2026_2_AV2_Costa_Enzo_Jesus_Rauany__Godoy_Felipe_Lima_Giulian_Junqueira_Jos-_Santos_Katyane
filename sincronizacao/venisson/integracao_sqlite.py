from pathlib import Path

import integracao_cache
from processamento_sqlite import criar_processador

RAIZ = Path(__file__).resolve().parents[2]


def main():
    banco = (
        RAIZ / "experimentos/resultados/venisson_integrado/indice.sqlite3"
    )
    processador = criar_processador(banco)

    # Confere recuperação para uma consulta e ausência para outra.
    exemplo = processador("O que administra um sistema operacional?")
    assert exemplo["fontes"], "Não recuperou o trecho esperado."
    assert not processador("Receita de bolo")["fontes"]

    print("Fonte recuperada:", exemplo["fontes"])
    print("Contexto:", exemplo["contexto"])
    print("Bytes de contexto:", exemplo["contexto_bytes"])
    print("Recuperação verificada.\n")

    # Duas perguntas repetidas, com IDs únicos por requisição.
    integracao_cache.PERGUNTAS = [
        "O que administra um sistema operacional?",
        "Quais recursos envolvem memória e arquivos?",
    ] * 3
    integracao_cache.processar_consulta = processador
    integracao_cache.main()


if __name__ == "__main__":
    main()
