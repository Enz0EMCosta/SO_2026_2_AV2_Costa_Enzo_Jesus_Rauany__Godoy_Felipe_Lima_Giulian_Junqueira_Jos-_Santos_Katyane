from processamento import processar_consulta
import threading
import math
import statistics
import time
from collections import deque

CAPACIDADE = 3
PRODUTORES = 2
CONSUMIDORES = 2
CONSULTAS_POR_PRODUTOR = 6

buffer = deque()
empty = threading.Semaphore(CAPACIDADE)
full = threading.Semaphore(0)
mutex = threading.Lock()
log_lock = threading.Lock()

processadas = []
esperas = []
tamanho_maximo = 0
envios = {}
latencias = []
tempo_ocupado = {}
fila_consultas = 0
area_fila = 0.0
ultima_medicao = time.perf_counter()


def atualizar_area_fila():
    # Chamar somente com mutex adquirido.
    global area_fila, ultima_medicao
    agora = time.perf_counter()
    area_fila += fila_consultas * (agora - ultima_medicao)
    ultima_medicao = agora


def registrar(mensagem):
    with log_lock:
        print(mensagem, flush=True)


def inserir(item):
    global tamanho_maximo, fila_consultas
    inicio = time.perf_counter()

    empty.acquire()
    bloqueio = time.perf_counter() - inicio

    with mutex:
        atualizar_area_fila()
        buffer.append((item, time.perf_counter()))
        if item is not None:
            fila_consultas += 1
        tamanho = len(buffer)
        tamanho_maximo = max(tamanho_maximo, tamanho)

    full.release()
    return tamanho, bloqueio


def retirar():
    global fila_consultas
    full.acquire()

    with mutex:
        atualizar_area_fila()
        item, entrada = buffer.popleft()
        if item is not None:
            fila_consultas -= 1
        espera = time.perf_counter() - entrada
        tamanho = len(buffer)

    empty.release()
    return item, espera, tamanho


def produtor(numero):
    for indice in range(CONSULTAS_POR_PRODUTOR):
        consulta = f"P{numero}-Q{indice}"
        with mutex:
            envios[consulta] = time.perf_counter()
        tamanho, bloqueio = inserir(consulta)
        registrar(
            f"PRODUZIDA {consulta} | fila após inserção={tamanho} "
            f"| espera por vaga={bloqueio:.4f}s"
        )


def consumidor(numero):
    while True:
        consulta, espera, tamanho = retirar()

        if consulta is None:
            return

        registrar(
            f"CONSUMIDOR {numero} iniciou {consulta} "
            f"| espera na fila={espera:.4f}s "
            f"| fila após retirada={tamanho}"
        )

        # Simula a recuperação/geração da resposta.
        inicio_processamento = time.perf_counter()
        resultado = processar_consulta(consulta)
        fim_processamento = time.perf_counter()

        with mutex:
            processadas.append(consulta)
            esperas.append(espera)
            if consulta in envios:
                latencias.append(fim_processamento - envios[consulta])
            tempo_ocupado[numero] = (
                tempo_ocupado.get(numero, 0.0)
                + fim_processamento - inicio_processamento
            )

        registrar(f"CONSUMIDOR {numero} concluiu {consulta}")


def main():
    global area_fila, ultima_medicao
    inicio = time.perf_counter()
    area_fila = 0.0
    ultima_medicao = inicio

    consumidores = [
        threading.Thread(target=consumidor, args=(i,))
        for i in range(CONSUMIDORES)
    ]
    produtores = [
        threading.Thread(target=produtor, args=(i,))
        for i in range(PRODUTORES)
    ]

    for thread in consumidores + produtores:
        thread.start()

    for thread in produtores:
        thread.join()

    # Uma mensagem de encerramento por consumidor.
    for _ in consumidores:
        inserir(None)

    for thread in consumidores:
        thread.join()

    with mutex:
        atualizar_area_fila()
        duracao = ultima_medicao - inicio
        tamanho_medio = area_fila / duracao
    esperadas = {
        f"P{p}-Q{q}"
        for p in range(PRODUTORES)
        for q in range(CONSULTAS_POR_PRODUTOR)
    }
    recebidas = set(processadas)

    print("\nRESULTADO")
    print(f"Consultas esperadas: {len(esperadas)}")
    print(f"Consultas processadas: {len(processadas)}")
    print(f"Perdidas: {len(esperadas - recebidas)}")
    print(f"Duplicadas: {len(processadas) - len(recebidas)}")
    print(f"Tamanho máximo do buffer: {tamanho_maximo}/{CAPACIDADE}")
    print(f"Tamanho médio da fila (ponderado pelo tempo): {tamanho_medio:.4f}")
    print(f"Espera média na fila: {sum(esperas)/len(esperas):.4f}s")
    print(f"Tempo total: {duracao:.4f}s")
    print(f"Vazão: {len(processadas)/duracao:.2f} consultas/s")
    ordenadas = sorted(latencias)
    p95 = ordenadas[math.ceil(0.95 * len(ordenadas)) - 1]
    print(f"Latência média: {statistics.mean(latencias):.4f}s")
    print(f"Latência mediana: {statistics.median(latencias):.4f}s")
    print(f"Latência p95 (posto mais próximo): {p95:.4f}s")
    for numero in range(CONSUMIDORES):
        utilizacao = tempo_ocupado.get(numero, 0.0) / duracao
        print(f"Utilização consumidor {numero}: {utilizacao:.1%}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="C3: fila limitada com produtores e consumidores."
    )
    parser.add_argument("--produtores", type=int, default=2)
    parser.add_argument("--consumidores", type=int, default=2)
    parser.add_argument("--capacidade", type=int, default=3)
    parser.add_argument("--consultas-por-produtor", type=int, default=6)
    args = parser.parse_args()

    if min(
        args.produtores,
        args.consumidores,
        args.capacidade,
        args.consultas_por_produtor,
    ) < 1:
        parser.error("Todos os parâmetros devem ser maiores que zero.")

    PRODUTORES = args.produtores
    CONSUMIDORES = args.consumidores
    CAPACIDADE = args.capacidade
    CONSULTAS_POR_PRODUTOR = args.consultas_por_produtor

    empty = threading.Semaphore(CAPACIDADE)
    full = threading.Semaphore(0)

    print(
        f"CONFIGURAÇÃO: produtores={PRODUTORES}, "
        f"consumidores={CONSUMIDORES}, capacidade={CAPACIDADE}, "
        f"consultas_por_produtor={CONSULTAS_POR_PRODUTOR}",
        flush=True,
    )
    main()
