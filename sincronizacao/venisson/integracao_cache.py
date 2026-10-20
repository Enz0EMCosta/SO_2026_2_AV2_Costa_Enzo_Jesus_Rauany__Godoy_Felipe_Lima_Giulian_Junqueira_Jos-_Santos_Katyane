import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import fila
from processamento import processar_consulta
from servidor.cache import CacheCompartilhado

# Uma única instância compartilhada pelos consumidores.
cache = CacheCompartilhado(capacidade=8, politica="lru")

PERGUNTAS = [
    "O que é memória virtual?",
    "Como funciona um semáforo?",
    "O que é memória virtual?",
    "Como funciona um semáforo?",
    "O que é memória virtual?",
    "Como funciona um semáforo?",
]

concluidas = []
erros = []
trava_resultados = threading.Lock()


def produtor(numero):
    for indice, pergunta in enumerate(PERGUNTAS):
        requisicao = {
            "id": f"P{numero}-Q{indice}",
            "consulta": pergunta,
        }
        tamanho, espera = fila.inserir(requisicao)
        fila.registrar(
            f"ENVIADA {requisicao['id']} | fila={tamanho} "
            f"| espera por vaga={espera:.4f}s"
        )


def consumidor(numero):
    while True:
        requisicao, espera, tamanho = fila.retirar()

        if requisicao is None:
            return

        identificador = requisicao["id"]
        pergunta = requisicao["consulta"]

        try:
            resposta, acerto, latencia = cache.obter_ou_gerar(
                pergunta, processar_consulta
            )

            if resposta["consulta"] != pergunta:
                raise ValueError("Resposta incompatível com a consulta")

            with trava_resultados:
                concluidas.append(identificador)

            fila.registrar(
                f"CONSUMIDOR {numero} | {identificador} "
                f"| cache={'ACERTO' if acerto else 'ERRO'} "
                f"| espera na fila={espera:.4f}s "
                f"| atendimento={latencia:.4f}s "
                f"| resposta={resposta['resposta']}"
            )

        except Exception as erro:
            with trava_resultados:
                erros.append(identificador)
            fila.registrar(f"FALHA {identificador}: {erro!r}")


def main():
    inicio = time.perf_counter()

    consumidores = [
        threading.Thread(target=consumidor, args=(i,))
        for i in range(2)
    ]
    produtores = [
        threading.Thread(target=produtor, args=(i,))
        for i in range(2)
    ]

    for thread in consumidores + produtores:
        thread.start()

    for thread in produtores:
        thread.join()

    for _ in consumidores:
        fila.inserir(None)

    for thread in consumidores:
        thread.join()

    duracao = time.perf_counter() - inicio
    esperadas = {
        f"P{p}-Q{q}"
        for p in range(2)
        for q in range(len(PERGUNTAS))
    }
    recebidas = set(concluidas)
    metricas = cache.metricas

    print("\nRESULTADO DA INTEGRAÇÃO")
    print(f"Requisições enviadas: {len(esperadas)}")
    print(f"Concluídas: {len(concluidas)}")
    print(f"Falhas de processamento: {len(erros)}")
    print(f"Não concluídas: {len(esperadas - recebidas)}")
    print(f"Duplicadas: {len(concluidas) - len(recebidas)}")
    print(f"Acertos do cache: {metricas.acertos}")
    print(f"Erros do cache (misses): {metricas.erros}")
    print(f"Taxa de acerto: {metricas.taxa_acerto:.1%}")
    print(f"Substituições: {metricas.substituicoes}")
    print(f"Entradas no cache: {metricas.tamanho_atual}")
    print(f"Tamanho máximo do buffer: {fila.tamanho_maximo}/3")
    print(f"Tempo total: {duracao:.4f}s")

    assert recebidas == esperadas, "Há requisições não concluídas"
    assert len(concluidas) == len(recebidas), "Há duplicações"
    assert not erros, "Há falhas de processamento"
    assert metricas.acertos + metricas.erros == len(esperadas)
    assert metricas.tamanho_atual == len(set(PERGUNTAS))
    assert fila.tamanho_maximo <= fila.CAPACIDADE

    print("Integração verificada: fila + cache + resposta simulada.")


if __name__ == "__main__":
    main()
