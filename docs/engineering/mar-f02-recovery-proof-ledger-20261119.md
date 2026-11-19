# MAR — F02/P0: ledger de recuperação e gate de credencial SQL (19/11/2026)

**Status:** F02 ACTIVE, recuperação operacional **HOLD**, F03–F13 BLOCKED. **Baseline GitHub:** `171f1db97aa68fa2537a5febcf966b3b2c190677`, posterior ao [PR #137](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/137). Este documento distingue **ensaio histórico real**, **teste atual de permissões**, **cópia de branch** e **serviço de backup recorrente**. A prova de um deles não implica aprovação dos demais.

## Evidências positivas históricas — não ignorar nem exagerar

| Executado | Evidência GitHub Actions | O que foi tecnicamente demonstrado | O que NÃO ficou demonstrado |
|---|---|---|---|
| 12/11/2026 | [run #43295473787](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43295473787), jobs `export-encrypted` e `restore-isolated` SUCCESS | Exportação de `mar_p0` da branch de validação, cifragem e passagem entre jobs, `pg_restore` em PostgreSQL local novo com comparação independente de hashes de linhas/esquema | Ciclo recorrente ativo; durabilidade além da retenção do artefato temporário; proteção contra exclusão; credencial SQL atual sem grants DML |
| 13/11/2026 | [run #43494075511](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43494075511), jobs `export-to-private-blob` e `restore-private-blob` SUCCESS | Envio de ciphertext para Vercel Private Blob, leitura autenticada, outro runner recuperou conteúdo em PostgreSQL isolado e verificou os dados | Imutabilidade 90 dias (WORM), backup diário corrente, cópias de idade >= 24h recuperáveis, retenção validada, separação de token RW, store ainda existente/acessível hoje |

**Precisão:** as duas execuções foram efetivamente **sucesso** no GitHub, com passos de exportação e de restauração concluídos; portanto é falso dizer que *nunca* houve recuperação independente. Mas seria igualmente incorreto afirmar que há serviço contínuo recuperável e protegido hoje. A segunda execução foi em branch de PR (não um release de produção).

## Diagnóstico autenticado em 19/11/2026

- [PR #93](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/93) de Vercel Private Blob ainda está **DRAFT**, não integrado à `main`. Seus workflows contêm `schedule` para jobs diários e semanais, mas isso **não comprova que executem na `main`**. Não mesclar ou iniciar crons automaticamente enquanto houver gate aberto.
- O fluxo do PR #93 usa `mar_p0_limited` por nome, tratado como `MAR_P0_READONLY_DATABASE_URL`, porém a inspeção real da branch `br-lingering-smoke-b8hjdnzb` identificou **INSERT nas três tabelas P0 e UPDATE em `checkpoints`**. Nome da role, tipo de URL e sucesso de `pg_dump` **não verificam princípio do menor privilégio**.
- O segundo runner usa também `BLOB_READ_WRITE_TOKEN`, portanto não demonstra segregação de permissão de *delete* no storage. A política do PR #93 já reconhece que não há WORM 90 dias demonstrado.
- Neon root `br-raspy-river-b8qx9oo9` segue `protected=false`; `history_retention_seconds=21600` (6h), sem snapshots listados e sem calendário automático de snapshot confirmado. Retenção de histórico (PITR) **não** é cópia externa imutável.
- A inspeção do projeto Vercel de recuperação encontrou variável `BLOB_STORE_ID`, mas as tentativas de consultar o store pelo identificador conectado, incluindo com o time associado, retornaram **404**. **Não inferir** se foi excluído ou se é problema de escopo/permissões; existência e acesso atuais **não comprovados**.
- A proposta cria jobs de exportação/recuperação separados e exige Environment secrets, mas **não foi possível verificar a configuração atual de Environments e segredos no GitHub** com o conector; o código YAML sozinho não comprova proteção aplicada.

## Teste live SELECT-only: resultado preciso

Foi executada consulta **somente no catálogo PostgreSQL**, autenticada como `mar_p0_limited`, sem recuperar linhas científicas nem expor payloads:

| Branch | SELECT em 3 tabelas | Algum privilégio DML | Papel de backup dedicado | Resultado |
|---|---|---|---|---|
| validação `br-lingering-smoke-b8hjdnzb` | sim | **sim** | não | **HOLD** |
| laboratório `br-purple-art-b8p4uvdr` | sim | não | não, permanece `mar_p0_limited` | **HOLD** |

Na branch de laboratório do PR #137 há `mar_p0_reader` com **NOLOGIN**, somente privilégios de USAGE+SELECT — recurso de ensaio, não a credencial de execução de backup. Seria erro transformar a role antiga, possivelmente um escritor legítimo, em role somente leitura no ambiente original sem verificar consumidores.

## Novo gate executável de defesa antes de exportar

`scripts/mar_f02_readonly_preflight.py`: por padrão **offline HOLD**, sem rede; com `--execute`, executa **apenas SELECT de catálogo** usando credenciais libpq previamente fornecidas pelo operador, sem imprimir senha, DSN, exceção do banco ou dados de tabelas. Rejeita todas as situações abaixo:

- login diferente do novo papel dedicado `mar_p0_backup_reader`; NOLOGIN, `SET ROLE` ou herança implícita;
- poderes administrativos, `CREATE` no banco/`mar_p0`/`public`, associação a owner/`neon_superuser`/`pg_write_all_data`;
- algum DML (`INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `REFERENCES`, `TRIGGER`) nas três tabelas;
- menos/mais de três tabelas do P0, inventário inesperado, ausência de SELECT, respostas malformadas ou falhas de conexão.

**Pré-requisito não realizado:** criar `mar_p0_backup_reader` como credencial efetiva **apenas na branch autorizada** e montar suas grants SELECT-only, sem herdar writer/owner. O código existente do PR #93 que fixa username=`mar_p0_limited` deverá ser **adaptado e testado** antes de qualquer ativação. A nova checagem, ainda que PASS, não é autorização de executar backup de produção ou de publicar dados.

Execução de validação local do código (nenhuma credencial):
```bash
python scripts/mar_f02_readonly_preflight.py
python -m unittest discover -s tests -p 'test_mar_f02_readonly_preflight.py' -v
```
Execução operacional **somente após aprovar a credencial no ambiente de validação**, com conexão libpq já configurada no secret manager (sem DSN no terminal/histórico):
```bash
python scripts/mar_f02_readonly_preflight.py --execute
```
O comando não expõe segredos, mas **não configura** o ambiente nem cria role. Falha com saída curta e código não zero se qualquer garantia faltar.

## Decisões e gates ainda abertos (F02 não pode ser concluída)

1. **P0.1:** credencial dedicada de **login** e segregação explícita writer/reader, com contrato real de execução e falha negativa no Neon isolado. Verificar secret manager e proteção GitHub Environments antes de rodar qualquer workflow.
2. **P0.2:** decidir, sob aceite `owner_only`, entre cópia secundária **WORM** e risco formal de usar Vercel Private Blob como proteção contra exclusão apenas administrativa. Não aceitar silenciosamente proteção inferior de dados importantes.
3. **P0.3:** comprovar acesso **atual** ao store privado e uma execução pós-aprovação de **exportação cifrada → transferência externa → restore independente em runner isolado**, seguida de recuperação histórica de backup de 24–192h, com falhas adversariais.
4. **P0.4:** demonstrar monitoramento, retenção verificável, custódia/rotação da chave AES, procedimento de recuperação quando a credencial falhar, e rollback do processo.
5. **P0.5:** decidir e testar proteção da branch principal; **não** executar migrações, snapshot ou alterações em produção sem avaliação/autorizações específicas.

**Escopo/HOLD:** F02 continua ativa; não alterar root Neon, corpora, valores de secrets, Vercel público, job de publicação ou próxima etapa F03. A assinatura humana do revisor único continua obrigatória para eventual encerramento.
