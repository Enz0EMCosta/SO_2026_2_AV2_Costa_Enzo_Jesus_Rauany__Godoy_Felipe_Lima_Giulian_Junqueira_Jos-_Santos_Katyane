# Contribuições da equipe

Preencher com as contribuições efetivamente realizadas por cada integrante.
Descrever tarefas concretas (implementação, testes, experimentos, análise,
documentação ou apresentação) e evitar atribuir trabalho não realizado.

| Integrante | Contribuições |
| --- | --- |
| Filipe de Carvalho Godoy | Implementação do cache compartilhado (`servidor/cache`) com políticas LRU e FIFO e proteção por mutex; script do experimento C4; execução e coleta das 36 execuções; análise dos resultados em `experimentos/analise_c4.md`; documentação da interface do componente para integração com os blocos de fila, recuperação e resposta. |
| Vênisson Cardoso dos Santos | Implementação da fila limitada com produtores e consumidores, semáforos `empty` e `full` e mutex; execução do C3 com 1, 2 e 4 consumidores, com três repetições por configuração; coleta de métricas de espera, latência, vazão, ocupação da fila e utilização dos consumidores; demonstração de falha controlada e correção; integração com ingestão, armazenamento, cache, recuperação e geração simulada; apoio à execução e validação dos experimentos de Rauany; organização do repositório e das evidências; elaboração de sua seção do relatório, dos textos de conclusão e dos slides; participação no vídeo. |
