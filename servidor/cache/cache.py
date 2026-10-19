"""
Cache compartilhado de respostas — GenResearch-Servidor
Bloco 5 (Parte B + C4) — Filipe

Guarda resultados recentes de consultas para evitar repetir a etapa cara de
recuperação e geração. O cache é compartilhado entre múltiplos trabalhadores
concorrentes, portanto todo acesso ao estado interno é serializado por um
mutex (threading.Lock).

Políticas de remoção implementadas:
  - LRU  (Least Recently Used): descarta a entrada usada há mais tempo
  - FIFO (First In, First Out):  descarta a entrada mais antiga inserida

Métricas coletadas (item 10 do enunciado):
  - acertos, erros, taxa de acerto
  - substituições (evictions)
  - tamanho atual e capacidade
  - tempo economizado
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field, asdict
from typing import Callable, Any


@dataclass
class Metricas:
    """Contadores do cache. Lidos e escritos sempre sob o mutex."""
    acertos: int = 0
    erros: int = 0
    substituicoes: int = 0
    tempo_economizado_s: float = 0.0
    tempo_gerando_s: float = 0.0
    tamanho_atual: int = 0
    capacidade: int = 0
    politica: str = ""

    @property
    def total_consultas(self) -> int:
        return self.acertos + self.erros

    @property
    def taxa_acerto(self) -> float:
        t = self.total_consultas
        return self.acertos / t if t else 0.0

    @property
    def taxa_erro(self) -> float:
        t = self.total_consultas
        return self.erros / t if t else 0.0

    def como_dict(self) -> dict:
        d = asdict(self)
        d["total_consultas"] = self.total_consultas
        d["taxa_acerto"] = round(self.taxa_acerto, 4)
        d["taxa_erro"] = round(self.taxa_erro, 4)
        return d


@dataclass
class _Entrada:
    """Valor guardado mais o custo que ele teve para ser produzido.

    Guardar o custo permite contabilizar o tempo economizado com precisão:
    em cada acerto, credita-se exatamente o custo que aquela entrada teve
    quando foi gerada, em vez de uma média estimada.
    """
    valor: Any
    custo_s: float
    criada_em: float = field(default_factory=time.monotonic)


class CacheCompartilhado:
    """Cache de respostas com capacidade fixa e remoção por LRU ou FIFO.

    Parâmetros
    ----------
    capacidade : int
        Número máximo de entradas. Ao exceder, uma entrada é removida.
    politica : {"lru", "fifo"}
        Critério de remoção.
    usar_lock : bool
        Quando False, o cache opera SEM exclusão mútua. Serve apenas para
        demonstrar a condição de corrida da Parte D (Opção 2); nunca deve
        ser usado em medição de desempenho.
    normalizar : bool
        Quando True, a chave é normalizada antes da busca (minúsculas,
        espaços colapsados, pontuação de borda removida). Afeta diretamente
        a taxa de acerto em consultas semanticamente próximas.
    """

    def __init__(
        self,
        capacidade: int = 32,
        politica: str = "lru",
        usar_lock: bool = True,
        normalizar: bool = False,
    ) -> None:
        politica = politica.lower()
        if politica not in ("lru", "fifo"):
            raise ValueError(f"política desconhecida: {politica}")
        if capacidade < 1:
            raise ValueError("capacidade deve ser >= 1")

        self.capacidade = capacidade
        self.politica = politica
        self.normalizar = normalizar
        self._usar_lock = usar_lock

        self._dados: OrderedDict[str, _Entrada] = OrderedDict()
        self._lock = threading.Lock() if usar_lock else _LockFalso()
        self._metricas = Metricas(capacidade=capacidade, politica=politica)

    # ------------------------------------------------------------------
    # chave
    # ------------------------------------------------------------------
    def _chave(self, consulta: str) -> str:
        if not self.normalizar:
            return consulta
        k = consulta.strip().lower()
        k = " ".join(k.split())
        return k.strip(" .,:;!?\"'")

    # ------------------------------------------------------------------
    # operações
    # ------------------------------------------------------------------
    def obter_ou_gerar(
        self,
        consulta: str,
        gerador: Callable[[str], Any],
    ) -> tuple[Any, bool, float]:
        """Devolve o valor da consulta, gerando-o se ainda não estiver no cache.

        Retorna (valor, foi_acerto, latencia_s).

        A geração ocorre FORA do mutex: segurar o lock durante uma operação
        cara serializaria todos os trabalhadores e anularia a concorrência.
        O preço dessa escolha é que duas threads podem gerar a mesma chave
        simultaneamente (trabalho duplicado, não inconsistência) — um
        trade-off deliberado entre contenção e desperdício.
        """
        chave = self._chave(consulta)
        inicio = time.perf_counter()

        # --- tentativa de acerto ---
        with self._lock:
            entrada = self._dados.get(chave)
            if entrada is not None:
                if self.politica == "lru":
                    self._dados.move_to_end(chave)
                self._metricas.acertos += 1
                self._metricas.tempo_economizado_s += entrada.custo_s
                return entrada.valor, True, time.perf_counter() - inicio

            self._metricas.erros += 1

        # --- erro: gera fora do lock ---
        t0 = time.perf_counter()
        valor = gerador(consulta)
        custo = time.perf_counter() - t0

        # --- insere ---
        with self._lock:
            self._metricas.tempo_gerando_s += custo
            if chave not in self._dados and len(self._dados) >= self.capacidade:
                self._dados.popitem(last=False)  # remove o primeiro da ordem
                self._metricas.substituicoes += 1
            self._dados[chave] = _Entrada(valor=valor, custo_s=custo)
            if self.politica == "lru":
                self._dados.move_to_end(chave)
            self._metricas.tamanho_atual = len(self._dados)

        return valor, False, time.perf_counter() - inicio

    def limpar(self) -> None:
        with self._lock:
            self._dados.clear()
            self._metricas = Metricas(
                capacidade=self.capacidade, politica=self.politica
            )

    @property
    def metricas(self) -> Metricas:
        with self._lock:
            self._metricas.tamanho_atual = len(self._dados)
            return self._metricas

    def __len__(self) -> int:
        with self._lock:
            return len(self._dados)

    def __repr__(self) -> str:
        m = self._metricas
        return (
            f"<CacheCompartilhado politica={self.politica} "
            f"cap={self.capacidade} tam={len(self._dados)} "
            f"acertos={m.acertos} erros={m.erros} subst={m.substituicoes}>"
        )


class _LockFalso:
    """Substituto do mutex que não protege nada.

    Usado apenas na demonstração de condição de corrida (Parte D, Opção 2).
    """

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def acquire(self, *args, **kwargs):
        return True

    def release(self):
        pass