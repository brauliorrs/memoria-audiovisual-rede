# Workflow de revisão tardia da visão pública

## Finalidade

O workflow `digital-infrastructure-publication-revision.yml` permite incorporar decisões curatoriais concluídas depois do fechamento de um snapshot sem executar nova coleta e sem alterar a visão pública inicial.

## Acionamento

O workflow é exclusivamente manual e exige:

- `snapshot_id`: snapshot histórico já consolidado;
- `reason`: justificativa curatorial da regeneração;
- `requested_by`: identificador do responsável pela solicitação.

## Pré-condições

A operação é bloqueada quando:

- a branch `digital-infrastructure-history` não existe;
- o identificador do snapshot é inválido;
- a visão pública inicial não existe;
- o arquivo de triagem original não existe;
- o ledger histórico não está disponível.

## Sequência

```text
restaurar branch histórica
→ validar snapshot e produtos originais
→ reconstruir visão a partir da triagem e do ledger
→ criar revision_NNNN
→ validar manifesto e arquivos derivados
→ consolidar somente a visão pública revisada
→ publicar cópia operacional temporária
```

## Garantias

- nenhuma coleta é executada;
- `events.json` e `manifest.json` da versão inicial permanecem imutáveis;
- revisões anteriores permanecem preservadas;
- o número da nova revisão é sequencial;
- justificativa e responsável são obrigatórios;
- uma execução malsucedida não altera a branch histórica;
- o artefato de 90 dias é apenas uma cópia operacional, não a memória principal.

## Concorrência

O grupo de concorrência inclui o `snapshot_id`. Duas regenerações do mesmo snapshot não são executadas simultaneamente, evitando disputa pelo próximo número de revisão.

## Limite

O workflow não aprova decisões humanas. Ele apenas materializa uma nova versão derivada com base nas decisões que já estão registradas no ledger e satisfazem o quórum de publicação.
