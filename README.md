# GenResearch-Servidor

Trabalho da equipe **Gemma** para a disciplina de **Sistemas Operacionais — AV2**.

O projeto implementa um serviço simplificado inspirado em recuperação aumentada
por geração (RAG). O objetivo é analisar memória, armazenamento, concorrência,
cache, sincronização e tratamento de falhas.

Os vetores e a geração de respostas são simulados. O foco da avaliação está
no comportamento do sistema operacional, não na qualidade das respostas.

## Funcionamento

```text
Documentos
    ↓
Leitura, fragmentação e vetores simulados
    ↓
Armazenamento SQLite
    ↓
Consultas → Fila limitada → Consumidores
                               ↓
                        Cache compartilhado
                               ↓
                     Recuperação de contexto
                               ↓
                       Resposta simulada
```

O índice é preparado antes do atendimento. Durante a execução, os consumidores
compartilham o cache e utilizam os dados carregados em memória.

## Contribuições da equipe

| Integrante | Componente |
|---|---|
| Enzo Emanuel Costa Maia | Inventário do ambiente e análise dos recursos disponíveis. |
| José Fagner Silva Junqueira | Ingestão, fragmentação, vetores simulados e armazenamento SQLite. |
| Vênisson Cardoso dos Santos | Fila, produtores e consumidores, sincronização, C3 e integração dos componentes. |
| Rauany Ingrid Santos de Jesus | Recuperação de contexto, geração simulada e benchmark correspondente. |
| Filipe de Carvalho Godoy | Cache compartilhado, políticas LRU/FIFO e experimento C4. |
| Giulian Fábio Bastos Amorim Lima | Comparação entre leitura convencional e mmap e análise de memória virtual. |
| Katyane dos Santos | Experimentos C5/C6, gráficos e consolidação dos resultados. |

Detalhes em [equipe/contribuicoes.md](equipe/contribuicoes.md).

## Estrutura

```text
ambiente/                 Inventário dos recursos
corpus-exemplo/           Documentos sintéticos de demonstração
servidor/                 Ingestão, armazenamento, cache, recuperação e resposta
sincronizacao/venisson/   Fila, falha/correção e executáveis de integração
experimentos/             Scripts, metodologia, análises e resultados
memoria-armazenamento/    Análise de memória, leitura e armazenamento
conclusao/                Discussão, limitações e relação com SO
equipe/                   Contribuições e declaração de uso de IA
tests/                    Testes funcionais
entrega/                  Relatório, apresentação e referência ao vídeo
```

A implementação executável da fila está em `sincronizacao/venisson/`.

## Requisitos

- Python 3.12 ou superior para o fluxo integrado.
- Linux nativo, VM Linux ou WSL2 para reproduzir as observações do ambiente Linux.
- Biblioteca padrão do Python para o fluxo principal.
- Matplotlib para os scripts de geração de gráficos.

Para gerar gráficos:

```bash
python3 -m pip install matplotlib
```

Não é necessário instalar Ollama, baixar modelos ou utilizar GPU para executar
a demonstração integrada com geração simulada.

Os ambientes e versões utilizados nas coletas estão identificados nas evidências.
Os comandos abaixo devem ser executados na raiz do repositório.

## Execução do fluxo integrado

### 1. Preparar o índice

```bash
python3 -m servidor.ingestao.pipeline corpus-exemplo \
  --database experimentos/resultados/venisson_integrado/indice.sqlite3 \
  --summaries experimentos/resultados/venisson_integrado/ingestao
```

O comando lê os documentos TXT, fragmenta o conteúdo, produz vetores simulados
e persiste os dados no SQLite.

### 2. Executar consultas

```bash
python3 sincronizacao/venisson/integracao_rauany.py
```

A demonstração conecta:

- Ingestão e armazenamento de Fagner.
- Fila concorrente de Vênisson.
- Cache compartilhado de Filipe.
- Recuperação e geração simulada de Rauany.

São enviadas doze requisições com perguntas repetidas. A saída apresenta
consultas concluídas, falhas, duplicações, acertos e misses do cache,
além de métricas das gerações.

O corpus de exemplo é mínimo e serve para verificar a integração.

## Testes funcionais

```bash
python3 -m unittest discover -s tests -p test_ingest.py -v
```

Os testes verificam fragmentação, vetores reproduzíveis, persistência,
reingestão, leitura convencional/mmap e tratamento de entradas inválidas.

## Fila e sincronização — C3

Exemplo com dois produtores, dois consumidores e buffer de três posições:

```bash
python3 sincronizacao/venisson/fila.py \
  --produtores 2 \
  --consumidores 2 \
  --capacidade 3 \
  --consultas-por-produtor 6
```

Falha controlada e correção:

```bash
python3 sincronizacao/venisson/falha_controlada.py
python3 sincronizacao/venisson/correcao_controlada.py
```

O cenário de falha descarta consultas quando o buffer está cheio.
Na correção, os produtores aguardam vagas por meio de semáforos.

Instruções adicionais em
[sincronizacao/venisson/README.md](sincronizacao/venisson/README.md).

## Experimentos

| Configuração | Objetivo | Referência |
|---|---|---|
| C1 | Leitura convencional | `memoria-armazenamento/` |
| C2 | Leitura com mmap | `memoria-armazenamento/` |
| C3 | Concorrência e fila | `sincronizacao/venisson/` |
| C4 | Cache compartilhado | `experimentos/scripts/c4_cache.py` |
| C5 | Aumento controlado de memória | `experimentos/scripts/c5_pressao_memoria.py` |
| C6 | Falha controlada de arquivo | `experimentos/scripts/c6_falha_controlada.py` |

A ingestão e a recuperação/geração também possuem benchmarks específicos
em `experimentos/scripts/`.

Cada configuração coletada deve ser identificada por seus parâmetros,
ambiente e repetições. As comparações devem respeitar as diferenças entre
operações e ambientes.

Antes de executar um benchmark, consulte suas instruções e verifique
se os arquivos de saída existentes serão preservados.

## Resultados e evidências

- `experimentos/genresearch/evidencias/`: ingestão e armazenamento.
- `experimentos/resultados/venisson_c3_20261020_025536/`: coleta C3 com métricas ampliadas.
- `experimentos/resultados/venisson_integrado/`: validações dos componentes integrados.
- `experimentos/resultados/c4_*.csv`: resultados do cache.
- `experimentos/resultados/c5_*.csv`: resultados de memória.
- `experimentos/resultados/c6_*.csv`: resultados de falha de arquivo.
- `experimentos/resultados/graficos/`: gráficos disponíveis.
- `memoria-armazenamento/`: análise e evidências de leitura e memória.

As tabelas, interpretações e limitações são apresentadas nas análises
dos experimentos e no relatório técnico. Coletas antigas são preservadas
como histórico, sem substituir os resultados principais.

## Discussão e limitações

- [Discussão dos resultados](conclusao/discussao.md)
- [Limitações](conclusao/limitacoes.md)
- [Relação com Sistemas Operacionais](conclusao/relacao-com-so.md)
- [Análise de memória e armazenamento](memoria-armazenamento/analise.md)

Os vetores SHA-256 não representam relações semânticas, e a geração simulada
não reproduz inferência real. Os resultados de componentes isolados não devem
ser confundidos com medições completas do fluxo integrado.

## Materiais de entrega

Os arquivos de relatório e apresentação estão organizados em `entrega/`.
Consulte essa pasta para identificar as versões disponíveis.

**Vídeo da equipe:**  
[SO_AV2.mp4](https://drive.google.com/file/d/1Eng0vAxw9eUuYno_TONka1DbBizSVzHV/view?usp=drivesdk)

**Pasta de gravações:**  
[Vídeos no Google Drive](https://drive.google.com/drive/folders/1OEmFcCSymYisb0Jm46aW3XSVcIHq-QGH)

A referência ao vídeo também está em [entrega/VIDEO.md](entrega/VIDEO.md).
Antes da submissão, confirmar o acesso para os avaliadores, a montagem final
e a duração de até vinte minutos.

## Uso de IA

O registro do apoio de ferramentas de IA está em
[equipe/uso-de-ia.md](equipe/uso-de-ia.md).
