import threading
import time
import fila


def main():
    produtores = [
        threading.Thread(target=fila.produtor, args=(i,))
        for i in range(fila.PRODUTORES)
    ]
    consumidores = [
        threading.Thread(target=fila.consumidor, args=(i,))
        for i in range(fila.CONSUMIDORES)
    ]

    inicio = time.perf_counter()
    print("CORREÇÃO: produtores aguardam vagas, sem descartar consultas")
    print("Consumidores iniciarão após atraso de 0,5 segundo")

    for thread in produtores:
        thread.start()

    time.sleep(0.5)

    for thread in consumidores:
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
        for p in range(fila.PRODUTORES)
        for q in range(fila.CONSULTAS_POR_PRODUTOR)
    }
    concluidas = set(fila.processadas)
    perdidas = esperadas - concluidas
    duplicadas = len(fila.processadas) - len(concluidas)

    print("\nRESULTADO DA CORREÇÃO")
    print(f"Consultas esperadas: {len(esperadas)}")
    print(f"Processadas: {len(fila.processadas)}")
    print(f"Perdidas: {len(perdidas)}")
    print(f"Duplicadas: {duplicadas}")
    print(f"Tamanho máximo do buffer: {fila.tamanho_maximo}")
    print(f"Tempo total, incluindo atraso: {duracao:.4f}s")

    assert concluidas == esperadas
    assert duplicadas == 0
    assert fila.tamanho_maximo <= fila.CAPACIDADE
    print("Correção verificada: todas as consultas foram processadas.")


if __name__ == "__main__":
    main()
