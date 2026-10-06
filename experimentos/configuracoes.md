# Configurações experimentais C1–C6

As configurações abaixo são uma matriz inicial. Fixar e registrar os parâmetros
numéricos antes da coleta; manter iguais os parâmetros não alterados em cada
comparação. Cada configuração deve ser executada pelo menos três vezes.

| ID | Configuração | Comparação principal |
| --- | --- | --- |
| C1 | Leitura convencional; execução de referência com fila, cache e corpus de referência | Linha de base |
| C2 | Mesmo cenário de C1, usando `mmap` na leitura dos documentos | Leitura convencional vs. mapeada |
| C3 | Fila com múltiplos produtores e consumidores; carga concorrente definida | Concorrência, vazão e contenção |
| C4 | Cache compartilhado habilitado; sequência de consultas com repetição conhecida | Acertos, erros, substituições e latência |
| C5 | Corpus e/ou contexto ampliados em relação à referência | Pressão de memória e armazenamento |
| C6 | Falha de sincronização controlada e, como controle, execução corrigida com mutex | Efeito da falha e da correção |

## Parâmetros a fixar

- tamanho e quantidade de documentos, política de fragmentação e formato dos
  embeddings;
- tamanho de fila, quantidade de produtores/consumidores e total de consultas;
- capacidade e política de substituição do cache, além da ordem de consultas;
- tamanho do contexto e parâmetros usados para simular ou executar geração;
- dados de entrada, versão do código, ambiente e condições de execução;
- ordem das execuções e política para aquecimento, se aplicável.

Não comparar configurações que alterem simultaneamente fatores não relacionados
sem explicitar essa limitação. A falha C6 deve usar apenas dados e recursos
controlados, e o resultado corrigido deve ser medido sob carga equivalente.
