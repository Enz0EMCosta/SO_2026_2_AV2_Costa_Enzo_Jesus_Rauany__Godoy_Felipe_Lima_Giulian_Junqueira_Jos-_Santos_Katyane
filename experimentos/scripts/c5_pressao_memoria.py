
import argparse
import csv
import os
import platform
import resource
import time
from datetime import datetime
from pathlib import Path

# Configurações iniciais seguras para o WSL2
CARGAS_MIB = [100, 250, 500]
REPETICOES = 3
RESERVA_SEGURANCA_MIB = 1024

RESULTADOS = Path(__file__).resolve().parents[1] / "resultados"
ARQUIVO_CSV = RESULTADOS / "c5_pressao_memoria.csv"


def memoria_linux():
    """Consulta a memória RAM e o swap pelo /proc/meminfo."""
    dados = {}

    with open("/proc/meminfo", encoding="utf-8") as arquivo:
        for linha in arquivo:
            chave, valor = linha.split(":", 1)
            dados[chave] = int(valor.strip().split()[0])

    return {
        "disponivel_mib": dados["MemAvailable"] / 1024,
        "swap_usado_mib": (
            dados["SwapTotal"] - dados["SwapFree"]
        ) / 1024,
    }


def memoria_processo():
    """Consulta RSS, VSZ e faltas de página do processo atual."""
    with open("/proc/self/status", encoding="utf-8") as arquivo:
        linhas = arquivo.readlines()

    valores = {}

    for linha in linhas:
        if linha.startswith(("VmRSS:", "VmSize:")):
            chave, valor = linha.split(":", 1)
            valores[chave] = int(valor.strip().split()[0]) / 1024

    uso = resource.getrusage(resource.RUSAGE_SELF)

    return {
        "rss_mib": valores.get("VmRSS", 0),
        "vsz_mib": valores.get("VmSize", 0),
        "faltas_menores": uso.ru_minflt,
        "faltas_maiores": uso.ru_majflt,
    }


def executar_teste(carga_mib, repeticao):
    antes_memoria = memoria_linux()
    antes_processo = memoria_processo()

    if antes_memoria["disponivel_mib"] < (
        carga_mib + RESERVA_SEGURANCA_MIB
    ):
        print(f"Teste ignorado: memória insuficiente para {carga_mib} MiB.")
        return None

    inicio = time.perf_counter()

    # Aloca memória e toca cada página para materializar a carga.
    bloco = bytearray(carga_mib * 1024 * 1024)

    for posicao in range(0, len(bloco), 4096):
        bloco[posicao] = 1

    # Mantém os dados alocados enquanto realiza a medição.
    processo = memoria_processo()
    sistema = memoria_linux()

    tempo = time.perf_counter() - inicio

    resultado = {
        "horario": datetime.now().astimezone().isoformat(),
        "ambiente": platform.platform(),
        "python": platform.python_version(),
        "pid": os.getpid(),
        "configuracao": "C5",
        "carga_mib": carga_mib,
        "repeticao": repeticao,
        "tempo_s": round(tempo, 6),
        "rss_mib": round(processo["rss_mib"], 2),
        "vsz_mib": round(processo["vsz_mib"], 2),
        "memavailable_mib": round(sistema["disponivel_mib"], 2),
        "swap_usado_mib": round(sistema["swap_usado_mib"], 2),
        "faltas_menores_delta": (
            processo["faltas_menores"] - antes_processo["faltas_menores"]
        ),
        "faltas_maiores_delta": (
            processo["faltas_maiores"] - antes_processo["faltas_maiores"]
        ),
    }

    del bloco
    return resultado


def main():
    parser = argparse.ArgumentParser(
        description="Experimento C5: pressão de memória controlada."
    )
    parser.add_argument(
        "--carga",
        type=int,
        choices=CARGAS_MIB,
        default=100,
        help="Carga em MiB: 100, 250 ou 500.",
    )
    parser.add_argument(
        "--repeticoes",
        type=int,
        default=REPETICOES,
    )

    args = parser.parse_args()

    if args.repeticoes < 1:
        parser.error("O número de repetições deve ser positivo.")

    RESULTADOS.mkdir(parents=True, exist_ok=True)

    for repeticao in range(1, args.repeticoes + 1):
        resultado = executar_teste(args.carga, repeticao)

        if resultado is None:
            break

        novo_arquivo = not ARQUIVO_CSV.exists() or ARQUIVO_CSV.stat().st_size == 0

        with open(ARQUIVO_CSV, "a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(
                arquivo, fieldnames=resultado.keys()
            )
            if novo_arquivo:
                escritor.writeheader()
            escritor.writerow(resultado)

        print(
            f"C5 | carga={args.carga} MiB | "
            f"repetição={repeticao} | "
            f"tempo={resultado['tempo_s']}s | "
            f"RSS={resultado['rss_mib']} MiB | "
            f"swap={resultado['swap_usado_mib']} MiB"
        )

    print(f"\nResultados salvos em: {ARQUIVO_CSV}")


if __name__ == "__main__":
    main()
