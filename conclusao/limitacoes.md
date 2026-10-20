# Limitações

## Simplificações do protótipo

O projeto utiliza documentos sintéticos, vetores simulados e geração por
espera temporizada. Os vetores derivados de SHA-256 são reproduzíveis,
mas não codificam relações semânticas.

Consequentemente, a recuperação por cosseno demonstra o funcionamento
da busca sobre vetores, sem comprovar relevância dos trechos selecionados.
A geração simulada também não reproduz o custo de inferência de um modelo
de linguagem real.

A validação integrada utiliza um corpus mínimo. Os experimentos isolados
com corpora maiores não constituem uma única avaliação de ponta a ponta
com todas as métricas coletadas simultaneamente.

## Ambientes e comparabilidade

As contribuições foram executadas em máquinas e versões de software
diferentes, incluindo Windows, WSL2 e uma máquina virtual Linux.

As comparações devem ser realizadas entre condições equivalentes
do mesmo experimento. Tempos de ingestão, alocação de memória,
recuperação e atendimento de consultas representam operações diferentes
e não devem ser comparados como uma mesma medida de desempenho.

A coleta original de ingestão em Windows não substitui as observações
de memória e paginação no ambiente Linux.

## Quantidade de repetições

Três repetições por configuração atendem ao mínimo adotado,
mas são insuficientes para generalizações estatísticas amplas.

No C3, cada execução contém doze consultas. Com o método do posto
mais próximo, o p95 corresponde ao maior valor observado.

No benchmark de recuperação e geração, as estatísticas agrupam
180 consultas por configuração. Essas consultas não equivalem
a 180 repetições independentes do ambiente experimental.

## Métricas e evidências

O C3 registra parâmetros, ambiente, commit-base e patch das alterações,
mas não contém horário individual para todas as execuções.

A utilização dos consumidores inclui períodos de sleep e representa
ocupação do trabalhador, não utilização de CPU.

Os tempos das validações integradas excluem ingestão e carregamento
inicial do índice. Os tempos de recuperação e geração não incluem
a espera da tarefa no executor.

Na branch de Giulian consultada, foram disponibilizadas análise e
capturas, mas não o script executável nem os CSVs brutos do experimento.
Essa ausência limita a reprodução e a conferência independente do bloco.

Algumas métricas de memória e E/S não foram coletadas em todos os
experimentos. Valores ausentes não devem ser estimados nem interpretados
como zero.

## Leitura, cache de páginas e mmap

A primeira passagem de leitura não garante cache frio.
Iniciar um processo novo não remove necessariamente os dados
do cache de páginas do sistema operacional.

Os tempos relatados no experimento de Giulian incluem o cálculo
de SHA-256. As faltas de página observadas no processo não podem
ser atribuídas exclusivamente ao acesso ao arquivo.

Na ingestão de Fagner, o conteúdo mapeado é materializado como bytes
para decodificação. Portanto, essa implementação não elimina todas
as cópias durante o processamento.

## Memória e paginação

O C5 limitou as alocações a 500 MiB para preservar a estabilidade
do equipamento. Nas cargas avaliadas, não foram observados uso
de swap nem faltas maiores.

Assim, o experimento não demonstrou thrashing ou degradação
por esgotamento de memória física.

As repetições de cada carga ocorreram no mesmo processo Python,
podendo sofrer influência do alocador e das execuções anteriores.

## Concorrência e cache

A espera simulada favorece a sobreposição do atendimento entre threads.
O ganho observado não comprova aceleração equivalente para uma carga
intensiva de CPU.

O cache utiliza a consulta como chave. Perguntas semanticamente
equivalentes com redações diferentes podem ocupar entradas distintas.

A geração fora do mutex permite trabalho repetido em misses simultâneos
da mesma chave, embora preserve a proteção das estruturas do cache.

Os registros de terminal são protegidos contra impressão intercalada,
mas não possuem uma sequência global que reproduza exatamente
a ordem das operações sobre o buffer.

## Falhas e encerramento

O encerramento normal dos consumidores utiliza mensagens sentinelas.
Não há timeout global para recuperar qualquer falha inesperada
de uma thread.

Os cenários de descarte e correção iniciam os consumidores em condições
diferentes. Sua comparação avalia preservação das consultas,
sem estabelecer ganho de desempenho entre os cenários.

O C6 de arquivo inexistente demonstra tratamento de FileNotFoundError
em um script isolado. Não avalia todas as falhas possíveis do serviço,
como indisponibilidade do banco, corrupção de índice ou interrupção
de um trabalhador.

## Valores atípicos

Uma consulta da primeira coleta de recuperação levou 47,0283 segundos.
O reteste também apresentou atrasos elevados na etapa de geração simulada.

Pausas do hospedeiro, contenção e escalonamento são hipóteses,
sem confirmação por monitoramento sincronizado. Os valores foram
preservados e não devem ser removidos apenas por divergirem da tendência.

A análise do reteste exige incorporar seus arquivos completos,
ainda separados da primeira coleta no momento desta revisão.

## Possíveis extensões

Uma avaliação futura poderá ampliar as cargas, padronizar os ambientes,
completar os dados brutos de leitura e mmap e coletar métricas por
requisição com horários individuais.

Também será importante monitorar a VM e o hospedeiro durante atrasos,
avaliar recuperação de falhas no fluxo completo e experimentar
embeddings semânticos e geração real.

Essas extensões exigirão novas medições. Os tempos simulados
não devem ser utilizados como previsão do desempenho de modelos reais.
