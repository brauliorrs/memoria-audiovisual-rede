# MAR — Prova de recuperação integral do esquema mar_p0 no Neon

**Data:** 12/11/2026 (14:19 UTC, branch criada). **Tipo:** prova **real** de recuperação isolada via ramificação no mesmo projeto Neon, **não** teste de backup/exportação offsite. **Escopo exato:** três tabelas do esquema `mar_p0` da branch de validação P0 (não o catálogo completo Czech TV, a branch `main` ou todos os bancos do projeto).

## 1. Origem, destino e impacto

- Serviço existente: Neon/PostgreSQL 18 `neon-erin-field`, projeto `holy-bread-70461948`, região `aws-us-east-1`.
- **Origem imutável no ensaio:** branch `mar-p0-validation-20261021` (`br-lingering-smoke-b8hjdnzb`).
- **Destino novo, isolado:** branch `mar-p0-recovery-proof-20261112` (`br-silent-butterfly-b80zepbt`), criada com `parent_id=br-lingering-smoke-b8hjdnzb` e `parent_lsn=0/1E4CD90`; estado final `ready`.
- Nenhum SQL de escrita executado em origem, destino ou `main`. Nenhuma alteração de aplicação, migração, coleta, vídeo, cursor, workflow ou schema. A criação da branch foi a única mutação remota do ensaio.
- A branch anterior `mar-p0-recovery-20261021` (**1/2/2**) não foi alterada. Ela não tem o mesmo conjunto que a origem (**4/8/4**) e não deve ser apresentada como restauração atual.
- Tentativa anterior de snapshot sobre a branch de validação recusada pelo Neon com HTTP 400 `not allowed to snapshot non-root branch`; nenhum snapshot criado. A tentativa de criar a branch com `suspend_timeout_seconds=60` também foi recusada por política da conta. A criação efetiva ocorreu **sem personalização de suspensão**, portanto com o compute padrão permitido pela conta.

## 2. Protocolo reproduzível, somente leitura

Para cada uma das três tabelas, a prova calculou na origem **e** no destino, no próprio PostgreSQL:
- contagem exata de linhas;
- hash **SHA-256** de uma concatenação determinística do `to_jsonb(t)::text` de **todas as linhas completas**, com `ORDER BY` da chave primária (incluindo `bytea`, timestamps, status e todas as demais colunas), separado por `E'\\n'`;
- consultas independentes de SHA-256 dos `manifest` e `payload` armazenados; referências FK órfãs e flags de admissão proibidas;
- hash SHA-256 da definição ordenada de **colunas, constraints e índices** via `information_schema.columns`, `pg_constraint`, `pg_get_constraintdef` e `pg_get_indexdef`;
- inventário no catálogo PostgreSQL de tabelas, views, sequences, stored routines, triggers de usuário e RLS.

O SQL de fingerprint de cada tabela seguiu este padrão (variando a tabela e a chave primária):

```sql
SELECT count(*)::int AS n,
 encode(sha256(convert_to(
  coalesce(string_agg(to_jsonb(t)::text, E'\n' ORDER BY t.run_key), ''),
  'UTF8'
 )), 'hex') AS fingerprint
FROM mar_p0.checkpoints t;
```

Para `checkpoint_pages` a ordenação foi `t.run_key,t.sequence`; para `raw_artifacts`, `t.sha256`.

## 3. Evidência comparativa: origens e restauração

| Recurso | Origem | Destino | Estado |
| --- | ---: | ---: | --- |
| `mar_p0.checkpoints` | 4 | 4 | IGUAL |
| `mar_p0.checkpoint_pages` | 8 | 8 | IGUAL |
| `mar_p0.raw_artifacts` | 4 | 4 | IGUAL |
| Total de linhas `mar_p0` | **16** | **16** | IGUAL |
| SHA-256 dos dados completos de cada tabela | idêntico | idêntico | PASS |
| Definições de colunas/constraints/índices | 69 | 69 | PASS |
| SHA-256 dessas 69 definições | idêntico | idêntico | PASS |
| Invalidade de SHA dos manifestos e artefatos | 0 | 0 | PASS |
| Referências órfãs FK | 0 | 0 | PASS |
| Flags `promotion_authorized` / `media_downloaded` verdadeiras | 0 | 0 | PASS |
| Soma de bytes de manifestos `bytea` | 4.213 | 4.213 | PASS |
| Soma de bytes de `raw_artifacts.payload` | 859 | 859 | PASS |

**Hashes SHA-256 observados em AMBAS as branches** (somente digests, sem expor payloads):

```text
checkpoints      3b1916b2759e2b93175fc67f2377e15425f999c8756f1fd3efaf36bf6fbe1dc9
checkpoint_pages f5f57f3492b9b2d0ab985b1a520046b3a6fceb49fa101c6e22036cac8b801b11
raw_artifacts    0fa8d1b661fa52b4a3baa5fa0b72b79d1e9b996cc0deef165752f2df0cb591da
schema           066bedfeae61f56acf6ee7b47e3dd6d1d613241743b4e167e3b40d1b185fb404
```

Ambos os ambientes apresentam **3 tabelas comuns** em `mar_p0` e 0 views, 0 sequences, 0 funções/procedures próprios, 0 triggers de usuário, 0 políticas RLS. Não foi feita avaliação de papéis/globais de usuário, disponibilidade multi-região ou objetos de outros esquemas.

## 4. Veredito e limites

**PASS — recuperação integral do escopo `mar_p0` no MESMO serviço Neon:** a nova branch reproduziu exatamente as 16 linhas de três tabelas e as 69 definições catalogadas. Esse teste confirma que o estado armazenado e suas relações podem ser recuperados em outra branch sem tocar na origem. A branch `mar-p0-recovery-proof-20261112` foi preservada para conferência do operador e pode implicar consumo de quota até remoção autorizada.

**HOLD — P0 de continuidade fora do Neon:** branching copia o estado do mesmo serviço e não demonstra recuperação de indisponibilidade de todo o Neon, perda de conta, falha de uma região ou corrupção replicada. Sem snapshot na branch não-raiz, sem exportação autenticada `pg_dump`, sem cópia externa comprovada e sem `pg_restore` em ambiente independente. Backups/snapshots agendados anteriormente consultados estavam vazios; a janela de histórico configurada é de seis horas.

**HOLD — completude Czech TV:** integridade e recuperação de checkpoints não atestam origem institucional de bytes, universo do catálogo ou terminalidade oficial de paginação. O contrato de pesquisa mantém `production_gate=HOLD`.

**Próxima prova distinta:** exportar `mar_p0` de forma controlada, cifrar o dump, guardar cópia independente e restaurar em outro ambiente; comparar novamente os mesmos hashes e constraints sem exportar segredos/logs. Não apagar a branch de prova nem alterar a `main` sem decisão explícita.
