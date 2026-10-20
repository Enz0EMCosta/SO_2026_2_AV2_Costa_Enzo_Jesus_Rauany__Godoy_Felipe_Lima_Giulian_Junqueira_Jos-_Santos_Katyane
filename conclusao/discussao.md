# Discussão dos resultados

## Visão geral

O desenvolvimento do GenResearch-Servidor permitiu observar a influência de
memória, armazenamento, concorrência, cache e sincronização em uma aplicação
inspirada em recuperação aumentada por geração (RAG).

As contribuições dos integrantes foram avaliadas em experimentos específicos
e em validações integradas. Os resultados devem ser interpretados dentro das
condições de cada coleta, pois foram utilizados ambientes, cargas e operações
diferentes.

## Ambiente, ingestão e armazenamento

O inventário elaborado por Enzo documenta os recursos do ambiente e fornece
uma referência para interpretar o consumo de memória, armazenamento e CPU.
A distinção entre MemFree, MemAvailable, cache de páginas e swap evita
interpretar toda memória ocupada como indisponível.

A implementação de Fagner realiza leitura de documentos, fragmentação,
geração de vetores simulados e persistência em SQLite. Os testes funcionais
verificaram fragmentação, normalização dos vetores, persistência, reabertura,
reingestão sem duplicação e tratamento de entradas inválidas.

Na coleta de ingestão, o corpus passou de 34.940 para 1.048.690 bytes.
Nesse intervalo, o tempo médio total com leitura convencional passou de
aproximadamente 0,0322 s para 0,0977 s. Esse tempo inclui fragmentação,
vetorização e escrita no banco, não representando apenas o custo da leitura.

O tamanho do SQLite inclui textos, metadados, vetores e estruturas internas.
Consequentemente, não deve ser confundido com o volume dos vetores ou com
a quantidade de bytes fisicamente transferidos pelo dispositivo.

## Leitura convencional e mmap

A análise de Giulian relata menor tempo médio de mmap para arquivos de
64 KiB e pequena vantagem da leitura convencional para arquivos de 8 MiB.
Também relata RSS e VSZ maiores com mmap nos arquivos maiores e equivalência
de bytes e SHA-256 em 36 pares de registros.

Essas observações estão documentadas na análise e nas capturas disponibilizadas.
Na versão examinada, o script e os CSVs brutos correspondentes não estavam
disponíveis, limitando a verificação independente das estatísticas.

O experimento de ingestão de Fagner constitui uma comparação diferente.
No maior corpus, o tempo médio total foi de aproximadamente 0,0977 s com
leitura convencional e 0,1001 s com mmap. Além disso, sua implementação
materializa os bytes do mapeamento antes da decodificação.

Os resultados não sustentam superioridade universal de um método.
O desempenho depende do tamanho dos arquivos, do processamento adicional,
do padrão de acesso e das condições do cache de páginas.

## Concorrência e fila de requisições

O experimento C3 de Vênisson utilizou dois produtores, doze consultas,
buffer com capacidade para três itens e processamento simulado de
0,2 segundo por consulta. Cada configuração foi repetida três vezes.

| Consumidores | Tempo total médio (s) | Vazão média (consultas/s) | Espera média na fila (s) |
|---|---:|---:|---:|
| 1 | 2,4193 | 4,96 | 0,5031 |
| 2 | 1,2154 | 9,87 | 0,2341 |
| 4 | 0,6196 | 19,37 | 0,1008 |

Todas as nove execuções concluíram as doze consultas sem perdas ou duplicações.
O buffer respeitou o limite de três itens.

O aumento de consumidores reduziu a espera e elevou a vazão na carga simulada.
Como o processamento utiliza sleep, os trabalhadores podem sobrepor períodos
de espera. Portanto, o ganho não representa uma previsão de aceleração para
inferência real limitada por CPU.

A ocupação registrada dos consumidores inclui o tempo de espera simulada
e não corresponde ao percentual de utilização do processador.

## Sincronização e falha controlada

A fila utiliza os semáforos empty e full para coordenar vagas e itens
disponíveis, além de um mutex para proteger inserções e retiradas.

Na falha controlada, os produtores não aguardavam vagas. Com os consumidores
inicialmente parados, três consultas foram aceitas e nove descartadas em cada
uma das três repetições.

Na correção, os produtores aguardavam espaço e os consumidores iniciavam após
um atraso de 0,5 segundo. Todas as doze consultas foram processadas nas três
repetições, sem perdas ou duplicações.

A comparação demonstra a preservação das consultas mediante espera por vagas.
Como o início dos consumidores difere entre os cenários, os tempos não devem
ser usados para concluir ganho de desempenho entre falha e correção.

## Cache compartilhado

O C4 de Filipe demonstrou que o aproveitamento do cache depende da repetição
de consultas, da capacidade e da política de substituição.

Na carga repetida, com capacidade de 32 entradas e quatro trabalhadores,
LRU atingiu aproximadamente 71,2% de acertos, enquanto FIFO alcançou 64,5%.
O aumento da capacidade para 128 entradas elevou o acerto para 73,3%,
indicando ganho decrescente nesse conjunto de consultas.

Na carga distinta, a taxa de acerto foi zero. Nesse cenário, o cache manteve
o custo de consulta e manutenção sem evitar gerações.

A geração ocorre fora do mutex do cache, reduzindo a duração da região crítica.
Como consequência, solicitações simultâneas da mesma chave podem produzir
trabalho repetido antes de a resposta estar disponível. Isso não significa
duplicação do identificador de uma requisição concluída.

O tempo economizado registrado pelo componente soma custos de gerações
evitadas. Ele não equivale, necessariamente, à redução do tempo de parede
medida em uma comparação controlada com cache desabilitado.

## Recuperação, geração e integração

A implementação de Rauany seleciona trechos por similaridade de cosseno,
monta um contexto limitado e simula a geração com custo proporcional ao
tamanho desse contexto.

A coleta completa disponível contém 45 execuções e 2.700 registros.
A proximidade dos resultados com top_k igual a quatro e oito é compatível
com o limite de contexto, que restringe o volume enviado à geração.

Os vetores utilizados são determinísticos por SHA-256. Embora consulta e
documentos utilizem o mesmo algoritmo, esses vetores não representam
relações semânticas entre textos.

Foi observado e preservado um tempo atípico de 47,0283 segundos.
Um reteste também apresentou atrasos elevados na geração simulada.
A causa não foi determinada, pois não houve monitoramento sincronizado
suficiente para atribuir os atrasos à virtualização, memória ou escalonamento.
Os arquivos do reteste devem acompanhar a entrega caso sejam utilizados
na análise final.

A integração entre ingestão e armazenamento de Fagner, fila de Vênisson,
cache de Filipe e recuperação/geração de Rauany foi validada três vezes.
Cada execução concluiu doze requisições sem falhas ou duplicações, com nove
acertos e três misses no cache.

Essas validações comprovam a conexão dos componentes na carga mínima.
Não avaliam qualidade semântica nem desempenho em produção. Os tempos
do lote excluem ingestão e carregamento inicial do índice.

## Memória e tratamento de falhas

No C5 de Katyane, as cargas de 100, 250 e 500 MiB elevaram o RSS médio de
116,20 para 516,18 MiB e o tempo médio de 0,138452 para 0,554763 segundo.

Foram observadas faltas menores de página, sem faltas maiores ou uso de swap.
O resultado demonstra crescimento do custo de alocação e acesso à memória,
mas não comprova esgotamento da RAM, thrashing ou paginação em disco.

No C6, as três tentativas de leitura de arquivo inexistente foram tratadas
como FileNotFoundError. O resultado demonstra o tratamento dessa falha no
script independente, sem comprovar recuperação de todas as falhas possíveis
do servidor integrado.

## Conclusão geral

Os resultados mostram que o funcionamento da aplicação depende tanto da
capacidade dos recursos quanto da forma de coordenar seu uso.

A fila limitada organiza o atendimento; os mecanismos de sincronização
preservam consultas; o cache aproveita a repetição; e o armazenamento mantém
os dados utilizados pela recuperação. A concorrência melhora o atendimento
da carga de espera testada, enquanto as observações de memória distinguem
crescimento de residência, faltas de página e uso de swap.

O protótipo tornou esses mecanismos observáveis e permitiu relacioná-los
a uma aplicação inspirada em RAG, respeitando as limitações descritas
no arquivo limitacoes.md.
