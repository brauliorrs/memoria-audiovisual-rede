# MAR — F02 / P0: inventário de riscos Neon e ensaio isolado (19/11/2026)

**Etapa exclusiva:** F02 da [fila canônica #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128). **Linha de base GitHub:** `9f8e1059a01ea1ff2aa3fd0b4b31c3a473cc8d54`. **Decisão atual: HOLD — não liberada F03.** Os resultados deste relatório foram observados via integração autenticada do Neon, usando apenas leitura nas branches existentes e alterações de privilégio em uma **nova branch de laboratório**, sem conexão ou escrita em Vercel.

## Escopo, proteção e impacto

F02 exige: segregação operacional das credenciais, prova real de role somente leitura na área de consulta, recuperação em destino separado, verificação da continuidade de dados e esquema, política de histórico/backup/retensão, logs sem segredos, CI positivo e adversarial no commit exato, rollback reproduzível e aceite `owner_only` identificado. Criar branch de laboratório e revogar escrita **somente nela** é um teste técnico parcial. Isso não converte o ambiente principal em seguro, não implanta backup durável nem autoriza usar a função de publicação.

**Sem alteração:** default branch Neon `br-raspy-river-b8qx9oo9`, branch existente `mar-p0-validation-20261021`, corpora, scripts científicos, Streamlit, Next.js, credenciais, Vercel e seus controles de proteção. Não gravar usernames/URLs de conexão, senhas ou payloads de checkpoints em logs ou no GitHub.

## Evidências reais — projeto Neon `holy-bread-70461948`

| Controle | Observação autenticada | Avaliação |
|---|---|---|
| Branch principal | `main`, `br-raspy-river-b8qx9oo9`, marcada como padrão e associada à integração Vercel de produção; `protected=false` | **P0 aberto:** falta proteção confirmada |
| Histórico de recuperação | `history_retention_seconds=21600` (seis horas) | Insuficiente como **única** estratégia de recuperação de longa duração; sem política validada |
| Snapshots | nenhum snapshot listado no projeto; agenda automática `[]` na main | **P0 aberto:** durabilidade e agendamento não demonstrados |
| Roles da main | `neondb_owner`, com poderes administrativos; sem login somente leitura demonstrado ali | Não usar owner em consultas do futuro site/admin |
| Branch de validação | `mar-p0-validation-20261021` (`br-lingering-smoke-b8hjdnzb`) | **P0 aberto:** `mar_p0_limited` NÃO era read-only |
| Grants originais | `mar_p0_limited` possui SELECT e INSERT em `checkpoint_pages`, `checkpoints`, `raw_artifacts`; possui UPDATE em `checkpoints` | **Não é read-only**; esses privilégios podem ser apropriados a um escritor de checkpoints. O uso real desse papel ainda precisa ser confirmado antes de afirmar vulnerabilidade |
| Outras permissões do papel | sem CREATE de schema no banco ou em `public`/`mar_p0`; com CONNECT e TEMP (concedido na base) | Acesso a temporárias **não** equivale a permissão de modificar tabelas científicas |
| Snapshots não-root | tentativa na branch de validação recebeu `not allowed to snapshot non-root branch`; nenhum snapshot foi criado | **HOLD:** não realizar snapshot em main sem aprovação operacional |
| PR de backup existente | [PR #93](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/93) de Private Blob segue DRAFT; política de WORM/imutabilidade e segregação do token RW não comprovadas | Não integrar nem declarar backup externo confiável automaticamente |

## Ensaio isolado de segregação de acesso (executado)

1. Criada a **branch nova** `br-purple-art-b8p4uvdr` / `mar-f02-privilege-and-restore-lab-20261119`, **filha somente** da branch de validação `br-lingering-smoke-b8hjdnzb`. A branch default de produção não foi a origem direta do ensaio.
2. Confirmada cópia dos três conjuntos: `checkpoints=4`, `checkpoint_pages=8`, `raw_artifacts=4`. Comparados, entre origem e filho, três digests MD5 obtidos por agregação determinística de registros `jsonb` ordenados; **todos iguais**. Digest aqui mede equivalência da cópia, não certifica segurança criptográfica de backup.
3. Executado **apenas na branch nova**, com owner do laboratório:

   `REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA mar_p0 FROM mar_p0_limited;`

4. Consultado o catálogo de privilégios da branch de ensaio: nas três tabelas, **SELECT=true** e **INSERT/UPDATE/DELETE/TRUNCATE=false**. O mesmo catálogo, na branch de validação original, ainda mostra os grants de escrita — a alteração **não** foi aplicada retroativamente.
5. Consulta usando autenticação real como `mar_p0_limited` sobre `mar_p0.checkpoints` funcionou, retornando exclusivamente `current_user` e contagem de quatro linhas. A sessão mostrou `transaction_read_only=off`: é a **ACL de tabelas** que impede DML nelas; não declarar que a transação é globalmente read-only.

6. Criado **apenas no laboratório** um papel independente `mar_p0_reader` com `NOLOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION`. Concedidos somente `USAGE` no schema `mar_p0` e `SELECT` nas três tabelas. Consulta ao catálogo PostgreSQL confirmou `rolcanlogin=false`, `rolsuper=false`, `rolcreatedb=false`, `rolcreaterole=false`, `all_select=true`, `any_dml=false`. O papel é **NOLOGIN de propósito**: não existe senha, login de aplicação ou consumidor provisionado; esses passos só poderão ocorrer sob gates próprios.
7. **Distinção importante:** o revogue sobre `mar_p0_limited` foi um ensaio de ACL na cópia. Se esse papel original foi concebido para gravar checkpoints, reproduzir a revogação em produção quebraria ingestão legítima. A implementação recomendada separa **writer mínimo** e **reader dedicado**, em vez de transformar automaticamente o escritor em leitor.

**Limite decisivo:** a criação de uma branch derivada verifica clonagem isolada e integridade comparada, **não constitui restauração independente de backup externo**. Não houve recuperação de snapshot, `pg_restore` em segundo executor, teste de ACL de storage, recuperação após exclusão, rotação de chaves nem prova de retenção de 30/90 dias. A F02 continua HOLD.

## Ensaio de LOGIN realmente dedicado — concluído somente no laboratório

Em 19/11/2026, foi criada, usando o conector oficial Neon e **somente** na branch `br-purple-art-b8p4uvdr`, a role LOGIN `mar_p0_backup_reader`, com `access=read_only`, `database=neondb` e `schemas=[mar_p0]`. O provedor devolveu senha gerada, que **não foi publicada, exibida nem registrada em código ou relatório**. A role foi ajustada com `ALTER ROLE mar_p0_backup_reader NOINHERIT` **no laboratório**. Uma credencial de uso operacional futuro precisará ser provisionada ou rotacionada no seu próprio secret manager.

O pré-teste SQL real, autenticado sob esse papel, confirmou: LOGIN ativo, `current_user=session_user`, ausência de memberships, administração, CREATE, ownership nas três tabelas, execução `SECURITY DEFINER` do schema e DML de tabela/coluna. `SELECT` está permitido nas três tabelas e encontrou 4 checkpoints.

Foram executados ensaios **sem mutação de dados** com `EXPLAIN INSERT`, `EXPLAIN UPDATE` e `EXPLAIN DELETE`; o PostgreSQL negou a permissão de cada um. A execução não acionou esses comandos DML, apenas verificou se o plano seria autorizado.

**Resultado do subgate de laboratório:** privilégio mínimo do LOGIN de backup **comprovado nessa branch isolada**. **NÃO comprovado**: acesso por uma URL de aplicação real, GitHub Environment/Secret configurado, backup atual usando essa credencial ou concessão equivalente no banco principal. F02 permanece `active`, sem encerramento nem autorização pública.

## Revalidação do armazenamento Vercel

No projeto `mar-p0-recovery-lab`, `BLOB_STORE_ID` está presente nos metadados de Environment. Entretanto, consultas à API para recuperar o store pelo identificador retornaram **HTTP 404 tanto no escopo da conta quanto do time**. Isso **não distingue recurso inexistente de recurso inacessível por permissão/escopo**. Não houve upload, download, criação de novo store ou remoção de conteúdo. A prova histórica de restauração de 13/11/2026 não é prova de acesso hoje e não equivale a retenção imutável.

**Gates seguintes:** verificar conta/team/integration correta ou reconfigurar armazenamento privado sob autorização do proprietário, sem expor tokens; comprovar retenção e custódia da chave; conectar o novo login dedicado em Environments protegidos de execução; só depois realizar backup cifrado e restauração independente de cópia atual e histórica.

## Como reproduzir a verificação sem vazar dados

Executar **somente consultas SELECT**, primeiro na branch de validação e depois na branch de ensaio, sem imprimir payloads:

```sql
SELECT c.relname,
       has_table_privilege('mar_p0_limited', c.oid, 'SELECT') AS can_select,
       has_table_privilege('mar_p0_limited', c.oid, 'INSERT') AS can_insert,
       has_table_privilege('mar_p0_limited', c.oid, 'UPDATE') AS can_update,
       has_table_privilege('mar_p0_limited', c.oid, 'DELETE') AS can_delete
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'mar_p0' AND c.relkind IN ('r','p')
ORDER BY c.relname;
```

A consulta produz prova de privilégios atuais; o relatório [JSON de baseline](mar-f02-p0-neon-evidence-20261119.json) é uma **fotografia datada**, não o estado atual garantido do Neon. O workflow CI verifica somente a **honestidade e consistência do relatório**, sem acesso aos segredos do banco. Testes adversariais rejeitam falsa conclusão de backup, restauração, proteção da branch e declaração de ausência de privilégios quando eles existem.

## Gates F02 — próximos trabalhos, em ordem

1. **P0.1 — Revisão de segurança e credenciais:** decidir, sob controle `owner_only`, esquema de identidades e autorizações. Criar LOGIN específico com grants SELECT estritos, provar bloqueio efetivo de INSERT/UPDATE/DELETE e impossibilidade de obter privilégios de owner; validar a segregação no contexto do consumidor, não confiar no nome da role. **Nenhuma mudança em main sem aceite da decisão de segurança**.
2. **P0.2 — Backup e retenção:** escolher armazenamento privado recuperável com política efetiva de ACL, custódia/rotação de chave e retenção; decidir o destino do PR #93 perante risco de imutabilidade WORM. A retenção histórica de seis horas não é prova de 30 ou 90 dias de backup.
3. **P0.3 — Recuperação isolada independente:** gerar cópia autenticada da origem autorizada, restaurar em branch/ambiente distinto e comparar tabelas, esquema, digests e limites de autorização; ensaiar falha de senha, arquivo adulterado, ausência de backup e rollback. Não executar `finalize restore` nem fazer swap da branch principal.
4. **P0.4 — CI, revisão e fechamento:** ensaios positivos/negativos no SHA exato, relatório sem segredos, documentação de risco residual e `ACCEPTED` expresso do proprietário na issue #128; só então alterar F02 para `completed` e liberar F03.

**Política:** qualquer indisponibilidade de storage/credenciais ou falta de teste externo mantém a F02 em HOLD operacional; não criar senha fictícia, não assumir backup semanal funcionando, não abrir o Vercel e não ativar automações de corpus.
