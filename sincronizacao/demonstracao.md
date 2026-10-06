# Demonstração de sincronização

## Problema e controle

O script `demonstracao.py` apresenta dois trabalhadores que incrementam um
contador compartilhado. Na primeira execução, uma barreira faz ambos lerem o
mesmo valor antes de qualquer escrita. Assim, uma das atualizações é perdida em
cada iteração, reproduzindo uma condição de corrida de forma controlada.

Na segunda execução, cada incremento é protegido por `threading.Lock` (mutex).
O acesso de leitura-modificação-escrita passa a ser uma seção crítica e o
contador final deve corresponder ao total de incrementos.

Execute com:

```bash
python sincronizacao/demonstracao.py
```

O script verifica os dois resultados e termina com erro explícito se a falha não
for reproduzida ou se a versão protegida estiver incorreta.

## Análise a completar

Após executar no ambiente inventariado, registrar:

- versão do Python e ambiente usados;
- valores observados para as duas execuções;
- por que a barreira torna a atualização perdida reproduzível;
- como o mutex protege a seção crítica;
- custo/impacto observado da sincronização, se medido.

## Evidências

Guardar nesta pasta capturas ou saídas de execução com data e ambiente
identificados. Não registrar evidências que não tenham sido coletadas.
