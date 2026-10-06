# Metodologia experimental

## Protocolo

1. Inventariar o ambiente em `ambiente/inventario.md` e registrar a revisão do
   código e os parâmetros da configuração.
2. Usar o mesmo corpus, consultas e carga em todas as execuções comparáveis.
3. Executar C1–C6 pelo menos três vezes cada. Identificar cada execução com ID,
   data/hora, configuração e número da repetição.
4. Registrar falhas e execuções inválidas explicitamente; não descartá-las sem
   indicar o motivo. Não substituir medições ausentes por estimativas.
5. Salvar dados brutos e comandos usados em `resultados/`; resumir média,
   dispersão e limitações sem ocultar variações.

## Métricas

Registrar, no mínimo:

- tempo total e latência das consultas (preferencialmente mediana e percentis);
- vazão (consultas por segundo) e número de trabalhadores ativos;
- RSS e VSZ do processo durante a execução;
- faltas de página, distinguindo minor e major quando a ferramenta permitir;
- armazenamento ocupado pelo corpus, índice/banco e logs;
- tamanho do cache, hits, misses e substituições;
- erros, bloqueios, filas pendentes e qualquer perda/inconsistência observada.

Identificar a ferramenta e a unidade de cada métrica. As métricas disponíveis
variam conforme o sistema operacional; anotar indisponibilidades em vez de
inferir valores.

## Reprodutibilidade

Arquivar os comandos, configurações, versões, dados de entrada ou sua descrição,
saídas brutas e critérios de cálculo. Evitar tarefas simultâneas que contaminem
as medições; quando isso não for possível, registrar a condição. Comparar
`mmap` e leitura convencional com o mesmo arquivo e condições equivalentes.

Os scripts de coleta e análise ainda serão implementados em `scripts/`. Até
então, não há resultados experimentais neste repositório.
