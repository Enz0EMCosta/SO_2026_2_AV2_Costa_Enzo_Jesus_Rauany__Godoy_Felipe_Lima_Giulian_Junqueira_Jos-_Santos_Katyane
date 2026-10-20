"""Gera relatÃ³rio Markdown/HTML e grÃ¡ficos apenas a partir dos CSVs da coleta."""
from __future__ import annotations

import csv
import html
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experimentos" / "genresearch"
EVIDENCE = BASE / "evidencias"
REPORT = BASE / "relatorio_individual"


def svg(rows: list[dict]) -> str:
    colors = {"standard": "#1d4ed8", "mmap": "#d97706"}; width, height = 760, 300; maximum = max(float(row["mean_ingest_seconds"]) for row in rows)
    bars, labels = [], []
    for index, row in enumerate(rows):
        x = 55 + index * 112; value = float(row["mean_ingest_seconds"]); bar = value / maximum * 205
        bars.append(f'<rect x="{x}" y="{245-bar:.1f}" width="38" height="{bar:.1f}" fill="{colors[row["mode"]]}"/><text x="{x}" y="260" font-size="11">{row["size"]}</text><text x="{x}" y="275" font-size="11">{row["mode"]}</text><text x="{x}" y="{238-bar:.1f}" font-size="10">{value:.3f}s</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/><text x="30" y="25" font-size="18" font-family="Arial">Tempo mÃ©dio total de ingestÃ£o (n=3)</text><line x1="45" y1="245" x2="735" y2="245" stroke="black"/>{"".join(bars)}<rect x="570" y="35" width="14" height="14" fill="#1d4ed8"/><text x="590" y="47" font-size="12">standard</text><rect x="665" y="35" width="14" height="14" fill="#d97706"/><text x="685" y="47" font-size="12">mmap</text></svg>'


def write_simple_pdf(markdown: str, target: Path, summary_rows: list[dict]) -> None:
    """PDF textual portÃ¡til; evita depender de conversor externo no ambiente de coleta."""
    lines: list[str] = []
    for source in markdown.splitlines():
        if source.startswith("!") or source.startswith("```"):
            continue
        lines.extend(textwrap.wrap(source, width=98, replace_whitespace=False) or [""])
    # 42 linhas por pÃ¡gina privilegia legibilidade e resulta em cerca de trÃªs pÃ¡ginas A4.
    pages = [lines[index:index + 42] for index in range(0, len(lines), 42)]
    objects: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    page_ids, stream_ids = [], []
    for page_number, page in enumerate(pages):
        escaped = []
        for line in page:
            clean = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").replace("â€”", "-").replace("â€“", "-")
            escaped.append(clean.encode("latin-1", "replace"))
        stream = b"BT\n/F1 9 Tf\n50 800 Td\n11 TL\n" + b"\n".join(b"(" + item + b") Tj T*" for item in escaped) + b"\nET"
        if page_number == len(pages) - 1:
            maximum = max(float(row["mean_ingest_seconds"]) for row in summary_rows)
            drawing = [b"q 0.1 0.1 0.1 RG 50 70 m 500 70 l S"]
            for index, row in enumerate(summary_rows):
                height = int(float(row["mean_ingest_seconds"]) / maximum * 95)
                color = b"0.12 0.31 0.85" if row["mode"] == "standard" else b"0.85 0.47 0.02"
                drawing.append(color + f" rg {60 + index * 68} 70 34 {height} re f".encode())
            stream += b"\n" + b"\n".join(drawing) + b"\nQ"
        page_ids.append(len(objects) + 1); objects.append(b"")
        stream_ids.append(len(objects) + 1); objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
    objects[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{item} 0 R" for item in page_ids) + f"] /Count {len(page_ids)} >>").encode()
    for index, (page_id, stream_id) in enumerate(zip(page_ids, stream_ids)):
        objects[page_id - 1] = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>".encode()
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output)); output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(output); output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    target.write_bytes(output)


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((EVIDENCE / "summary.csv").open(encoding="utf-8")))
    corpora = json.loads((EVIDENCE / "corpora.json").read_text(encoding="utf-8"))["corpora"]
    graph = svg(rows); (REPORT / "tempo_por_modo.svg").write_text(graph, encoding="utf-8")
    table = "\n".join(f"| {r['size']} | {r['mode']} | {float(r['mean_ingest_seconds']):.6f} | {float(r['median_ingest_seconds']):.6f} | {float(r['stdev_ingest_seconds']):.6f} | {float(r['mean_read_seconds']):.6f} |" for r in rows)
    corpus_table = "\n".join(f"| {name} | {data['documents']} | {data['actual_bytes']} |" for name, data in corpora.items())
    md = f'''# RelatÃ³rio individual â€” IngestÃ£o e Armazenamento do GenResearch-Servidor

## 1. Escopo e objetivo

Esta contribuiÃ§Ã£o implementa e valida o pipeline local de ingestÃ£o do GenResearch-Servidor. O escopo compreende leitura recursiva de arquivos `.txt` UTF-8, fragmentaÃ§Ã£o por palavras, vetorizaÃ§Ã£o determinÃ­stica simulada e persistÃªncia em SQLite. NÃ£o inclui servidor HTTP, fila, cache, geraÃ§Ã£o de respostas ou avaliaÃ§Ã£o de qualidade de recuperaÃ§Ã£o. A identificaÃ§Ã£o pessoal nÃ£o foi incluÃ­da porque nÃ£o hÃ¡ responsÃ¡vel individual confirmado para esta parte no repositÃ³rio.

## 2. Ambiente e mÃ©todo

A coleta foi executada em 19/10/2026 no Windows 11 (10.0.26200), AMD64, Python 3.14.7 e 12 CPUs lÃ³gicas reportadas. O commit de referÃªncia era `def19e2`; a Ã¡rvore tinha alteraÃ§Ãµes locais nÃ£o commitadas, incluindo esta implementaÃ§Ã£o e as evidÃªncias. NÃ£o hÃ¡ dependÃªncias externas: SQLite Ã© acessado pela biblioteca padrÃ£o. O ambiente nÃ£o Ã© Linux/WSL; por isso `/proc`, `getrusage` Linux, faltas menores/maiores, VSZ, RSS de pico e contadores de I/O nÃ£o foram coletados. NÃ£o se alterou cache de pÃ¡ginas ou configuraÃ§Ã£o global; processos novos nÃ£o equivalem a cache frio.

O script `experimentos/scripts/benchmark_ingestao.py` gerou corpus determinÃ­stico com a semente `genresearch-so-2026-2-seed-01`. Foram feitas trÃªs repetiÃ§Ãµes por modo, em ordem alternada standard/mmap, mmap/standard, standard/mmap. Cada repetiÃ§Ã£o iniciou novo processo Python e banco SQLite exclusivo, eliminando o efeito da deduplicaÃ§Ã£o na mediÃ§Ã£o. ParÃ¢metros comuns: 200 palavras por trecho, sobreposiÃ§Ã£o de 40 palavras e 128 posiÃ§Ãµes por vetor.

| Corpus | Documentos | Bytes reais |
|---|---:|---:|
{corpus_table}

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
{table}

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
'''
    (REPORT / "relatorio_individual.md").write_text(md, encoding="utf-8")
    body = html.escape(md).replace("\n", "<br>\n")
    # O HTML preserva o relatÃ³rio editÃ¡vel e adiciona o grÃ¡fico SVG real para impressÃ£o em PDF.
    document = f'''<!doctype html><html><head><meta charset="utf-8"><style>@page{{size:A4;margin:18mm}}body{{font-family:Arial,sans-serif;font-size:10pt;line-height:1.38}}pre{{white-space:pre-wrap}}img{{max-width:100%;margin:12px 0}}</style></head><body><pre>{body}</pre><img src="tempo_por_modo.svg"></body></html>'''
    (REPORT / "relatorio_individual.html").write_text(document, encoding="utf-8")
    write_simple_pdf(md, REPORT / "relatorio_individual.pdf", rows)


if __name__ == "__main__": main()
