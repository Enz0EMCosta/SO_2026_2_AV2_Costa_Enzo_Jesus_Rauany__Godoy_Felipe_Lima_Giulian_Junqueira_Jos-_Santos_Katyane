
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
| C4 | Utilização de cache | Aguardando resultados da equipe |
| C5 | Pressão de memória | Teste sintético preliminar realizado |
| C6 | Falha controlada | Teste sintético preliminar realizado |

## 3. Resultados disponíveis

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

A comparação geral será preenchida após a disponibilização
das medições dos demais integrantes.

Os resultados de C5 e C6 apresentados neste documento
são provenientes de scripts sintéticos independentes.

Não é adequado compará-los diretamente com tempos de
requisição do pipeline GenResearch-Servidor, pois as
operações medidas são diferentes.

## 5. Gráficos disponíveis

- resultados/graficos/c5_tempo_medio.png
- resultados/graficos/c5_rss_medio.png
- resultados/graficos/c6_tempo_falha.png

## 6. Pendências

- Receber os resultados de C1, C2, C3 e C4.
- Conferir unidades, parâmetros e número de repetições.
- Consolidar métricas comparáveis entre configurações.
- Produzir gráficos comparativos quando houver dados.
- Executar e documentar testes integrados ao servidor.
- Revisar conclusões e limitações com a equipe.
