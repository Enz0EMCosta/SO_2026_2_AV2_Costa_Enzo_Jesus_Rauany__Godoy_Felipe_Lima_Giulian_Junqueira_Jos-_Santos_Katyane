# Análise do Experimento C4 — Cache compartilhado

## 1. Objetivo

Avaliar o efeito do cache compartilhado de respostas sobre latência, vazão e
uso de recursos do GenResearch-Servidor, comparando consultas repetidas e
semanticamente distintas, conforme a configuração C4 de
`experimentos/configuracoes.md`.

Mede-se taxa de acerto, taxa de erro, substituições e tempo economizado, além
do comportamento sob diferentes capacidades, políticas de remoção e números de
trabalhadores concorrentes.

## 2. Ambiente de execução

| Item | Valor |
|---|---|
| Sistema | Ubuntu 24.04.5 LTS sobre WSL2 |
| Kernel | 6.6.87.2-microsoft-standard-WSL2 |
| CPU | Intel Core i5-10500H — 6 núcleos, 12 threads lógicas |
| RAM | 7,6 GiB · swap 2,0 GiB |
| Python | 3.12.3, apenas biblioteca padrão |
| Commit | `3b4340d` |
| Data da coleta | 2026-10-18, 23h38 (UTC−03) |
| Diretório | `/home/filipe/gemma` (sistema de arquivos nativo do Linux) |

As medições foram feitas no sistema de arquivos nativo, nunca em `/mnt/c`,
cujo acesso atravessa uma camada de tradução e distorceria os tempos.

> **Nota sobre comparabilidade.** Este ambiente difere do usado em C5 e C6
> (kernel 6.18, Python 3.14). Tempos absolutos entre configurações medidas em
> ambientes distintos não são diretamente comparáveis. As comparações internas
> ao C4 são válidas, pois todas as suas 36 execuções ocorreram no mesmo
> ambiente, na mesma sessão.

## 3. Experimento C4 — Cache compartilhado

### 3.1 Metodologia

O componente avaliado é `servidor/cache`, que guarda respostas recentes
indexadas pela consulta, com capacidade fixa e remoção por LRU ou FIFO. Por ser
compartilhado entre trabalhadores concorrentes, todo acesso ao estado interno é
serializado por um `threading.Lock`.

**Parâmetros fixados** (conforme exigido em `configuracoes.md`):

| Parâmetro | Valor |
|---|---|
| Consultas por execução | 200 |
| Repetições por configuração | 3 |
| Semente do gerador aleatório | 42 (+ número da repetição) |
| Universo de consultas distintas (carga repetida) | 60 |
| Distribuição de acesso (carga repetida) | enviesada, peso 1/posição |
| Custo simulado de geração | 8 ms + 0,12 ms por caractere + jitter até 4 ms |

**Fatores variados**, um por vez a partir da configuração base (capacidade 32,
LRU, 4 trabalhadores), sempre nas duas cargas:

| Fator | Valores |
|---|---|
| Carga | repetidas · distintas |
| Capacidade do cache | 8 · 32 · 128 |
| Política de remoção | LRU · FIFO |
| Trabalhadores concorrentes | 1 · 2 · 4 |

Total: **12 configurações × 3 repetições = 36 execuções**.

**Cargas de trabalho.** Em *repetidas*, 60 consultas distintas são sorteadas com
distribuição enviesada — poucas muito populares, cauda longa de raras —,
reproduzindo o padrão de localidade de um serviço real de perguntas. Em
*distintas*, toda consulta é única, representando exploração aberta.

**Geração simulada.** O custo de recuperação e geração é simulado por atraso
proporcional ao tamanho da consulta, alternativa autorizada pelo enunciado
(Parte B, "Resposta"). Para integrar com `servidor/recuperacao` e
`servidor/resposta`, basta passar a função real como segundo argumento de
`obter_ou_gerar`; nenhuma outra alteração é necessária.

**Por que lotes de 200 consultas.** O cálculo de mediana e p95 exigido no item
10 do enunciado não é possível sobre três pontos. Cada execução processa um
lote, e as três repetições medem a dispersão entre execuções.

### 3.2 Comandos utilizados

```bash
# execução de conferência
python3 experimentos/scripts/c4_cache.py --validacao --consultas 200 --repeticoes 3

# execução registrada
python3 experimentos/scripts/c4_cache.py --consultas 200 --repeticoes 3
```

### 3.3 Resultados

Médias das três repetições da execução registrada.

| Carga | Cap. | Pol. | Trab. | Acerto | Subst. | Total (s) | Econ. (s) | Vazão (c/s) | Média (ms) | Mediana (ms) | p95 (ms) |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| repetidas | 8 | LRU | 4 | 36,5% | 104 | 0,48 | 1,00 | 421 | 9,3 | 13,1 | 17,3 |
| repetidas | 32 | LRU | 4 | 71,2% | 19 | 0,22 | 1,99 | 911 | 4,3 | 0,0 | 16,5 |
| repetidas | 128 | LRU | 4 | 73,3% | 0 | 0,21 | 2,15 | 963 | 4,0 | 0,0 | 16,4 |
| repetidas | 32 | FIFO | 4 | 64,5% | 28 | 0,27 | 1,88 | 744 | 5,2 | 0,0 | 16,6 |
| repetidas | 32 | LRU | 1 | 72,8% | 22 | 0,81 | 2,06 | 251 | 4,0 | 0,0 | 16,7 |
| repetidas | 32 | LRU | 2 | 72,5% | 21 | 0,42 | 2,05 | 481 | 4,1 | 0,0 | 16,8 |
| distintas | 8 | LRU | 4 | 0,0% | 192 | 0,80 | 0,00 | 251 | 15,6 | 15,6 | 18,4 |
| distintas | 32 | LRU | 4 | 0,0% | 168 | 0,79 | 0,00 | 255 | 15,5 | 15,4 | 18,1 |
| distintas | 128 | LRU | 4 | 0,0% | 72 | 0,79 | 0,00 | 253 | 15,5 | 15,6 | 18,4 |
| distintas | 32 | FIFO | 4 | 0,0% | 168 | 0,78 | 0,00 | 257 | 15,3 | 15,4 | 18,3 |
| distintas | 32 | LRU | 1 | 0,0% | 168 | 3,12 | 0,00 | 64 | 15,5 | 15,5 | 18,5 |
| distintas | 32 | LRU | 2 | 0,0% | 168 | 1,55 | 0,00 | 129 | 15,4 | 15,4 | 18,4 |

**Latência por tipo de evento**, agregada sobre as 36 execuções:

| Evento | Latência média |
|---|---:|
| Acerto (servido pelo cache) | 0,0029 ms |
| Erro (exigiu geração) | 15,12 ms |
| **Razão** | **5.135×** |

#### Dispersão dos tempos

Mesmo tratamento estatístico aplicado em C5 e C6.

| Configuração | Média (s) | Desvio-padrão (s) | Mínimo (s) | Máximo (s) |
|---|---:|---:|---:|---:|
| C4 — repetidas, cap 32, LRU, 1 trab. | 0,806133 | 0,105749 | 0,687000 | 0,888900 |
| C4 — repetidas, cap 32, LRU, 2 trab. | 0,419800 | 0,047857 | 0,366700 | 0,459600 |
| C4 — repetidas, cap 32, LRU, 4 trab. | 0,222833 | 0,032036 | 0,185900 | 0,243100 |
| C4 — repetidas, cap 8, LRU, 4 trab. | 0,475267 | 0,013996 | 0,464200 | 0,491000 |
| C4 — repetidas, cap 128, LRU, 4 trab. | 0,207933 | 0,008344 | 0,198300 | 0,212900 |
| C4 — repetidas, cap 32, FIFO, 4 trab. | 0,270700 | 0,026258 | 0,240400 | 0,286800 |
| C4 — distintas, cap 32, LRU, 1 trab. | 3,115900 | 0,027042 | 3,085900 | 3,138400 |
| C4 — distintas, cap 32, LRU, 2 trab. | 1,554233 | 0,012796 | 1,546400 | 1,569000 |
| C4 — distintas, cap 32, LRU, 4 trab. | 0,785800 | 0,009560 | 0,779500 | 0,796800 |
| C4 — distintas, cap 8, LRU, 4 trab. | 0,797800 | 0,007238 | 0,789500 | 0,802800 |
| C4 — distintas, cap 128, LRU, 4 trab. | 0,790567 | 0,007003 | 0,782800 | 0,796400 |
| C4 — distintas, cap 32, FIFO, 4 trab. | 0,777367 | 0,003530 | 0,773600 | 0,780600 |

A dispersão é sistematicamente maior na carga repetida — desvio-padrão de
0,105 s contra 0,027 s na configuração equivalente da carga distinta. A
explicação está no mecanismo: na carga repetida o tempo total depende de
*quando* cada acerto ocorre, e a ordem de chegada das consultas varia entre
repetições. Na carga distinta toda consulta custa o mesmo (sempre erro), e o
tempo total é quase determinístico — desvio-padrão de 0,0035 s no melhor caso.

Uma execução de conferência prévia (`c4_validacao.csv`) produziu valores dentro
da mesma faixa, confirmando a estabilidade das medições.

### 3.4 Análise

**O acerto é cinco mil vezes mais barato que o erro.** Latência média de um
acerto: 0,0029 ms. De um erro: 15,12 ms. Razão de **5.135×**. O cache não
acelera a geração — ele a elimina. Todo o resto decorre disso.

**A capacidade tem retorno decrescente, com ponto de inflexão visível.** Passar
de 8 para 32 entradas quase dobrou a taxa de acerto, de 36,5% para 71,2%, e
reduziu o tempo total de 0,48 s para 0,22 s. Quadruplicar de 32 para 128 rendeu
apenas 2,1 pontos percentuais.

O que muda de fato entre 32 e 128 é a substituição: 19 contra zero. Com
capacidade 128 o universo inteiro de 60 consultas cabe no cache, e nada precisa
ser descartado. O ganho de capacidade se esgota quando ela alcança o conjunto
de trabalho; depois disso, só se consome memória.

**LRU supera FIFO porque a carga tem localidade.** Na mesma capacidade e com os
mesmos trabalhadores, LRU alcançou 71,2% contra 64,5% do FIFO — 6,7 pontos
percentuais —, com menos substituições (19 contra 28) e vazão maior (911 contra
744 consultas por segundo).

O FIFO descarta por ordem de chegada, sem considerar uso: uma consulta popular
inserida cedo é removida mesmo sendo pedida constantemente. O LRU descarta o
que não é usado há mais tempo, preservando o conjunto quente. Sob acesso
uniforme as duas políticas empatariam — a diferença só existe porque a carga
tem localidade, como têm as cargas reais.

**A concorrência escalou quase linearmente.** Com capacidade 32 e LRU, o tempo
caiu de 0,81 s (1 trabalhador) para 0,42 s (2) e 0,22 s (4), com a vazão subindo
de 251 para 481 e 911 consultas por segundo — **3,6× com 4 trabalhadores**.

Na carga distinta a escala foi ainda melhor: 3,12 s para 0,79 s, ou **3,9×**,
praticamente o ideal teórico. A diferença tem explicação: na carga repetida boa
parte do trabalho são acertos quase instantâneos, de modo que sobra menos
trabalho paralelizável e o custo fixo pesa proporcionalmente mais.

Duas razões para a ausência de contenção no mutex:

1. A seção crítica é curta — consulta a dicionário e atualização de contadores.
   O trabalho caro acontece fora do lock.
2. A carga é limitada por espera, não por CPU. Nesse regime as threads liberam
   o GIL durante a espera e são a escolha adequada. Com geração limitada por
   CPU, o GIL seria o gargalo e processos seriam necessários.

A taxa de acerto caiu ligeiramente com mais trabalhadores: 72,8% com um, 72,5%
com dois, 71,2% com quatro. É o efeito do trabalho duplicado — como a geração
ocorre fora do lock, várias threads podem produzir a mesma chave
simultaneamente. Custo da decisão de projeto, e pequeno: 1,6 ponto percentual
para um ganho de 3,6× em vazão.

**Na carga distinta o cache é custo puro.** Taxa de acerto zero em todas as
configurações, tempo economizado zero, e nenhuma variação de tempo total entre
capacidades — 0,80 s, 0,79 s e 0,79 s para capacidades 8, 32 e 128. O que muda
é apenas o número de substituições: 192, 168 e 72, ou seja, trabalho de
manutenção sem contrapartida.

A conclusão não é que o cache seja inútil, e sim que **ele só paga quando há
repetição**. Um serviço de perguntas frequentes se beneficia; uma ferramenta de
exploração aberta, não. Dimensionar cache sem conhecer o padrão de acesso é
adivinhação.

**Mediana e p95 contam histórias opostas.** Na carga repetida com capacidade 32,
a mediana é **0,0 ms** e o p95 é **16,5 ms**. A consulta típica é instantânea; a
do percentil 95 custa o mesmo que custaria sem cache algum — compare com os
18,1 ms de p95 da carga distinta, onde não há acerto nenhum.

O motivo é que a cauda da distribuição *é* o conjunto de erros. O cache move
massa para perto de zero, mas não melhora o pior caso — apenas o torna mais
raro. Para dimensionamento por SLA de p95 a distinção é decisiva, porque a
média engana ao ser puxada pelos acertos: 4,3 ms de média contra 0,0 ms de
mediana e 16,5 ms de p95 descrevem a mesma amostra.

A configuração de capacidade 8 é o caso intermediário instrutivo: mediana de
13,1 ms, entre os dois extremos. Com apenas 36,5% de acerto, nem metade das
consultas é servida pelo cache, e a mediana cai no território dos erros.

**Relação com conceitos de Sistemas Operacionais.** O comportamento observado
reproduz, em nível de aplicação, o que o kernel faz com o cache de páginas: um
conjunto de trabalho pequeno em relação à capacidade produz alta taxa de
acerto; acesso sem localidade transforma o cache em sobrecarga; e a política de
remoção importa exatamente na faixa em que a capacidade é menor que o conjunto
de trabalho. A diferença de 5.135× entre acerto e erro é o análogo da diferença
entre servir uma página já residente em memória e buscá-la no disco.

## 4. Limitações e próximos passos

- **A geração é simulada.** Os tempos absolutos não representam o custo real de
  recuperação e geração. As comparações relativas entre configurações permanecem
  válidas, já que todas usam o mesmo gerador. A integração com
  `servidor/recuperacao` e `servidor/resposta` exige apenas trocar a função
  passada a `obter_ou_gerar`.
- **A chave é a consulta exata.** Consultas semanticamente equivalentes com
  redação diferente contam como entradas distintas. O módulo oferece
  normalização opcional, não usada nestas medições. Acerto por similaridade
  semântica exigiria comparação de embeddings, fora do recorte adotado.
- **Ambiente distinto do usado em C5 e C6**, conforme a nota da seção 2.
- **Threads, não processos.** Adequado para carga limitada por espera. Com
  geração limitada por CPU, o GIL seria o gargalo.
- **Três repetições por configuração** atendem ao mínimo do enunciado, mas são
  poucas para conclusões estatísticas robustas — mesma ressalva registrada em
  C5 e C6. O desvio-padrão de 0,105 s na configuração de um trabalhador, sobre
  média de 0,806 s, indica variabilidade de cerca de 13%.
- **Não foram medidos RSS, VSZ nem faltas de página.** O cache mantém no máximo
  128 respostas curtas em memória, volume irrelevante frente aos 7,6 GiB
  disponíveis. A análise de pressão de memória é objeto de C5.
- **O experimento ainda não é integrado ao pipeline completo.** Mede o
  componente de cache isoladamente, com gerador simulado. A execução integrada
  com fila, recuperação e resposta reais está pendente.

## 5. Contribuição para a consolidação C1–C6

Linha para `experimentos/consolidacao_c1_c6.md`:

| Configuração | Descrição | Situação |
|---|---|---|
| C4 | Utilização de cache | Resultados coletados — 12 configurações × 3 repetições |

Resumo para a comparação geral: na carga com repetição e capacidade adequada, o
cache elevou a taxa de acerto a 71,2% e reduziu o tempo total de 0,79 s para
0,22 s — **3,6× mais rápido** que a mesma carga sem acertos possíveis, com
vazão subindo de 255 para 911 consultas por segundo. Na carga sem repetição,
não houve ganho algum.

Para a análise estatística dos tempos, as doze linhas da seção 3.3 estão em
`experimentos/resultados/c4_estatisticas.csv`, no mesmo formato usado em C5
e C6.

## 6. Arquivos de evidência

| Arquivo | Conteúdo |
|---|---|
| `servidor/cache/cache.py` | Implementação do cache compartilhado |
| `servidor/cache/README.md` | Interface e decisões de projeto |
| `experimentos/scripts/c4_cache.py` | Script do experimento |
| `experimentos/resultados/c4_cache_compartilhado.csv` | 36 execuções, uma por linha |
| `experimentos/resultados/c4_estatisticas.csv` | Média, desvio-padrão, mínimo e máximo |
| `experimentos/resultados/c4_validacao.csv` | Execução de conferência |
| `experimentos/resultados/c4_validacao_estatisticas.csv` | Estatísticas da conferência |
| `experimentos/resultados/c4_eventos.jsonl` | Log de eventos com escrita concorrente protegida |