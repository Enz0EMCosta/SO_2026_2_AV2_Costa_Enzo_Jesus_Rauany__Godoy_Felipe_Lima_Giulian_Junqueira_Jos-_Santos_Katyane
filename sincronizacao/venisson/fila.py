from processamento import processar_consulta
import threading
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


def registrar(mensagem):
    with log_lock:
        print(mensagem, flush=True)


def inserir(item):
    global tamanho_maximo
    inicio = time.perf_counter()

    empty.acquire()
    bloqueio = time.perf_counter() - inicio

    with mutex:
        buffer.append((item, time.perf_counter()))
        tamanho = len(buffer)
        tamanho_maximo = max(tamanho_maximo, tamanho)

    full.release()
    return tamanho, bloqueio


def retirar():
    full.acquire()

    with mutex:
        item, entrada = buffer.popleft()
        espera = time.perf_counter() - entrada
        tamanho = len(buffer)

    empty.release()
    return item, espera, tamanho


def produtor(numero):
    for indice in range(CONSULTAS_POR_PRODUTOR):
        consulta = f"P{numero}-Q{indice}"
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
        resultado = processar_consulta(consulta)

        with mutex:
            processadas.append(consulta)
            esperas.append(espera)

        registrar(f"CONSUMIDOR {numero} concluiu {consulta}")


def main():
    inicio = time.perf_counter()

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

    duracao = time.perf_counter() - inicio
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
    print(f"Espera média na fila: {sum(esperas)/len(esperas):.4f}s")
    print(f"Tempo total: {duracao:.4f}s")
    print(f"Vazão: {len(processadas)/duracao:.2f} consultas/s")


if __name__ == "__main__":
    main()
