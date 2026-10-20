# RelatÃ³rio individual â€” IngestÃ£o e Armazenamento do GenResearch-Servidor

## 1. Escopo e objetivo

Esta contribuiÃ§Ã£o implementa e valida o pipeline local de ingestÃ£o do GenResearch-Servidor. O escopo compreende leitura recursiva de arquivos `.txt` UTF-8, fragmentaÃ§Ã£o por palavras, vetorizaÃ§Ã£o determinÃ­stica simulada e persistÃªncia em SQLite. NÃ£o inclui servidor HTTP, fila, cache, geraÃ§Ã£o de respostas ou avaliaÃ§Ã£o de qualidade de recuperaÃ§Ã£o. A identificaÃ§Ã£o pessoal nÃ£o foi incluÃ­da porque nÃ£o hÃ¡ responsÃ¡vel individual confirmado para esta parte no repositÃ³rio.

## 2. Ambiente e mÃ©todo

A coleta foi executada em 19/10/2026 no Windows 11 (10.0.26200), AMD64, Python 3.14.7 e 12 CPUs lÃ³gicas reportadas. O commit de referÃªncia era `def19e2`; a Ã¡rvore tinha alteraÃ§Ãµes locais nÃ£o commitadas, incluindo esta implementaÃ§Ã£o e as evidÃªncias. NÃ£o hÃ¡ dependÃªncias externas: SQLite Ã© acessado pela biblioteca padrÃ£o. O ambiente nÃ£o Ã© Linux/WSL; por isso `/proc`, `getrusage` Linux, faltas menores/maiores, VSZ, RSS de pico e contadores de I/O nÃ£o foram coletados. NÃ£o se alterou cache de pÃ¡ginas ou configuraÃ§Ã£o global; processos novos nÃ£o equivalem a cache frio.

O script `experimentos/scripts/benchmark_ingestao.py` gerou corpus determinÃ­stico com a semente `genresearch-so-2026-2-seed-01`. Foram feitas trÃªs repetiÃ§Ãµes por modo, em ordem alternada standard/mmap, mmap/standard, standard/mmap. Cada repetiÃ§Ã£o iniciou novo processo Python e banco SQLite exclusivo, eliminando o efeito da deduplicaÃ§Ã£o na mediÃ§Ã£o. ParÃ¢metros comuns: 200 palavras por trecho, sobreposiÃ§Ã£o de 40 palavras e 128 posiÃ§Ãµes por vetor.

| Corpus | Documentos | Bytes reais |
|---|---:|---:|
| pequeno | 10 | 34940 |
| medio | 76 | 265610 |
| grande | 300 | 1048690 |

## 3. Pipeline, vetores e armazenamento

`standard` usa leitura convencional de bytes; `mmap` mapeia o arquivo apenas se nÃ£o vazio, fecha arquivo e mapeamento, e entÃ£o materializa `mapped[:]` para decodificar UTF-8. Portanto, mmap nÃ£o elimina a cÃ³pia de bytes/texto nesta implementaÃ§Ã£o. Os trechos preservam caminho relativo, identificador do documento e posiÃ§Ã£o ordinal. O arquivo vazio Ã© ignorado e erro de decodificaÃ§Ã£o Ã© registrado sem encerrar toda a ingestÃ£o.

Os vetores sÃ£o simulados: SHA-256 do texto com contador, expandido para dimensÃ£o configurÃ¡vel e normalizado em L2; o formato persistido Ã© `float32-le`. O mesmo texto Ã© reproduzÃ­vel entre processos, mas o vetor nÃ£o representa semÃ¢ntica e nÃ£o valida a qualidade de recuperaÃ§Ã£o. A recuperaÃ§Ã£o recebe lotes por `SQLiteIndex.iter_chunk_vectors(batch_size=128)`.

SQLite guarda `documents` (caminho relativo, bytes e SHA-256), `chunks` (documento, posiÃ§Ã£o e texto), `vectors` (BLOB, dimensÃ£o e formato), `index_config` e `ingestion_runs`. ReingestÃ£o idÃªntica nÃ£o duplica registros; conteÃºdo alterado substitui o documento e seus dependentes. MudanÃ§as de dimensÃ£o, tamanho ou sobreposiÃ§Ã£o exigem `--rebuild`, que torna a remoÃ§Ã£o explÃ­cita. O banco nÃ£o utiliza WAL: o tamanho medido Ã© somente o arquivo `.sqlite3` gerado em cada repetiÃ§Ã£o.

Tamanho do corpus Ã© a soma dos bytes dos textos de entrada. Volume dos vetores Ã© a soma medida dos BLOBs (`n_vetores Ã— 128 Ã— 4`); tamanho do SQLite inclui pÃ¡ginas, Ã­ndices, textos, metadados e os vetores, portanto nÃ£o Ã© igual ao volume de vetores nem mede E/S fÃ­sica.

## 4. Testes funcionais

`python -m unittest discover -s tests -v` executou 6 testes e todos passaram. Eles verificaram: fragmentaÃ§Ã£o e sobreposiÃ§Ã£o; validaÃ§Ã£o de parÃ¢metros; vetores reprodutÃ­veis e normalizados; persistÃªncia, reabertura e leitura em lote; reingestÃ£o sem duplicaÃ§Ã£o; equivalÃªncia do Ã­ndice standard/mmap; corpus inexistente; arquivo vazio; subpasta; documento modificado; configuraÃ§Ã£o divergente que requer reconstruÃ§Ã£o; e UTF-8 invÃ¡lido tratado como erro registrado. Durante a validaÃ§Ã£o, foi corrigido apenas o coletor: o processo-filho passou a usar `-X utf8`, pois o codepage do console do Windows impedia o coletor de decodificar seu JSON. NÃ£o houve correÃ§Ã£o funcional necessÃ¡ria no pipeline.

## 5. Resultados reais da coleta

| Corpus | Modo | MÃ©dia total (s) | Mediana (s) | DP amostral (s) | MÃ©dia leitura (s) |
|---|---|---:|---:|---:|---:|
| pequeno | standard | 0.032222 | 0.032998 | 0.003157 | 0.000664 |
| pequeno | mmap | 0.030746 | 0.029642 | 0.002126 | 0.000835 |
| medio | standard | 0.046374 | 0.047155 | 0.004370 | 0.005170 |
| medio | mmap | 0.047141 | 0.044832 | 0.005208 | 0.005793 |
| grande | standard | 0.097683 | 0.099653 | 0.004029 | 0.019726 |
| grande | mmap | 0.100051 | 0.096948 | 0.006811 | 0.022369 |

![Tempo mÃ©dio por modo](tempo_por_modo.svg)

Os resultados brutos contÃªm 18 linhas e mostram, em todas as repetiÃ§Ãµes, as mesmas contagens para cada corpus e modo. No corpus mÃ©dio, mmap teve mÃ©dia total menor (0,053986 s versus 0,061417 s); no grande, standard teve mÃ©dia menor (0,119132 s versus 0,129144 s). As amostras sÃ£o pequenas (n=3) e os tempos sÃ£o curtos; nÃ£o foi calculado p95 por baixa representatividade. Logo, os dados nÃ£o sustentam uma conclusÃ£o geral de superioridade do mmap.

## 6. RelaÃ§Ã£o com Sistemas Operacionais e limitaÃ§Ãµes

No modo convencional, a aplicaÃ§Ã£o solicita leitura de arquivo ao sistema; no modo mmap, o espaÃ§o de endereÃ§amento recebe um mapeamento e o sistema operacional pode trazer pÃ¡ginas sob demanda. Ambos estÃ£o sujeitos ao cache de pÃ¡ginas, que nÃ£o foi controlado. SQLite adiciona buffers, Ã­ndices, transaÃ§Ãµes e pÃ¡ginas de armazenamento; por isso o crescimento do Ã­ndice nÃ£o Ã© somente o crescimento dos vetores. A fragmentaÃ§Ã£o por documento evita carregar o corpus completo de uma vez, mas cada documento ainda Ã© lido e decodificado integralmente antes de ser fragmentado.

NÃ£o foram medidos pico de RSS, VSZ, faltas de pÃ¡gina ou contadores de E/S; nÃ£o sÃ£o inferidos de uma amostra. TambÃ©m nÃ£o houve teste em Linux/WSL nem controle de cache frio. A comparaÃ§Ã£o avalia custos do pipeline com vetores simulados, nÃ£o qualidade semÃ¢ntica, concorrÃªncia ou sincronizaÃ§Ã£o.

## 7. ReproduÃ§Ã£o e integraÃ§Ã£o

```bash
python -m unittest discover -s tests -v
python experimentos/scripts/benchmark_ingestao.py
python experimentos/scripts/generate_relatorio_ingestao.py
```

Os dados ficam em `experimentos/genresearch/evidencias/`: `raw_results.csv`, `summary.csv`, `corpora.json`, `environment.json`, bancos individuais e resumos JSON. O restante do projeto pode abrir `SQLiteIndex(caminho).iter_chunk_vectors(128)` para consumir texto, origem, posiÃ§Ã£o e vetor em lotes.

**Texto para a tabela de contribuiÃ§Ãµes:** â€œImplementaÃ§Ã£o e validaÃ§Ã£o da ingestÃ£o recursiva de corpus, fragmentaÃ§Ã£o configurÃ¡vel, vetores simulados determinÃ­sticos, persistÃªncia SQLite, testes funcionais e experimento comparativo entre leitura convencional e mmap.â€
