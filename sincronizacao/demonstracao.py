"""Reproduz uma atualização perdida e demonstra a correção com mutex."""

from threading import Barrier, Lock, Thread


def demonstrar_condicao_de_corrida(iteracoes: int) -> tuple[int, int]:
    contador = 0
    barreira = Barrier(2)

    def incrementar() -> None:
        nonlocal contador
        for _ in range(iteracoes):
            valor_lido = contador
            barreira.wait()
            contador = valor_lido + 1
            barreira.wait()

    trabalhadores = [Thread(target=incrementar) for _ in range(2)]
    for trabalhador in trabalhadores:
        trabalhador.start()
    for trabalhador in trabalhadores:
        trabalhador.join()

    return contador, iteracoes * 2


def demonstrar_correcao(iteracoes: int) -> tuple[int, int]:
    contador = 0
    mutex = Lock()

    def incrementar() -> None:
        nonlocal contador
        for _ in range(iteracoes):
            with mutex:
                contador += 1

    trabalhadores = [Thread(target=incrementar) for _ in range(2)]
    for trabalhador in trabalhadores:
        trabalhador.start()
    for trabalhador in trabalhadores:
        trabalhador.join()

    return contador, iteracoes * 2


def main() -> None:
    iteracoes = 10_000
    observado, esperado = demonstrar_condicao_de_corrida(iteracoes)
    corrigido, total = demonstrar_correcao(iteracoes)

    print(f"Sem mutex: contador={observado}; esperado={esperado}")
    print(f"Com mutex: contador={corrigido}; esperado={total}")

    if observado == esperado:
        raise RuntimeError("A demonstração não reproduziu a atualização perdida.")
    if corrigido != total:
        raise RuntimeError("O contador protegido pelo mutex ficou inconsistente.")


if __name__ == "__main__":
    main()
