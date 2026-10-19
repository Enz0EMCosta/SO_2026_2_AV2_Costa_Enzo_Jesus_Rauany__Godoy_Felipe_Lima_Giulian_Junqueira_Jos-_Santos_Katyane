
# Consolidação dos Experimentos C1–C6

## 1. Objetivo

Reunir os resultados das seis configurações experimentais
do projeto GenResearch-Servidor, permitindo comparar
desempenho, uso de memória, comportamento de entrada/saída
e tratamento de falhas.

## 2. Situação das configurações

| Configuração | Descrição | Situação |
|---|---|---|
| C1 | Leitura convencional | Aguardando resultados da equipe |
| C2 | Leitura com mmap | Aguardando resultados da equipe |
| C3 | Processamento com fila | Aguardando resultados da equipe |
| C4 | Utilização de cache | Resultados coletados — 12 configurações × 3 repetições |
| C5 | Pressão de memória | Teste sintético preliminar realizado |
| C6 | Falha controlada | Teste sintético preliminar realizado |

## 3. Resultados disponíveis

### C4 — Cache compartilhado

O experimento C4 avaliou o comportamento de um cache
compartilhado, comparando diferentes capacidades,
políticas de substituição e quantidades de trabalhadores.

Foram realizadas 36 execuções, correspondentes a
12 configurações com 3 repetições cada.

#### Resultados principais

| Métrica | Resultado |
|---|---:|
| Capacidade do cache | 32 entradas |
| Política de substituição | LRU |
| Trabalhadores | 4 |
| Consultas por execução | 200 |
| Taxa média de acerto (consultas repetidas) | 71,2% |
| Tempo médio do lote | 0,222833 s |
| Desvio-padrão amostral | 0,032036 s |
| Vazão média | 911 consultas/s |
| Latência média por consulta | 4,3 ms |
| Latência p95 | 16,5 ms |

Os resultados mostram que o cache reduz o tempo de
processamento quando há repetição de consultas.

Na comparação entre políticas, a LRU apresentou
taxa de acerto de 71,2%, enquanto a FIFO alcançou
64,5%, ambas com capacidade 32 e quatro trabalhadores.

O aumento da capacidade de 32 para 128 entradas
elevou a taxa de acerto de 71,2% para 73,3%,
indicando ganhos decrescentes.

Para consultas distintas, a taxa de acerto foi
de 0%, demonstrando que o benefício do cache
depende da reutilização de informações.

Os resultados foram obtidos com geração simulada
e execução isolada do componente de cache.
O ambiente utilizado na C4 difere do ambiente
de C5 e C6, impedindo a comparação direta
dos tempos absolutos entre esses experimentos.

Fonte: experimentos/analise_c4.md
Dados: experimentos/resultados/c4_estatisticas.csv

### C5 — Pressão de memória

| Carga (MiB) | Repetições | Tempo médio (s) | RSS médio (MiB) | Swap (MiB) |
|---|---:|---:|---:|---:|
| 100 | 3 | 0,138452 | 116,20 | 0 |
| 250 | 3 | 0,280650 | 266,21 | 0 |
| 500 | 3 | 0,554763 | 516,18 | 0 |

O aumento da carga elevou o tempo de execução e o
consumo de memória física. Não foi observado uso de swap.

### C6 — Falha controlada

| Cenário | Repetições | Falhas tratadas | Tempo médio (s) |
|---|---:|---:|---:|
| Arquivo inexistente | 3 | 3 | 0,002523 |

As três tentativas produziram o erro FileNotFoundError,
que foi tratado e registrado pelo programa.


### Análise estatística dos tempos

Para avaliar a dispersão dos resultados, foram calculados
a média, o desvio-padrão amostral, o mínimo e o máximo
das três repetições de cada cenário.

| Configuração | Média (s) | Desvio-padrão (s) | Mínimo (s) | Máximo (s) |
|---|---:|---:|---:|---:|
| C5 — 100 MiB | 0,138452 | 0,073089 | 0,095836 | 0,222847 |
| C5 — 250 MiB | 0,280650 | 0,098335 | 0,214362 | 0,393632 |
| C5 — 500 MiB | 0,554763 | 0,257336 | 0,371561 | 0,848971 |
| C6 — Arquivo inexistente | 0,002523 | 0,000357 | 0,002272 | 0,002932 |

Na C5, o tempo médio aumentou conforme a carga de memória.
A carga de 500 MiB apresentou a maior dispersão absoluta.

Na C6, as três execuções registraram a falha como tratada.

Como foram realizadas apenas três repetições por cenário,
os resultados devem ser interpretados como observações
preliminares. Não permitem estabelecer conclusões
estatísticas robustas sobre o desempenho do servidor.

Os tempos medem operações sintéticas independentes,
não a latência de consultas do GenResearch-Servidor.


## 4. Comparação C1–C6

A consolidação parcial reúne os resultados disponíveis
de C4, C5 e C6. Os experimentos C1, C2 e C3
permanecem pendentes de publicação pela equipe.

| Configuração | Aspecto avaliado | Principal resultado |
|---|---|---|
| C1 | Leitura convencional | Aguardando resultados |
| C2 | Leitura com mmap | Aguardando resultados |
| C3 | Processamento com fila | Aguardando resultados |
| C4 | Cache compartilhado | 71,2% de acertos com LRU, capacidade 32 e 4 trabalhadores |
| C5 | Pressão de memória | RSS médio de 516,18 MiB na carga de 500 MiB, sem uso de swap |
| C6 | Falha controlada | 3 falhas FileNotFoundError tratadas em 3 execuções |

### 4.1 Relação com Sistemas Operacionais

Na C4, o cache compartilhado demonstrou a importância
da localidade de acesso, das políticas de substituição
e da concorrência entre trabalhadores.

Na C5, o aumento da carga elevou o consumo de memória
física e o tempo de execução. Foram observadas faltas
menores de página, sem faltas maiores ou uso de swap
nas cargas avaliadas.

Na C6, o tratamento da exceção FileNotFoundError
demonstrou como uma aplicação pode reconhecer e
registrar uma falha de acesso a arquivo sem encerrar
inesperadamente sua execução.

### 4.2 Limitações da comparação

Os experimentos disponíveis avaliam operações diferentes.

A C4 utiliza geração simulada e mede o componente de
cache isoladamente. A C5 utiliza alocação sintética
de memória, enquanto a C6 simula uma falha de arquivo.

Além disso, C4 foi executada em um ambiente diferente
daquele utilizado para C5 e C6.

Por esses motivos, os tempos absolutos não devem
ser comparados diretamente como se representassem
a latência de uma mesma operação do GenResearch-Servidor.

A comparação completa dependerá dos resultados de
C1, C2 e C3 e da integração dos componentes do servidor.

## 5. Gráficos disponíveis

- resultados/graficos/c5_tempo_medio.png
- resultados/graficos/c5_rss_medio.png
- resultados/graficos/c6_tempo_falha.png

## 6. Pendências

- Receber os resultados de C1, C2 e C3.
- Conferir unidades, parâmetros e número de repetições
  dos experimentos ainda pendentes.
- Produzir gráficos comparativos entre configurações
  que utilizem métricas e condições equivalentes.
- Executar e documentar testes integrados ao
  GenResearch-Servidor.
- Revisar as conclusões e limitações com a equipe.
