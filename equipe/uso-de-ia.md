# Uso de inteligência artificial

Declarar as ferramentas de IA utilizadas, para quais tarefas foram usadas e
como as sugestões foram verificadas pela equipe. Registrar também alterações
feitas pelos integrantes e confirmar que o conteúdo final foi revisado.

Preencher de acordo com o uso real durante o trabalho; não declarar ferramentas
ou contribuições que não ocorreram.

## Ferramentas utilizadas

| Ferramenta | Integrante | Tarefas |
| --- | --- | --- |
| Claude | Filipe | Configuração do ambiente WSL2; implementação do cache compartilhado; script do experimento C4; estruturação da análise dos resultados |

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
