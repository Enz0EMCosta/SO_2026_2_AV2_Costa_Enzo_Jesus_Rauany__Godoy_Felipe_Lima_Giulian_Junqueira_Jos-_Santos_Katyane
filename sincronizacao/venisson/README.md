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
