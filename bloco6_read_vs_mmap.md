6 - Leitura convencional vs. mmap + Memória Virtual (C1 + C2 + Parte E) — Giulian



Giulian Fabio Bastos Amorim Lima



 Objetivo



Comparar a leitura convencional de arquivos com `open()` e `read()` e o acesso a arquivos por mapeamento de memória usando `mmap`, observando desempenho, consumo de memória e faltas de página.



Corpus pequeno: arquivos de 64 KiB.

Corpus grande: arquivos de 8 MiB.

Repetições: 3 por arquivo e método, com 2 passagens.

Tamanho do bloco de leitura convencional: 65.536 bytes.


Leitura convencional



O programa abre o arquivo com `open()` e lê seu conteúdo em blocos usando `read()`.



Mapeamento de memória



O programa abre o arquivo e utiliza `mmap` para mapear seu conteúdo na memória virtual, acessando os dados em blocos.



Resultados observados:



Nos arquivos pequenos, o `mmap` apresentou menor tempo médio nas duas passagens. Nos arquivos grandes, a leitura convencional apresentou menor tempo médio, com diferenças relativamente pequenas.



Nas medições dos arquivos grandes, o `mmap` apresentou RSS e VSZ maiores. Isso é compatível com o mapeamento do arquivo, mas VSZ não representa diretamente a memória física ocupada.



A validação realizada comparou 36 pares de registros. Não foram encontradas diferenças na quantidade de bytes processados nem no SHA-256 entre os métodos.



Limitações
-Os tempos incluem o processamento necessário para calcular SHA-256.
-As faltas de página são diferenças observadas no processo e não representam exclusivamente as faltas causadas pelo arquivo.
-A primeira passagem não garante cache de disco frio.
-O resultado vale para o ambiente, corpus e parâmetros utilizados; não permite concluir que um método seja sempre superior.

Conclusão:



O experimento demonstra que o desempenho de `read()` e `mmap` depende do tamanho dos arquivos e das condições de execução. Para o corpus pequeno testado, `mmap` apresentou menor tempo médio. Para o corpus grande, `read()` apresentou uma pequena vantagem.



A escolha entre os métodos deve considerar o padrão de acesso, a memória disponível, a complexidade de implementação e o perfil da aplicação.



Os dois métodos acessam os dados de maneiras diferentes. O `read()` copia os dados para um buffer do programa, enquanto o `mmap` permite acessá-los por meio da memória virtual, podendo evitar essa cópia adicional.



Isso pode influenciar o tempo de leitura, mas também depende do tamanho do arquivo e do cache do sistema operacional. Por isso, a equipe fez três repetições para comparar os resultados com mais confiabilidade e evitar depender de uma única execução.

