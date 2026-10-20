# Uso de inteligência artificial

Este documento registra as ferramentas de IA utilizadas, as tarefas apoiadas
e os procedimentos de verificação realizados pelos integrantes.

## Ferramentas utilizadas

| Ferramenta | Integrante | Tarefas |
| --- | --- | --- |
| Claude | Filipe | Configuração do ambiente WSL2; implementação do cache compartilhado; script do experimento C4; estruturação da análise dos resultados |
| ChatGPT/Codex | Vênisson | Apoio à implementação da fila e sincronização; integração dos componentes; elaboração de comandos e scripts experimentais; conferência e interpretação dos resultados; organização do repositório; apoio à redação do relatório, README, conclusões, slides e roteiro do vídeo |

## Verificação das sugestões

**Filipe — C4, cache compartilhado.** Li e revisei todo o código antes de usar.
Executei os experimentos na minha própria máquina, em duas rodadas independentes
(conferência e registro), e todos os números de `experimentos/analise_c4.md` vêm
dessas execuções — não aceitei nenhum valor sugerido pela ferramenta sem
reproduzir localmente.

Correções que fiz durante o processo:

- A carga de trabalho inicial usava 20 consultas distintas com sorteio uniforme,
  o que tornava as capacidades 32 e 128 indistinguíveis e empatava LRU com FIFO.
  Substituí por 60 consultas com distribuição enviesada, o que tornou a
  comparação entre políticas significativa.
- A primeira medição do custo do mutex estava inflada, porque media o overhead
  com a janela de corrida artificialmente alargada. Separei em duas medições:
  uma para demonstrar a falha, outra para medir o custo real.
- Ajustei o formato de saída às convenções já adotadas pela equipe em C5 e C6
  (colunas do CSV, nomenclatura dos arquivos, tabela de dispersão).
- Mantive na análise um resultado negativo: a condição de corrida não se
  manifestou no cache real sob a carga testada. Registrei o resultado com a
  interpretação correspondente em vez de descartá-lo.

Revisei o conteúdo final.

**Vênisson — C3, fila, concorrência e integração.** Utilizei ChatGPT/Codex
como apoio ao desenvolvimento. Executei os comandos e experimentos na minha
máquina virtual Ubuntu e conferi as saídas, incluindo consultas processadas,
perdas, duplicações, capacidade da fila, espera, latência e vazão.

Com apoio da ferramenta, implementei e ajustei os seguintes pontos durante
os testes:

- Parametrização da quantidade de produtores e consumidores, da capacidade
  do buffer e do número de consultas.
- Inclusão de métricas de latência, utilização dos consumidores e tamanho
  médio da fila ponderado pelo tempo.
- Correção da instrumentação do cenário de falha para atualizar o contador
  de ocupação do buffer.
- Integração da fila ao armazenamento de Fagner, ao cache de Filipe e à
  recuperação e geração simulada de Rauany, com verificação do atendimento
  das requisições em três execuções.
- No apoio aos testes de Rauany, correção da associação entre consultas
  e eventos concorrentes, organização das saídas em pastas independentes
  e serialização do caminho de saída no log JSON.
- Preservação dos valores atípicos e repetição da coleta para verificar
  sua ocorrência, sem atribuir uma causa não confirmada.
- Separação dos resultados dos experimentos C3 e das validações integradas,
  pois utilizam cargas e custos de processamento diferentes.

Os resultados apresentados foram obtidos nas execuções, sem preenchimento
de métricas ausentes por valores sugeridos pela IA. As interpretações foram
conferidas com as evidências disponíveis, distinguindo observações,
hipóteses e limitações.

Também utilizei ChatGPT/Codex para apoiar a redação e a organização dos
materiais. A ferramenta auxiliou na elaboração de textos do relatório,
instruções de reprodução, documentação, conclusões, slides, gráfico e roteiro
de apresentação. O código dos demais integrantes manteve sua atribuição original.

As verificações locais adicionais realizadas com apoio do Codex no Windows
foram distinguidas das coletas experimentais realizadas na VM Linux.
A revisão final do conteúdo e a responsabilidade pela entrega permanecem
com os integrantes da equipe.
