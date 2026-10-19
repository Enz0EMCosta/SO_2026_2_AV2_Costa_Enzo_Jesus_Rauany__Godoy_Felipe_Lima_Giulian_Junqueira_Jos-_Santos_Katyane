
# Análise dos Experimentos C5 e C6

## 1. Objetivo

Avaliar o comportamento do sistema operacional Linux em dois cenários:

- C5: aumento controlado do consumo de memória.
- C6: tratamento de falha causada pela tentativa de leitura de um arquivo inexistente.

Os testes apresentados são experimentos sintéticos independentes,
utilizados como etapa preliminar de avaliação. Não representam
medições do pipeline completo do GenResearch-Servidor.

## 2. Ambiente de execução

- Sistema operacional: Linux em WSL2
- Kernel: 6.18.33.2-microsoft-standard-WSL2
- Linguagem: Python 3.14.4
- Memória RAM disponível no ambiente: aproximadamente 4,8 GiB no total
- Swap configurada: 4,0 GiB

## 3. Experimento C5 — Pressão de memória

### 3.1 Metodologia

Foi desenvolvido um script Python que aloca blocos de memória
de 100, 250 e 500 MiB.

Cada bloco é acessado em intervalos de 4 KiB para provocar
o mapeamento das páginas de memória.

Foram realizadas três repetições para cada carga, totalizando
nove medições.

As métricas coletadas foram:

- Tempo de execução;
- RSS (memória física residente);
- VSZ (memória virtual do processo);
- MemAvailable;
- Swap utilizada;
- Faltas de página menores e maiores.

### 3.2 Comandos utilizados

```bash
python3 experimentos/scripts/c5_pressao_memoria.py --carga 100 --repeticoes 3
python3 experimentos/scripts/c5_pressao_memoria.py --carga 250 --repeticoes 3
python3 experimentos/scripts/c5_pressao_memoria.py --carga 500 --repeticoes 3
```

### 3.3 Resultados

| Carga | Tempo médio (s) | RSS médio (MiB) | Faltas menores por repetição | Faltas maiores | Swap (MiB) |
|---|---:|---:|---:|---:|---:|
| 100 MiB | 0,138452 | 116,20 | 25.601 | 0 | 0 |
| 250 MiB | 0,280650 | 266,21 | 64.001 | 0 | 0 |
| 500 MiB | 0,554763 | 516,18 | 128.001 | 0 | 0 |

### 3.4 Análise

O aumento da carga resultou em maior consumo de memória física
e maior tempo médio de execução.

As faltas menores aumentaram proporcionalmente ao volume de
memória acessado. Não foram observadas faltas maiores nem
utilização de swap durante as medições.

Portanto, o experimento demonstrou o custo crescente da
alocação e do acesso à memória, mas não evidenciou esgotamento
da RAM ou degradação decorrente de uso de swap.

As três repetições de cada carga foram executadas no mesmo
processo Python, o que pode influenciar os tempos observados.

## 4. Experimento C6 — Falha controlada

### 4.1 Metodologia

Foi desenvolvido um script que tenta ler um arquivo inexistente.

O erro FileNotFoundError é capturado e registrado, permitindo
que o programa continue até finalizar as repetições previstas.

Foram realizadas três tentativas.

### 4.2 Comando utilizado

```bash
python3 experimentos/scripts/c6_falha_controlada.py --repeticoes 3
```

### 4.3 Resultados

| Repetição | Status | Erro | Tempo (s) |
|---|---|---|---:|
| 1 | falha_tratada | FileNotFoundError | 0,002365 |
| 2 | falha_tratada | FileNotFoundError | 0,002272 |
| 3 | falha_tratada | FileNotFoundError | 0,002932 |

Tempo médio: 0,002523 s.

Taxa de tratamento no cenário testado: 3 de 3 tentativas (100%).

### 4.4 Análise

O programa identificou e tratou corretamente as três
tentativas de acesso ao arquivo inexistente.

Não ocorreram exceções não tratadas durante as medições.

O resultado demonstra o funcionamento do mecanismo de
tratamento de falha no script independente, sem comprovar
a recuperação de falhas no GenResearch-Servidor completo.

## 5. Limitações e próximos passos

Os experimentos foram executados em scripts independentes.

Na C5, as cargas não foram suficientes para provocar uso
observado de swap ou faltas maiores de página.

Na C6, foi avaliado somente o cenário de arquivo inexistente.

Será necessário relacionar esses cenários ao GenResearch-Servidor
da equipe e, quando o pipeline estiver disponível, realizar
testes integrados.

Também será necessária a consolidação dos resultados das
configurações C1 a C4, desenvolvidas pelos demais integrantes.

## 6. Arquivos de evidência

- experimentos/scripts/c5_pressao_memoria.py
- experimentos/scripts/c6_falha_controlada.py
- experimentos/resultados/c5_pressao_memoria.csv
- experimentos/resultados/c6_falha_controlada.csv
- experimentos/resultados/c5_validacao.csv
- experimentos/resultados/c6_validacao.csv
```
