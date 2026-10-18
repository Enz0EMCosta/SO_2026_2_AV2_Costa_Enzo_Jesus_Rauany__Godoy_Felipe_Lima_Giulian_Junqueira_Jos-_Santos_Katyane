
import argparse
import csv
import os
import platform
import time
from datetime import datetime
from pathlib import Path

RESULTADOS = Path(__file__).resolve().parents[1] / "resultados"
ARQUIVO_CSV = RESULTADOS / "c6_falha_controlada.csv"


def executar_teste(arquivo, repeticao):
    inicio = time.perf_counter()
    status = "sucesso"
    tipo_erro = "nenhum"
    mensagem = ""

    try:
        with open(arquivo, "rb") as entrada:
            entrada.read(1024)

    except FileNotFoundError:
        status = "falha_tratada"
        tipo_erro = "FileNotFoundError"
        mensagem = "Arquivo nao encontrado"

    except PermissionError:
        status = "falha_tratada"
        tipo_erro = "PermissionError"
        mensagem = "Acesso negado ao arquivo"

    tempo = time.perf_counter() - inicio

    return {
        "horario": datetime.now().astimezone().isoformat(),
        "ambiente": platform.platform(),
        "python": platform.python_version(),
        "pid": os.getpid(),
        "configuracao": "C6",
        "cenario": "arquivo_inexistente",
        "repeticao": repeticao,
        "arquivo": str(arquivo),
        "status": status,
        "tipo_erro": tipo_erro,
        "mensagem": mensagem,
        "tempo_s": round(tempo, 6),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Experimento C6: falha controlada de leitura."
    )

    parser.add_argument(
        "--arquivo",
        default="experimentos/dados/arquivo_inexistente.txt",
        help="Caminho do arquivo a ser lido.",
    )

    parser.add_argument(
        "--repeticoes",
        type=int,
        default=3,
        help="Numero de repeticoes.",
    )

    args = parser.parse_args()

    if args.repeticoes < 1:
        parser.error("O numero de repeticoes deve ser positivo.")

    RESULTADOS.mkdir(parents=True, exist_ok=True)

    for repeticao in range(1, args.repeticoes + 1):
        resultado = executar_teste(args.arquivo, repeticao)

        novo_arquivo = (
            not ARQUIVO_CSV.exists()
            or ARQUIVO_CSV.stat().st_size == 0
        )

        with open(
            ARQUIVO_CSV, "a", newline="", encoding="utf-8"
        ) as arquivo_csv:
            escritor = csv.DictWriter(
                arquivo_csv, fieldnames=resultado.keys()
            )

            if novo_arquivo:
                escritor.writeheader()

            escritor.writerow(resultado)

        print(
            f"C6 | repeticao={repeticao} | "
            f"status={resultado['status']} | "
            f"erro={resultado['tipo_erro']} | "
            f"tempo={resultado['tempo_s']}s"
        )

    print(f"\nResultados salvos em: {ARQUIVO_CSV}")


if __name__ == "__main__":
    main()
