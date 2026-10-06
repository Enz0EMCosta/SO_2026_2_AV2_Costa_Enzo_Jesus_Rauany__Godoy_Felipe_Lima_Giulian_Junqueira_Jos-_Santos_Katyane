# GenResearch-Servidor

Repositório do trabalho da equipe **Gemma** para a disciplina de Sistemas
Operacionais. O projeto propõe implementar e avaliar um serviço simplificado de
recuperação aumentada por geração (RAG), com foco no comportamento do sistema
operacional durante a execução — não na qualidade linguística das respostas.

## Objetivos

- Ingerir documentos, dividi-los em trechos e gerar embeddings reais ou
  simulados.
- Persistir trechos, metadados e vetores.
- Processar consultas por uma fila compartilhada com múltiplos produtores e
  consumidores.
- Recuperar trechos relevantes e montar o contexto usado na resposta.
- Gerar respostas com um modelo local ou simular o custo computacional.
- Medir o comportamento de um cache compartilhado e registrar eventos com
  escrita concorrente protegida.
- Demonstrar um problema de sincronização reproduzível, sua correção e os
  efeitos observados.
- Executar seis configurações experimentais (C1–C6), com pelo menos três
  repetições cada, registrando métricas de desempenho, memória e armazenamento.

## Estrutura

```text
ambiente/                 Inventário do ambiente de execução
servidor/                 Pacotes Python dos componentes do serviço
sincronizacao/            Demonstração concorrente e evidências
experimentos/             Configurações, metodologia, scripts e resultados
memoria-armazenamento/    Análise de memória e armazenamento
conclusao/                Discussão, relação com SO e limitações
equipe/                   Contribuições e declaração de uso de IA
entrega/                  Materiais finais de entrega
```

## Ambiente e execução

O ambiente ainda precisa ser inventariado em [ambiente/inventario.md](ambiente/inventario.md).
As medições devem ser feitas e descritas em Linux nativo, VM Linux ou WSL2;
registre a opção utilizada e não misture resultados obtidos em ambientes
diferentes sem identificá-los.

A demonstração de condição de corrida usa apenas a biblioteca padrão do Python:

```bash
python sincronizacao/demonstracao.py
```

O restante do servidor e os scripts de experimentação serão implementados nas
etapas seguintes. Consulte [experimentos/metodologia.md](experimentos/metodologia.md)
antes de coletar dados.

## Estado do trabalho

Este repositório contém a estrutura inicial, documentação de planejamento e uma
demonstração executável de sincronização. Resultados, inventário de hardware e
software, contribuições da equipe e artefatos finais devem ser preenchidos com
dados realmente coletados; nenhum resultado experimental está presumido.
