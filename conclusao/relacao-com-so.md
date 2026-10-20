# Relação com Sistemas Operacionais

## Processos, threads e escalonamento

A fila de consultas permite observar execução concorrente dentro
de um processo. Produtores e consumidores utilizam threads,
compartilham memória e dependem do escalonamento para avançar.

No C3, o aumento de um para quatro consumidores elevou a vazão média
de 4,96 para 19,37 consultas por segundo. Esse resultado é compatível
com a sobreposição dos períodos de espera simulada.

Concorrência não significa, necessariamente, paralelismo de CPU.
O resultado não permite concluir que uma geração real intensiva
em processamento teria a mesma aceleração.

Os atrasos da geração simulada também demonstram a diferença entre
tempo decorrido e tempo de CPU. A medição de parede inclui intervalos
em que a thread não executa. Entretanto, os dados não identificam
a causa específica desses intervalos.

## Memória compartilhada e sincronização

Produtores e consumidores acessam o mesmo buffer. O mutex estabelece
exclusão mútua durante inserções e retiradas, protegendo a estrutura
compartilhada.

Os semáforos cumprem outra responsabilidade: empty representa
vagas disponíveis e full representa itens disponíveis.
Proteger o buffer não substitui aguardar a condição necessária
para produzir ou consumir.

O limite da fila também controla o volume de consultas pendentes.
Quando o buffer está cheio, o produtor aguarda uma vaga,
em vez de ampliar indefinidamente a fila.

Na demonstração de falha, a ausência dessa espera resultou em nove
consultas descartadas por execução. Na correção, a sincronização
permitiu concluir todas as consultas.

O processamento ocorre fora do mutex, evitando que o atendimento
de uma consulta bloqueie todas as operações sobre o buffer.

## Cache compartilhado e região crítica

O cache mantém respostas e contadores acessados por vários trabalhadores.
Seu lock protege entradas, ordem de substituição e métricas.

A geração ocorre fora da região crítica, reduzindo o período
de exclusão mútua. Essa decisão permite atender consultas
concorrentemente, mas pode repetir a geração de uma chave
solicitada simultaneamente.

O experimento distingue, portanto, consistência do estado compartilhado
e eliminação de trabalho redundante. São objetivos relacionados,
mas não equivalentes.

## Memória física e memória virtual

O inventário do ambiente distingue MemFree de MemAvailable.
MemFree indica memória livre, enquanto MemAvailable estima
quanto pode ser disponibilizado a novas alocações considerando
parcelas recuperáveis.

O Linux utiliza parte da RAM para manter conteúdo de arquivos
no cache de páginas. Essa memória pode beneficiar leituras
posteriores e não representa, por si só, desperdício.

A recuperação de páginas do cache pode exigir trabalho do kernel.
Páginas modificadas podem precisar ser escritas antes da liberação.

RSS representa páginas residentes do processo, enquanto VSZ
representa seu espaço de endereçamento virtual. Um aumento de VSZ
não implica crescimento equivalente da RAM efetivamente ocupada.

O experimento de leitura e mmap relaciona esses conceitos ao acesso
a arquivos: um mapeamento pode reservar endereçamento antes que
todas as páginas sejam acessadas.

## Paginação e swap

No C5, o acesso às alocações em intervalos de 4 KiB esteve associado
ao crescimento de faltas menores de página.

Faltas menores podem ser resolvidas sem buscar o conteúdo
em armazenamento secundário. Por isso, sua ocorrência não significa
uso de swap.

Nas cargas avaliadas, não foram observadas faltas maiores
ou utilização de swap. O experimento mostrou crescimento
do consumo de memória, mas não demonstrou thrashing.

A existência de uma área de swap configurada também não comprova
que ela tenha sido utilizada durante uma execução.

## Arquivos, leitura convencional e mmap

A ingestão depende do sistema de arquivos para acessar os documentos.
Na leitura convencional, a aplicação solicita os dados por operações
de leitura. Com mmap, um arquivo é associado a uma região do espaço
de endereçamento virtual.

Ambos os métodos podem aproveitar o cache de páginas. Isso ajuda
a explicar diferenças entre passagens de leitura e entre arquivos
pequenos e maiores, sem estabelecer superioridade universal.

No pipeline de ingestão, o conteúdo mapeado é convertido em bytes
para decodificação. A medição corresponde a essa implementação,
incluindo suas cópias e etapas adicionais.

Bytes lidos logicamente não equivalem, necessariamente,
a bytes transferidos do dispositivo físico, pois o cache
pode atender parte das operações.

## Armazenamento persistente e SQLite

O SQLite mantém documentos, trechos, vetores e metadados
em estruturas persistentes organizadas em páginas e transações.

O tamanho do banco inclui dados e estruturas internas.
Consequentemente, não corresponde apenas ao tamanho do corpus
ou dos vetores.

Na integração, o índice é carregado pela thread principal
e a conexão é fechada antes do atendimento concorrente.
A recuperação posterior utiliza os dados em memória.

Essa escolha evita compartilhar entre consumidores a conexão SQLite
criada em outra thread. Em contrapartida, mantém trechos e vetores
na memória do processo durante o atendimento.

## Localidade e substituição

O C4 demonstra localidade em nível de aplicação.
Com consultas repetidas, LRU com capacidade de 32 entradas
atingiu aproximadamente 71,2% de acertos. Na carga distinta,
não houve acertos.

A diferença entre LRU e FIFO mostra que a política de substituição
influencia a preservação de entradas populares.

O ganho menor ao aumentar a capacidade de 32 para 128 entradas
também relaciona o dimensionamento ao conjunto de trabalho
da carga utilizada.

A analogia com caches do sistema operacional é conceitual.
O cache de respostas armazena resultados indexados por consulta,
enquanto o cache de páginas mantém conteúdo de arquivos.
As métricas de um não quantificam diretamente o comportamento do outro.

## Falhas e observabilidade

O C6 demonstra como uma tentativa de acesso a arquivo inexistente
é comunicada à aplicação e tratada como FileNotFoundError.

O registro controlado permite distinguir uma falha prevista
de encerramento inesperado. Entretanto, o tratamento dessa exceção
não demonstra recuperação de todas as falhas do servidor.

Os logs da fila e os eventos de recuperação permitem acompanhar
operações e métricas. A observabilidade é necessária para separar
resultados medidos de hipóteses sobre gargalos e comportamento
do ambiente.

## Relação com aplicações RAG

Em aplicações RAG, documentos, vetores e índices utilizam memória
e armazenamento; consultas disputam capacidade de atendimento;
filas organizam a espera; e caches evitam processamento repetido.

O GenResearch-Servidor torna essas relações observáveis por meio
de componentes simplificados. A integração demonstra o caminho
entre ingestão, armazenamento, fila, cache, recuperação e resposta,
sem apresentar os resultados simulados como previsão
para grandes modelos ou ambientes distribuídos.
