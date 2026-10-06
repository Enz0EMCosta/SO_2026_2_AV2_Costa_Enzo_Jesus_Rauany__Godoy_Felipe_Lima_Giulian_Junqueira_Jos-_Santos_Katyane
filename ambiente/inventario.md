# Inventário do ambiente de execução

Preencher no ambiente em que os experimentos forem medidos. Se forem usados
ambientes diferentes (por exemplo, Windows e WSL2), registrar cada um
separadamente e identificar em qual foram obtidos os resultados.

## Plataforma

| Item | Valor |
| --- | --- |
| Tipo de ambiente (Linux nativo, VM ou WSL2) | Pendente |
| Distribuição e versão | Pendente |
| Kernel | Pendente |
| Arquitetura | Pendente |
| Data da coleta | Pendente |

## Hardware e recursos

| Item | Valor |
| --- | --- |
| CPU (modelo e núcleos lógicos) | Pendente |
| Memória RAM | Pendente |
| Armazenamento e espaço disponível | Pendente |
| Limites de CPU/memória da VM ou WSL2, se aplicável | Pendente |

## Software

| Item | Versão/configuração |
| --- | --- |
| Python | Pendente |
| Git | Pendente |
| SQLite | Pendente |
| Modelo local (se usado) | Pendente |
| Dependências do projeto | Pendente |

## Como reproduzir o inventário

Registrar os comandos usados e seus resultados, por exemplo:

```bash
uname -a
python3 --version
sqlite3 --version
```

Para CPU, memória e armazenamento, anotar também a ferramenta consultada (por
exemplo, `lscpu`, `free -h` e `df -h`). Remover ou anonimizar identificadores
pessoais antes de publicar a saída completa dos comandos.
