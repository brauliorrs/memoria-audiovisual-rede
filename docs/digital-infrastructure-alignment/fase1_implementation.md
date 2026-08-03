# Fase 1 — núcleo executável de dados e proveniência

## Escopo

Este incremento implementa o núcleo operacional da camada infraestrutura digital. Ele não adapta coletores, não executa auditorias empíricas e não publica resultados.

## Componentes implementados

- identificadores determinísticos para entidades e versões imutáveis;
- modelos de entidade, evidência, proveniência e decisão curatorial;
- validação integral com JSON Schema Draft 2020-12;
- ledger append-only com uma linha JSONL por transação lógica;
- lock cooperativo local para serializar escritas;
- registro conjunto de entidade, evidências e proveniência;
- persistência validada de decisões de `merge`, `split`, `redirect` e `keep_separate`;
- índices reconstruíveis de entidades, versões e evidências;
- snapshots compactos e verificáveis dos índices derivados;
- integridade referencial e cadeia obrigatória de `previous_version_id`;
- aliases curados e sugestões conservadoras de duplicidade;
- auditoria reconstruível da cadeia histórica;
- exportação do relatório de integridade conforme o schema versionado;
- inspeção e recuperação controlada de cauda truncada, sempre com backup;
- interface `SourceAdapter` para os adaptadores da Fase 2;
- testes unitários e testes de aceite do núcleo.

## Organização

```text
src/memoria_audiovisual/digital_infrastructure/
├── adapters.py
├── audit.py
├── contracts.py
├── entity_decisions.py
├── evidence.py
├── ids.py
├── index.py
├── index_store.py
├── integrity.py
├── ledger.py
├── locking.py
├── models.py
├── persistence.py
├── recovery.py
├── reporting.py
├── resolution.py
├── service.py
└── validation.py
```

## Fluxo de gravação

```text
entrada
→ validação do contrato
→ geração do entity_id e version_id
→ reconstrução do índice do ledger
→ validação da cadeia de versões
→ validação das evidências e referências
→ composição da proveniência
→ aquisição do lock cooperativo
→ commit lógico único no ledger
→ liberação do lock
```

## Decisões curatoriais

Decisões de entidade são validadas pelo schema, verificadas contra as entidades e evidências existentes e persistidas como eventos append-only. `merge` e `redirect` aprovados passam por detecção de conflitos. Similaridade lexical nunca gera decisão automática.

## Auditoria, relatório e recuperação

A auditoria percorre o ledger desde o início e produz violações com código e severidade. O exportador converte o resultado para `integrity_report.schema.json`, calcula o estado geral e preserva o número de registros verificados.

A recuperação automática só é permitida quando o defeito está restrito à última linha. Antes do corte, o arquivo original é preservado com extensão `.bak`. Falhas no meio do ledger permanecem bloqueadas para análise humana.

## Índices derivados

Os índices não são fonte primária. Podem ser materializados em JSON para acelerar consultas, acompanhados pelo hash SHA-256 do ledger. A verificação compara o snapshot armazenado com uma reconstrução atual; qualquer alteração posterior no ledger invalida o índice antigo.

## Critérios de aceite da Fase 1

| Critério | Situação |
|---|---|
| IDs estáveis e versões imutáveis | implementado |
| validação integral dos contratos | implementado |
| persistência append-only | implementado |
| proveniência e evidências vinculadas | implementado |
| integridade referencial | implementado |
| cadeia histórica de versões | implementado |
| controle cooperativo de escrita | implementado |
| aliases e duplicidades potenciais | implementado |
| decisões de merge/split/redirect | implementado |
| auditoria histórica | implementado |
| relatório conforme schema | implementado |
| recuperação segura de cauda | implementado |
| índices derivados verificáveis | implementado |
| contrato de entrada da Fase 2 | implementado |
| integração com coletores reais | fora do escopo da Fase 1 |
| execução empírica e publicação | fora do escopo da Fase 1 |

## Limites preservados

- não há banco relacional nem transação ACID;
- o lock é cooperativo e local ao sistema de arquivos;
- não há integração com os coletores existentes;
- não há modelos semânticos para resolução automática;
- não há publicação direta de registros;
- testes foram escritos, mas não executados durante esta etapa.

## Encerramento

Do ponto de vista de implementação prevista no roadmap, a Fase 1 está estruturalmente completa e pronta para revisão final do PR. A etapa seguinte é a Fase 2: adaptadores de ingestão e integração controlada da auditoria técnica existente com o núcleo de proveniência.
