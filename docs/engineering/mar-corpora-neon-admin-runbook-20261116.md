# MAR — PostgreSQL/Neon + painel de gestão: implantação controlada

## Estado comprovado do laboratório, 16/11/2026

Projeto Neon `holy-bread-70461948` (MAR). Branch de laboratório criada explicitamente para este trabalho: `mar-corpora-admin-schema-lab-20261116`, ID `br-small-rain-b8olypnn`, descendente do ambiente isolado `mar-p0-validation-20261021`, **não da branch principal de produção**. Migrations `20261116_mar_corpora_audit_v1.sql` e `20261116_mar_corpora_attestation_guard_v1.sql` executadas com sucesso neste laboratório.

O laboratório possui cinco conectores e cinco eventos iniciais de cadastro. Um teste negativo identificou que o owner Neon pertence administrativamente à role de atestação, porém sem herança de uso. O controle baseado apenas em membership permitiu um evento sintético de teste (#6); ele foi corrigido para exigir `pg_has_role(..., 'USAGE')` e o teste repetido foi rejeitado (SQLSTATE P0001). Como o ledger é append-only, preservamos esse evento sintético para auditoria e adicionamos um HOLD corretivo (#8). Existem agora sete eventos no laboratório, com Eye em HOLD. Todos os corpora mantêm `publication_authorized=false` e `scientific_validation_proven_by_database=false`. Credenciais não foram recuperadas, copiadas ou registradas no código. Não houve migração nem inserção na branch principal Neon.

## Arquitetura e invariantes

- `corpus_admission_engine.REGISTRY` permanece **contrato revisado em código**, não é modificado por usuários do banco; o hash SHA-256 de cada `ConnectorSpec` deve corresponder ao espelho `mar_corpora.connector_registry`. Divergência aborta sincronização, sem `UPDATE`.
- `audit_events` aceita somente INSERT em ordem crescente. Triggers bloqueiam UPDATE/DELETE/TRUNCATE; papel leitor só SELECT, ingester somente SELECT+INSERT; papel adicional `mar_corpora_attestor` NOLOGIN, sem permissão herdada para a conta owner, é exigido para estados avançados. Timestamp e `actor_ref` de novos eventos são atribuídos pelo PostgreSQL com `current_user` e `clock_timestamp()`, não pelo cliente.
- Esse ledger **não é WORM inviolável**: proprietário do banco pode remover permissões e triggers. É uma trilha administrativa para rastreamento; aprovação científica e publicação dependem de documentação externa, revisão independente em PR e gates do PR #95.
- A única API de escrita entregue ao operador aceita `registered` (espelho idempotente), `probed`, `HOLD` ou `note`; não permite marcar `curator_reviewed`, `evidence_validated`, `admission_ready` ou `published` com um comando comum.
- O painel é um entry point **interno e separado**: `admin/corpora_dashboard.py`. Não foi adicionado ao menu público nem habilitado automaticamente. Uso de OIDC `st.user`, `email_verified=true` e `MAR_ADMIN_EMAIL_ALLOWLIST` configurado exclusivamente no servidor. **Sem autenticação, o painel não consulta o banco**. A conexão exige a role `mar_corpora_reader` e nenhuma permissão INSERT/UPDATE/DELETE.
- As fontes legadas, `neon_auth.*`, `mar_p0.*`, workflows, streams, coletores e mídias não são alterados.

## Migração e credenciais futuras

Revisar o PR, testes, política P0 e plano de restauração antes de executar em produção. Aplicar as duas migrações SQL em ordem, usando conexão direta **em janela aprovada**, não a URL pooled ou do app público. Conceder `mar_corpora_reader` a uma conta LOGIN exclusivamente para o painel privado e `mar_corpora_ingester` a uma conta diferente, exclusivamente para operações manuais. A role `mar_corpora_attestor` não recebe herança de acesso por contas de serviço até processo de autorização de revisores independentes. Não usar a conta owner para nenhuma URL de aplicação.

Variáveis exclusivas do runtime privado:
- `MAR_CORPORA_READONLY_DATABASE_URL`: conexão Neon com credencial realmente SELECT-only.
- `MAR_CORPORA_INGESTER_DATABASE_URL`: conexão de inserção auditada para scripts manuais (nunca configurá-la no painel).
- `MAR_ADMIN_EMAIL_ALLOWLIST`: lista de e-mails OIDC verificados, mantida fora de Git.
- Segredos OIDC conforme configuração oficial do Streamlit (cookie secret, client id/secret e discovery metadata), **também apenas no servidor**.

Dependências separadas: `pip install -r requirements-admin.txt`. Não publicar a aplicação em hospedagem pública sem autenticação OIDC ativa.

### Execução manual após provisionamento de conta ingester

```bash
python -m scripts.sync_mar_corpora_registry --apply
python -m scripts.record_mar_corpus_observation eye probed --evidence-sha256 SHA256_REAL \
  --evidence-ref https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/NUMERO_REAL \
  --note "Sonda pública limitada auditada" --apply
streamlit run admin/corpora_dashboard.py
```

O exemplo de sonda **não deve ser executado com hashes fictícios**; usar evidência e execução reais auditadas. Em um primeiro ambiente sem credentials, comandos devem retornar HOLD. Nenhuma publicação é realizada pelo comando.

## Gates de liberação

1. Testes unitários + CI no HEAD do PR e revisão independente (ruleset da `main`).
2. Validar leitura e segregação de contas LOGIN no laboratório, incluindo tentativa de acesso à view com credencial SELECT-only; os papéis criados neste incremento ainda são NOLOGIN e **nenhuma conta de aplicação foi provisionada**.
3. Validar login OIDC de administrador com e-mail verificado e bloqueio de usuários não listados em implantação interna; **não afirmar deploy já validado**.
4. Segurança P0, recuperação e plano de reversão aprovados antes de migrar Neon principal.
5. PR #95 de admissão continua gate independente; nenhum evento administrativo publica fichas.

Reversão: não excluir nenhuma branch ou dados sem aprovação específica. Para código, reverter este PR. Para schema isolado, descartar branch de laboratório somente após validação, autorização e backup aplicável. Em produção, preferir rollback aditivo/desabilitar acesso administrativo a apagar o histórico.


## Homologação complementar — 17/11/2026, branch isolada

**Credencial LOGIN criada no laboratório:** `mar_corpora_dashboard_lab` no Neon `br-small-rain-b8olypnn`, acesso `read_only` limitado ao database `neondb` e schema `mar_corpora`. Senha retornada pelo provedor apenas no ato da criação, não armazenada no repositório nem exibida em relatórios. Em produção será necessária outra credencial independente, criada após gate P0.

**Validação feita por login real, não apenas `SET ROLE`:** usando o argumento `role_name=mar_corpora_dashboard_lab` em consultas de banco e `current_user` conferido, foram verdadeiros os **13 controles** da função `read_only_role_assertion`: USAGE do schema administrativo, ausência de CREATE, SELECT nas duas tabelas e view, ausência de INSERT/UPDATE/DELETE nas tabelas e ausência de USAGE nos schemas `neon_auth` e `mar_p0`. Tentativas reais de INSERT no ledger e SELECT em `neon_auth.user` falharam com SQLSTATE `42501`. A função da aplicação foi corrigida para testar os privilégios efetivos em vez de exigir participação no grupo `mar_corpora_reader`, que não é concedida automaticamente a LOGIN criado pelo Neon como `read_only` de schema. 

**Segurança OIDC da aplicação:** `authorized_admin` continua exigindo `is_logged_in=true`, `email_verified=true` e lista de e-mails no servidor. Foi acrescentado o bloqueio para `exp` ausente ou vencido, pois a biblioteca Streamlit não revoga automaticamente a sessão quando o ID-token expira (o cookie pode durar mais). Instalar `Authlib` via `requirements-admin.txt`. O login OIDC real e o deploy **não foram executados**, porque o cliente de identidade, a URL HTTPS privada e os usuários aprovados ainda não foram fornecidos/configurados. Sem esses dados, a página deve bloquear consultas.

### Preparação do OIDC para homologação privada (não inserir segredos no Git)

Criar um aplicativo OIDC com provedor institucional autorizado, com retorno exato `https://DOMINIO-INTERNO/oauth2callback`. Configurar as variáveis `MAR_ADMIN_EMAIL_ALLOWLIST` (e-mail verificado de cada administrador) e `MAR_CORPORA_READONLY_DATABASE_URL` (LOGIN no **laboratório** durante testes). No secret manager do runtime Streamlit configurar `[auth]`: `redirect_uri`, `cookie_secret`, `client_id`, `client_secret`, `server_metadata_url`. A URL de produção não deve compartilhar a senha, o token ou a conexão com a branch de laboratório. Recomenda-se acesso privado com proteção de rede/reverse-proxy além do gate no Streamlit.

Testar presencialmente ou no navegador autorizado: (1) anônimo bloqueado antes de executar SQL; (2) conta não autorizada bloqueada; (3) e-mail não verificado bloqueado; (4) ID-token expirado bloqueado; (5) conta explicitamente autorizada consegue consultar apenas as 5 fontes; (6) falha ou expiração do banco não revela segredos. Registrar logs com data, ator e resultado, sem credenciais. Somente depois o painel pode passar de HOLD de implantação para candidato a implantação interna.

A aprovação independente do GitHub é diferente do login do painel: PRs #95 e #98 foram marcados *ready for review* em 17/11/2026 após CI aprovado, mas ainda aguardam revisor distinto do autor. Este laboratório **não autoriza** qualquer merge ou migração da branch Neon main.
