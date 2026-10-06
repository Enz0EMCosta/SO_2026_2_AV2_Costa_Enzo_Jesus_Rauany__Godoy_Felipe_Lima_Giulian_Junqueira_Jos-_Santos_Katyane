# Análise de memória e armazenamento

Preencher com medições reais das configurações C1–C6 e referenciar os arquivos
brutos em `experimentos/resultados/`.

## Memória

Analisar RSS e VSZ ao longo do tempo, faltas de página e efeito do tamanho do
corpus, do contexto e do número de trabalhadores. Explicar o que cada métrica
representa no ambiente medido e indicar a ferramenta usada.

## Armazenamento

Registrar o tamanho inicial e final dos documentos, metadados, vetores/índices,
cache persistente (se houver) e logs. Diferenciar espaço lógico de espaço
efetivamente ocupado quando a ferramenta permitir.

## Comparações e limitações

Comparar leitura convencional com `mmap` e discutir page cache, acesso ao disco,
pressão de memória e efeitos de aquecimento. Relacionar as observações aos
parâmetros e ao ambiente, sem extrapolar além dos dados coletados.
