# Análise de memória e armazenamento

## 1. Objetivo

Relacionar o funcionamento do GenResearch-Servidor ao uso de memória,
armazenamento, cache de páginas e memória virtual, considerando as
contribuições de todos os integrantes.

A análise reúne observações do ambiente, ingestão e persistência,
leitura convencional e mmap, fila concorrente, recuperação de contexto,
cache compartilhado e experimentos controlados de memória e falha.

Os experimentos foram executados em ambientes e cargas diferentes.
Por isso, suas métricas não devem ser comparadas diretamente como
se representassem uma única execução do servidor.

## 2. Ambiente e interpretação da memória

O inventário elaborado por Enzo documenta os recursos do ambiente Linux
e os comandos utilizados para observar memória e armazenamento.

A interpretação das medições exige distinguir:

- **MemFree:** memória completamente livre.
- **MemAvailable:** estimativa de memória disponível para novas
  alocações sem necessidade de swap, considerando parcelas recuperáveis.
- **Cache de páginas:** conteúdo de arquivos mantido em RAM para
  favorecer acessos posteriores.
- **Swap:** armazenamento utilizado pelo sistema operacional para
  manter páginas de memória fora da RAM.
- **RSS:** memória residente associada ao processo.
- **VSZ:** espaço de endereçamento virtual do processo.

Memória ocupada pelo cache de páginas não representa, por si só,
desperdício. Parte desse conteúdo pode ser recuperada quando outras
alocações precisam de espaço. A liberação pode exigir trabalho do
kernel e escrita de páginas modificadas.

Da mesma forma, VSZ elevado não significa que todo o espaço virtual
esteja ocupando memória física. A existência de swap configurada
também não comprova sua utilização durante os experimentos.

O inventário de um integrante não representa automaticamente os
ambientes utilizados pelos demais.

## 3. Corpus, vetores e persistência

A implementação de Fagner realiza leitura recursiva de arquivos TXT,
fragmentação por palavras, geração de vetores simulados e persistência
em SQLite.

O banco armazena documentos, trechos, metadados, vetores e informações
das execuções de ingestão. Os trechos mantêm sua associação com
o documento de origem e sua posição no texto.

Na coleta comparativa de ingestão, foram utilizados:

| Corpus | Documentos | Tamanho real (bytes) |
|---|---:|---:|
| Pequeno | 10 | 34.940 |
| Médio | 76 | 265.610 |
| Grande | 300 | 1.048.690 |

Os vetores possuem 128 dimensões, armazenadas como valores float32,
correspondendo a 512 bytes por vetor. Esse volume não representa
o tamanho total do índice, pois o SQLite também mantém textos,
metadados, índices e estruturas internas de páginas.

Na validação integrada inicial, um documento produziu um trecho
e um vetor, com banco de 40.960 bytes. Esse exemplo verifica
a conexão dos componentes, sem representar a carga completa
dos experimentos de ingestão.

Os vetores são determinísticos por SHA-256 e não codificam
similaridade semântica.

## 4. Leitura convencional e mmap

### 4.1 Experimento de Giulian

O experimento compara leitura convencional com open/read e acesso
por mmap, considerando arquivos de 64 KiB e 8 MiB, três repetições
por arquivo e método e duas passagens.

A análise disponibilizada por Giulian relata:

- Menor tempo médio com mmap nos arquivos pequenos.
- Pequena vantagem da leitura convencional nos arquivos maiores.
- RSS e VSZ maiores com mmap nas medições de arquivos grandes.
- Equivalência de bytes processados e SHA-256 em 36 pares de registros.

Esses resultados mostram que o método de acesso influencia
o comportamento observado, mas não estabelecem uma escolha
universalmente superior.

Os tempos incluem o cálculo de SHA-256. A primeira passagem
não garante cache frio, e as faltas de página do processo
não representam exclusivamente o acesso ao arquivo.

Na branch consultada, foram disponibilizadas análise e capturas,
mas não o script nem os CSVs brutos correspondentes.
Essa ausência limita a reprodução independente do experimento.

### 4.2 Comparação no pipeline de ingestão

A coleta de Fagner também compara leitura convencional e mmap,
mas mede um pipeline que inclui fragmentação, vetorização
e persistência.

| Corpus | Leitura convencional: tempo total médio (s) | mmap: tempo total médio (s) |
|---|---:|---:|
| Pequeno | 0,032222 | 0,030746 |
| Médio | 0,046374 | 0,047141 |
| Grande | 0,097683 | 0,100051 |

Fonte: experimentos/genresearch/evidencias/summary.csv.

As diferenças devem ser interpretadas considerando os tempos
curtos e as três repetições por condição.

Nessa implementação, o conteúdo mapeado é materializado em bytes
antes da decodificação. Portanto, o uso de mmap não elimina
todas as cópias do processamento.

Esse experimento não deve ser confundido com a comparação específica
de Giulian, pois os corpora e as operações medidas são diferentes.

## 5. Cache de páginas e aquecimento

A leitura convencional e o mmap podem aproveitar o cache de páginas
do sistema operacional.

Uma leitura posterior pode encontrar conteúdo já residente em RAM,
reduzindo acessos ao dispositivo. Entretanto, iniciar outro processo
não garante que esse conteúdo tenha sido removido do cache.

Assim, primeira e segunda passagens devem ser identificadas
sem presumir que correspondam, respectivamente, a disco frio
e cache aquecido.

Também é necessário distinguir bytes solicitados pela aplicação
de bytes fisicamente transferidos pelo armazenamento.
O cache pode atender parte das operações.

## 6. Fila e recursos compartilhados

A fila implementada por Vênisson limita a quantidade de consultas
pendentes no buffer. Nos experimentos C3, sua capacidade foi de
três itens, com dois produtores e configurações de um, dois
e quatro consumidores.

O limite estabelece controle sobre a entrada: quando não há vagas,
o produtor aguarda, em vez de ampliar indefinidamente a fila.

Os testes registraram tamanho médio e máximo da fila, espera,
latência e vazão. Essas métricas descrevem a ocupação do buffer,
mas não quantificam diretamente seu consumo de RAM.

O aumento de consumidores reduziu a espera na carga simulada,
sem perdas ou duplicações. Entretanto, não foram coletadas
medições de RSS e VSZ que permitam quantificar o custo de memória
de cada configuração de threads.

A falha controlada descartou nove consultas por execução.
A correção com espera por vagas preservou as doze consultas,
mantendo a capacidade limitada.

## 7. Cache compartilhado de respostas

O cache de Filipe mantém respostas em memória com capacidade
limitada por quantidade de entradas e políticas LRU ou FIFO.

Na carga repetida, com quatro trabalhadores e capacidade 32,
LRU alcançou aproximadamente 71,2% de acertos. Com capacidade 128,
a taxa passou para 73,3%, indicando retorno decrescente
nesse conjunto de consultas.

Na carga distinta, não houve acertos. Nesse caso, aumentar
a capacidade não trouxe reaproveitamento de respostas.

A capacidade em entradas não equivale a um limite exato em bytes:
respostas podem ter tamanhos diferentes, e as estruturas Python
também possuem custo de memória.

O cache de respostas é diferente do cache de páginas do Linux.
O primeiro evita etapas da aplicação; o segundo pode evitar
acessos físicos a arquivos. As métricas de um não medem
diretamente o comportamento do outro.

## 8. Recuperação e geração

A recuperação de Rauany carrega os trechos e vetores do SQLite
antes do atendimento concorrente. A conexão é fechada após
o carregamento, e os consumidores consultam os dados em memória.

Essa estratégia evita reler o índice a cada consulta e não
compartilha a conexão SQLite entre threads. Em contrapartida,
mantém uma cópia dos trechos e vetores na memória do processo.

O contexto possui um limite configurado de caracteres.
Por isso, aumentar top_k de quatro para oito não implica
duplicar o contexto enviado à geração.

A implementação limita o texto dos trechos, mas não contabiliza
os separadores entre eles nesse orçamento. O tamanho final pode
ultrapassar ligeiramente o limite configurado.

A geração utiliza espera simulada proporcional ao contexto.
As medições não representam o consumo de memória de um modelo
de linguagem real, seus pesos ou seu cache de inferência.

## 9. Aumento controlado de memória — C5

O experimento de Katyane alocou blocos de 100, 250 e 500 MiB,
com acesso em intervalos de 4 KiB e três repetições por carga.

| Carga | Tempo médio (s) | RSS médio (MiB) | Faltas menores por repetição | Faltas maiores | Swap observada (MiB) |
|---|---:|---:|---:|---:|---:|
| 100 MiB | 0,138452 | 116,20 | 25.601 | 0 | 0 |
| 250 MiB | 0,280650 | 266,21 | 64.001 | 0 | 0 |
| 500 MiB | 0,554763 | 516,18 | 128.001 | 0 | 0 |

Fonte: experimentos/analise_c5_c6.md e resultados de C5.

O crescimento da carga esteve associado ao aumento do RSS,
do tempo de execução e das faltas menores de página.

Não foram observadas faltas maiores nem uso de swap.
Portanto, o experimento demonstra o custo crescente da alocação
e do acesso à memória, sem comprovar thrashing ou esgotamento
da memória física.

As repetições de cada carga ocorreram no mesmo processo Python,
podendo sofrer influência do alocador e das execuções anteriores.

## 10. Falha de acesso a arquivo — C6

O experimento C6 de Katyane tentou ler um arquivo inexistente
e tratou FileNotFoundError nas três repetições.

O resultado demonstra que uma falha de entrada pode ser
identificada e registrada sem encerrar inesperadamente o script.

Esse teste é independente da falha de saturação da fila.
Ele não comprova recuperação de indisponibilidade do SQLite
ou de corrupção dos dados do servidor.

## 11. Limitações das medições

Os experimentos foram realizados em ambientes diferentes,
incluindo Windows, WSL2 e VM Linux. Seus tempos absolutos
não devem ser comparados diretamente entre blocos.

Nem todas as contribuições coletaram RSS, VSZ, faltas de página
ou contadores de E/S. Métricas ausentes não foram estimadas.

Os atrasos atípicos observados na geração simulada não constituem
evidência de swap ou pressão de memória. Sem monitoramento
sincronizado, sua causa permanece indeterminada.

Os experimentos isolados e as validações integradas também
medem etapas distintas. O tempo de atendimento do lote integrado
exclui ingestão e carregamento inicial do índice.

## 12. Considerações finais

A avaliação mostrou que memória e armazenamento influenciam
diferentes etapas do GenResearch-Servidor.

A persistência mantém documentos e vetores disponíveis,
o cache de páginas pode favorecer leituras posteriores,
a fila limitada controla consultas pendentes e o cache
de respostas evita processamento repetido.

A escolha entre leitura convencional e mmap depende do padrão
de acesso e das condições do experimento. O aumento de memória
alocada elevou o RSS e o tempo, mas não produziu evidência
de paginação em disco nas cargas avaliadas.

Os resultados relacionam o protótipo aos mecanismos do sistema
operacional sem extrapolar suas observações para modelos reais,
grandes corpora ou ambientes distribuídos.
