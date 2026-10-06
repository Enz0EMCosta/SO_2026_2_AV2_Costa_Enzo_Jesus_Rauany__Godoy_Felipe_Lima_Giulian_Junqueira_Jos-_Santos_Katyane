# Componentes do servidor

Cada subdiretório é um pacote Python destinado a uma responsabilidade do
GenResearch-Servidor:

| Pacote | Responsabilidade prevista |
| --- | --- |
| `ingestao` | Ler documentos, fragmentá-los e gerar embeddings |
| `armazenamento` | Persistir documentos, metadados e vetores |
| `fila` | Coordenar consultas entre produtores e trabalhadores |
| `recuperacao` | Selecionar trechos relevantes e montar contexto |
| `resposta` | Gerar ou simular a resposta |
| `cache` | Compartilhar respostas recentes e contabilizar hits/misses/substituições |
| `logs` | Registrar eventos de forma segura sob escrita concorrente |

As interfaces entre componentes, dependências e formato dos dados ainda serão
definidos durante a implementação. Manter configuráveis os tamanhos do corpus,
dos trechos, do contexto, da fila e do cache para permitir os experimentos.

O foco da avaliação é observar uso de CPU, memória, armazenamento, concorrência
e sincronização. Não tratar a qualidade semântica da resposta como métrica
principal.
