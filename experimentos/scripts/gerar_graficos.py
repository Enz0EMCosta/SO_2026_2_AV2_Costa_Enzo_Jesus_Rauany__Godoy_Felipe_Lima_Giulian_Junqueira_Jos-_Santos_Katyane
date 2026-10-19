
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
RESULTADOS = BASE / "resultados"
GRAFICOS = RESULTADOS / "graficos"


def ler_csv(nome):
    caminho = RESULTADOS / nome
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_graficos_c5():
    dados = ler_csv("c5_pressao_memoria.csv")
    grupos = defaultdict(list)

    for linha in dados:
        carga = int(linha["carga_mib"])
        grupos[carga].append(linha)

    cargas = sorted(grupos)

    tempos = [
        sum(float(linha["tempo_s"]) for linha in grupos[carga])
        / len(grupos[carga])
        for carga in cargas
    ]

    rss = [
        sum(float(linha["rss_mib"]) for linha in grupos[carga])
        / len(grupos[carga])
        for carga in cargas
    ]

    plt.figure(figsize=(8, 5))
    plt.plot(cargas, tempos, marker="o", linewidth=2)
    plt.title("C5 - Tempo medio por carga de memoria")
    plt.xlabel("Carga de memoria (MiB)")
    plt.ylabel("Tempo medio (segundos)")
    plt.xticks(cargas)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(GRAFICOS / "c5_tempo_medio.png", dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.bar([str(carga) for carga in cargas], rss)
    plt.title("C5 - Consumo medio de memoria RAM")
    plt.xlabel("Carga de memoria (MiB)")
    plt.ylabel("RSS medio (MiB)")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(GRAFICOS / "c5_rss_medio.png", dpi=200)
    plt.close()


def gerar_grafico_c6():
    dados = ler_csv("c6_falha_controlada.csv")

    repeticoes = [int(linha["repeticao"]) for linha in dados]
    tempos_ms = [
        float(linha["tempo_s"]) * 1000 for linha in dados
    ]

    plt.figure(figsize=(8, 5))
    plt.bar([str(rep) for rep in repeticoes], tempos_ms)
    plt.title("C6 - Tempo de tratamento da falha")
    plt.xlabel("Repeticao")
    plt.ylabel("Tempo (milissegundos)")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(GRAFICOS / "c6_tempo_falha.png", dpi=200)
    plt.close()


def main():
    GRAFICOS.mkdir(parents=True, exist_ok=True)

    gerar_graficos_c5()
    gerar_grafico_c6()

    print("Graficos gerados com sucesso!")
    print(f"Arquivos salvos em: {GRAFICOS}")


if __name__ == "__main__":
    main()
