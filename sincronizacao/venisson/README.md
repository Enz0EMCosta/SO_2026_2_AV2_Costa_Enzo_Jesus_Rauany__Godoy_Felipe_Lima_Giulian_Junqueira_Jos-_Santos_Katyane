# C3 — Fila de requisições e sincronização

Responsável: Vênisson Cardoso dos Santos.

## Implementação

- Dois produtores, com seis consultas sintéticas cada.
- Dois consumidores por padrão; comparação com quatro consumidores.
- Buffer limitado a três itens.
- Semáforos empty/full e mutex.
- Processamento simulado de 0,2 segundo por consulta.
- Nenhuma dependência externa; Python 3.12.3 utilizado nos testes.

## Execução

A partir da raiz do repositório:

```bash
cd sincronizacao/venisson

python3 fila.py

python3 -c 'import fila; fila.CONSUMIDORES = 4; fila.main()'

python3 falha_controlada.py

python3 correcao_controlada.py
```

Execute cada comando em um processo Python independente.
Mantenha os quatro scripts na mesma pasta.

## Cenários

- Normal: consultas aguardam vagas e são atendidas pelos consumidores.
- Falha: produtores descartam consultas quando o buffer está cheio;
  consumidores iniciam após o término dos produtores.
- Correção: produtores aguardam vagas; consumidores iniciam após 0,5 segundo.

## Evidências

A pasta resultados/ contém as saídas dos experimentos.
Foram realizadas três repetições por cenário e por configuração de concorrência.

As repetições originais usaram sleep diretamente no consumidor.
Após a separação em processamento.py, cada cenário foi verificado novamente,
com as saídas identificadas por modulo_simulado.

Tabelas e análise dos resultados pertencem ao relatório técnico.

## Limitações

O processamento é simulado e ainda não está conectado aos demais módulos.
Os cenários de falha e correção usam critérios diferentes para iniciar
os consumidores; seus tempos não devem ser comparados como ganho de desempenho.
A ordem das impressões não representa necessariamente a ordem das operações.

## Integração com o cache compartilhado

A demonstração integracao_cache.py conecta a fila ao cache de Filipe
e ao processamento simulado. Os consumidores compartilham uma única
instância do cache. Cada requisição possui um ID único, enquanto
o texto da consulta pode se repetir.

Execute a partir da raiz do repositório:

    python3 sincronizacao/venisson/integracao_cache.py

A validação inicial concluiu 12 requisições sem falhas ou duplicações,
com 8 acertos, 4 misses e duas entradas no cache.
Os valores de acertos e misses podem variar conforme o escalonamento.

Essa integração ainda não inclui ingestão, armazenamento ou recuperação
de documentos. Os experimentos C3 originais permanecem separados.

## Integração com ingestão e armazenamento SQLite

Esta demonstração conecta a ingestão e o armazenamento do Fagner à fila,
ao cache do Filipe e a um adaptador provisório de recuperação lexical
com resposta simulada.

Execute a partir da raiz do repositório:

```bash
python3 -m servidor.ingestao.pipeline corpus-exemplo \
  --database experimentos/resultados/venisson_integrado/indice.sqlite3 \
  --summaries experimentos/resultados/venisson_integrado/ingestao

python3 sincronizacao/venisson/integracao_sqlite.py
```

O índice é carregado antes do início das threads e a conexão SQLite é
fechada. Os consumidores compartilham os trechos somente para leitura.

A recuperação seleciona trechos por palavras em comum. Os vetores
simulados do índice não são utilizados para similaridade semântica.
A geração simula custo proporcional ao tamanho do contexto.

As três validações concluíram doze requisições cada, sem falhas ou
duplicações. Os logs estão em experimentos/resultados/venisson_integrado/.

Essas validações são separadas dos experimentos C3 originais.
O tempo do lote não inclui ingestão nem carregamento inicial do índice.
O corpus mínimo verifica a conexão entre componentes, sem avaliar
a qualidade da recuperação.

O adaptador poderá ser substituído pela implementação da Rauany.

## C3 — Coleta com métricas ampliadas

O script fila.py aceita parâmetros de execução:

```bash
python3 sincronizacao/venisson/fila.py \
  --produtores 2 --consumidores 2 --capacidade 3 \
  --consultas-por-produtor 6
```

Foram realizadas três repetições com 1, 2 e 4 consumidores,
mantendo dois produtores, doze consultas e capacidade três.
Um consumidor constitui a referência sequencial de atendimento.

Métricas:
- Espera na fila: da inserção até a retirada.
- Latência: da tentativa de envio até o fim do processamento,
  incluindo a espera do produtor por vaga.
- Tamanho médio da fila: média ponderada pelo tempo, excluindo sentinelas.
- Utilização: tempo dentro do processamento dividido pela duração
  do experimento; representa ocupação do consumidor, não uso de CPU.
- p95: método do posto mais próximo. Com doze consultas, corresponde
  ao maior valor de latência observado na execução.

As saídas estão em:
experimentos/resultados/venisson_c3_20261020_025536/

A pasta inclui nove execuções normais, três de falha e três de correção,
além do ambiente e do patch do código durante a coleta de concorrência.
O pequeno ajuste de instrumentação da falha foi aplicado antes dessa coleta.

Todas as execuções normais e corrigidas concluíram doze consultas
sem perdas ou duplicações. A falha descartou nove por execução.

O processamento utiliza espera simulada de 0,2 segundo.
Os resultados não representam desempenho de inferência real.
