import threading
import time
import fila

descartadas = []


def produtor_sem_espera(numero):
    for indice in range(fila.CONSULTAS_POR_PRODUTOR):
        consulta = f"P{numero}-Q{indice}"

        # Falha proposital: não aguarda uma vaga.
        if not fila.empty.acquire(blocking=False):
            with fila.mutex:
                descartadas.append(consulta)
            fila.registrar(f"DESCARTADA {consulta}: fila cheia")
            continue

        with fila.mutex:
            fila.buffer.append((consulta, time.perf_counter()))
            tamanho = len(fila.buffer)
            fila.tamanho_maximo = max(fila.tamanho_maximo, tamanho)

        fila.full.release()
        fila.registrar(f"ACEITA {consulta} | fila={tamanho}")


def main():
    produtores = [
        threading.Thread(target=produtor_sem_espera, args=(i,))
        for i in range(fila.PRODUTORES)
    ]
    consumidores = [
        threading.Thread(target=fila.consumidor, args=(i,))
        for i in range(fila.CONSUMIDORES)
    ]

    print("FALHA CONTROLADA: consumidores inicialmente pausados")

    for thread in produtores:
        thread.start()
    for thread in produtores:
        thread.join()

    print("Liberando consumidores para esvaziar o buffer")

    for thread in consumidores:
        thread.start()

    for _ in consumidores:
        fila.inserir(None)

    for thread in consumidores:
        thread.join()

    esperadas = {
        f"P{p}-Q{q}"
        for p in range(fila.PRODUTORES)
        for q in range(fila.CONSULTAS_POR_PRODUTOR)
    }
    concluidas = set(fila.processadas)

    print("\nRESULTADO DA FALHA")
    print(f"Consultas enviadas: {len(esperadas)}")
    print(f"Processadas: {len(fila.processadas)}")
    print(f"Descartadas: {len(descartadas)}")
    print(f"Não processadas: {len(esperadas - concluidas)}")
    print(f"Duplicadas: {len(fila.processadas) - len(concluidas)}")
    print(f"Tamanho máximo do buffer: {fila.tamanho_maximo}")
    assert len(descartadas) == 9
    assert len(concluidas) == 3
    assert concluidas.isdisjoint(descartadas)
    assert concluidas | set(descartadas) == esperadas
    print("Falha reproduzida e todas as consultas contabilizadas.")


if __name__ == "__main__":
    main()
