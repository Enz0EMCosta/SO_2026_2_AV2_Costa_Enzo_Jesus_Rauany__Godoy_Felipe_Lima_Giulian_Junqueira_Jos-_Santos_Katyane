import time


def processar_consulta(consulta):
    """Simula o processamento de uma consulta por 0,2 segundo."""
    time.sleep(0.2)
    return {
        "consulta": consulta,
        "resposta": f"Resposta simulada para {consulta}",
        "simulado": True,
    }
