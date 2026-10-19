# servidor/cache — cache compartilhado de respostas

Guarda respostas recentes indexadas pela consulta, evitando repetir a etapa
cara de recuperação e geração. Compartilhado entre trabalhadores concorrentes;
todo acesso ao estado interno é serializado por um `threading.Lock`.

Apenas biblioteca padrão. Sem dependências externas.

## Interface

```python
from servidor.cache import CacheCompartilhado

cache = CacheCompartilhado(
    capacidade=32,        # nº máximo de entradas
    politica="lru",       # "lru" ou "fifo"
    usar_lock=True,       # False apenas para a demonstração de corrida (C6)
    normalizar=False,     # normaliza a chave antes de buscar
)

resposta, foi_acerto, latencia_s = cache.obter_ou_gerar(consulta, gerador)
```

**`obter_ou_gerar(consulta: str, gerador: Callable[[str], Any])`**
devolve `(valor, foi_acerto: bool, latencia_s: float)`.
Se a consulta estiver no cache, devolve o valor guardado. Caso contrário,
chama `gerador(consulta)`, guarda o resultado e o devolve.

### Contrato com os demais componentes

O `gerador` é qualquer função que receba a consulta e devolva a resposta. O
cache não conhece seu funcionamento interno.

- **`servidor/fila`** chama `obter_ou_gerar` de dentro de cada trabalhador. A
  mesma instância de cache é compartilhada por todos — é para isso que serve o
  mutex.
- **`servidor/recuperacao` + `servidor/resposta`** fornecem o `gerador`:
  qualquer `Callable[[str], Any]` serve, seja geração real por modelo local ou
  custo simulado.

Enquanto `recuperacao` e `resposta` não estiverem prontos,
`experimentos/scripts/c4_cache.py` usa um gerador simulado com atraso
proporcional ao tamanho da consulta. Para integrar, basta passar a função real
como segundo argumento; nada mais muda.

## Métricas

`cache.metricas` devolve um objeto com:

| Campo | Significado |
|---|---|
| `acertos` / `erros` | consultas servidas pelo cache / que exigiram geração |
| `taxa_acerto` / `taxa_erro` | proporções correspondentes |
| `substituicoes` | entradas descartadas por falta de capacidade |
| `tamanho_atual` / `capacidade` | ocupação e limite |
| `tempo_economizado_s` | soma dos custos de geração evitados |
| `tempo_gerando_s` | tempo efetivamente gasto gerando |

O tempo economizado é exato, não estimado: cada entrada guarda o custo que teve
para ser produzida, e cada acerto credita esse valor.

## Decisões de projeto

**A geração ocorre fora do mutex.** Segurar o lock durante uma operação cara
serializaria todos os trabalhadores e anularia a concorrência. O preço é que
duas threads podem gerar a mesma chave simultaneamente — trabalho duplicado,
não inconsistência. Trade-off deliberado entre contenção e desperdício; nas
medições, custou cerca de um ponto percentual de taxa de acerto ao passar de 1
para 4 trabalhadores.

**A chave é a consulta exata, por padrão.** Consultas semanticamente
equivalentes com redação diferente contam como entradas distintas. Com
`normalizar=True`, a chave passa por minúsculas, colapso de espaços e remoção
de pontuação de borda. Acerto por similaridade semântica exigiria comparação de
embeddings, fora do recorte adotado.

**`usar_lock=False` existe apenas para a demonstração de C6.** Nunca usar em
medição de desempenho.

## Experimentos

```bash
python3 experimentos/scripts/c4_cache.py --consultas 200 --repeticoes 3
python3 experimentos/scripts/corrida_cache.py
```

Parâmetros registrados em `experimentos/configuracoes.md`; resultados brutos em
`experimentos/resultados/`.