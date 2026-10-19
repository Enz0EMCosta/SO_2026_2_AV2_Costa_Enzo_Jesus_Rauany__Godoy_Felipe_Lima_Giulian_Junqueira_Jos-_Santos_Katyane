"""Cache compartilhado de respostas — GenResearch-Servidor.

Compartilha respostas recentes entre trabalhadores concorrentes e contabiliza
acertos, erros e substituições.

Uso:
    from servidor.cache import CacheCompartilhado

    cache = CacheCompartilhado(capacidade=32, politica="lru")
    resposta, foi_acerto, latencia = cache.obter_ou_gerar(consulta, gerador)
"""

from servidor.cache.cache import CacheCompartilhado, Metricas

__all__ = ["CacheCompartilhado", "Metricas"]