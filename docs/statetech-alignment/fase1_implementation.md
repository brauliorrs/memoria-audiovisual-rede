# Fase 1 — núcleo executável de dados e proveniência

## Escopo

Este incremento implementa o núcleo operacional da camada Estado–tecnologia. Ele não adapta coletores, não executa auditorias empíricas e não publica resultados.

## Componentes implementados

- identificadores determinísticos de entidades e versões;
- modelos de entidade, evidência e proveniência;
- validação integral com JSON Schema Draft 2020-12;
- ledger append-only com uma linha JSONL por transação lógica;
- lock cooperativo para serializar escritas entre processos;
- registro conjunto de entidade, evidências e proveniência;
- índices reconstruíveis e integridade referencial;
- cadeia obrigatória de `previous_version_id`;
- aliases curados e sugestões conservadoras de duplicidade;
- decisões formais de `merge`, `split`, `redirect` e `keep_separate`;
- auditoria reconstruível da cadeia histórica;
- recuperação controlada de cauda truncada com backup;
- contrato de adaptadores para a Fase 2;
- testes unitários do núcleo.

## Organização

```text
src/memoria_audiovisual/statetech/
├── adapters.py
├── audit.py
├── contracts.py
├── entity_decisions.py
├── evidence.py
├── ids.py
├── index.py
├── integrity.py
├── ledger.py
├── locking.py
├── models.py
├── persistence.py
├── recovery.py
├── resolution.py
├── service.py
└── validation.py
```

## Fluxo de gravação

```text
entrada
→ validação do contrato
→ geração de IDs
→ reconstrução do índice
→ validação de versões, evidências e referências
→ aquisição do lock de escrita
→ commit lógico único no ledger
→ liberação do lock
```

## Resolução e decisões curatoriais

Aliases somente resolvem entidades quando foram explicitamente curados. Similaridade lexical gera candidatos, nunca fusão automática. Alterações de identidade exigem uma decisão registrada com origem, destino, justificativa, responsável, evidências, estado e data. Apenas decisões aprovadas de `merge` ou `redirect` produzem mapas de redirecionamento.

## Concorrência

O backend JSONL utiliza arquivo `.lock` criado de modo exclusivo. Um segundo processo cooperativo aguarda até o timeout configurado. O lock é removido ao final da operação, inclusive quando ocorre exceção. Essa garantia reduz colisões locais, mas não equivale a transações ACID nem protege contra processos que ignorem o protocolo.

## Auditoria e recuperação

A auditoria percorre o ledger desde o início e registra violações por código e severidade. A recuperação automática só é permitida quando o defeito está restrito à última linha; antes do corte, o arquivo original é preservado em `.bak`.

## Interface da Fase 2

`SourceAdapter` define o contrato mínimo para transformar fontes externas em `AdaptedRecord`. Adaptadores não persistem nem publicam diretamente: entregam payload, chave natural, proveniência, evidências, referências e versão anterior ao serviço da Fase 1.

## Garantias

1. Estados anteriores não são sobrescritos.
2. Versões duplicadas e referências órfãs são bloqueadas.
3. Atualizações apontam para a versão imediatamente anterior.
4. Evidências e proveniência integram o mesmo commit lógico.
5. Escritas cooperativas são serializadas.
6. Aliases e redirecionamentos conflitantes são rejeitados.
7. Merge e split exigem decisão curatorial explícita.
8. Índices e auditorias são reconstruíveis a partir do ledger.
9. Reparos preservam backup.
10. Coletores e publicação permanecem desacoplados.

## Limites atuais

- não há banco relacional ou transação ACID;
- o lock é cooperativo e local ao sistema de arquivos;
- não há fusão ou split automático;
- não há compactação formal dos índices derivados;
- o relatório de integridade ainda precisa ser exportado diretamente no schema estrutural;
- os coletores existentes ainda não usam `SourceAdapter`.

## Próximo incremento

- exportar auditorias no `integrity_report.schema.json`;
- persistir decisões de entidade no ledger com validação do schema;
- compactar e verificar índices derivados;
- concluir critérios de aceite da Fase 1;
- iniciar adaptadores concretos da Fase 2 somente após integração deste PR.
