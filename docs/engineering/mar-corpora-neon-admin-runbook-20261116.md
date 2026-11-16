# MAR — PostgreSQL/Neon + painel de gestão: implantação controlada

## Estado comprovado do laboratório, 16/11/2026

Projeto Neon `holy-bread-70461948` (MAR). Branch de laboratório criada explicitamente para este trabalho: `mar-corpora-admin-schema-lab-20261116`, ID `br-small-rain-b8olypnn`, descendente do ambiente isolado `mar-p0-validation-20261021`, **não da branch principal de produção**. Migrations `20261116_mar_corpora_audit_v1.sql` e `20261116_mar_corpora_attestation_guard_v1.sql` executadas com sucesso neste laboratório.

O laboratório possui cinco conectores mirrorizados e cinco eventos de cadastro; `publication_authorized=false` e `scientific_validation_proven_by_database=false` para cada um. Credenciais não foram recuperadas, copiadas ou registradas no código. Não houve migração nem inserção na branch principal Neon.

## Arquitetura e invariantes

- `corpus_admission_engine.REGISTRY` permanece **contrato revisado em código**, não é modificado por usuários do banco; o hash SHA-256 de cada `ConnectorSpec` deve corresponder ao espelho `mar_corpora.connector_registry`. Divergência aborta sincronização, sem `UPDATE`.
- `audit_events` aceita somente INSERT em ordem crescente. Triggers bloqueiam UPDATE/DELETE/TRUNCATE; papel leitor só SELECT, ingester somente SELECT+INSERT; papel adicional `mar_corpora_attestor` NOLOGIN, sem membro, é exigido para estados avançados. Timestamp e `actor_ref` de novos eventos são atribuídos pelo PostgreSQL com `current_user` e `clock_timestamp()`, não pelo cliente.
- Esse ledger **não é WORM inviolável**: proprietário do banco pode remover permissões e triggers. É uma trilha administrativa para rastreamento; aprovação científica e publicação dependem de documentação externa, revisão independente em PR e gates do PR #95.
- A única API de escrita entregue ao operador aceita `registered` (espelho idempotente), `probed`, `HOLD` ou `note`; não permite marcar `curator_reviewed`, `evidence_validated`, `admission_ready` ou `published` com um comando comum.
- O painel é um entry point **interno e separado**: `admin/corpora_dashboard.py`. Não foi adicionado ao menu público nem habilitado automaticamente. Uso de OIDC `st.user`, `email_verified=true` e `MAR_ADMIN_EMAIL_ALLOWLIST` configurado exclusivamente no servidor. **Sem autenticação, o painel não consulta o banco**. A conexão exige a role `mar_corpora_reader` e nenhuma permissão INSERT/UPDATE/DELETE.
- As fontes legadas, `neon_auth.*`, `mar_p0.*`, workflows, streams, coletores e mídias não são alterados.

## Migração e credenciais futuras

Revisar o PR, testes, política P0 e plano de restauração antes de executar em produção. Aplicar as duas migrações SQL em ordem, usando conexão direta **em janela aprovada**, não a URL pooled ou do app público. Conceder `mar_corpora_reader` a uma conta LOGIN exclusivamente para o painel privado e `mar_corpora_ingester` a uma conta diferente, exclusivamente para operações manuais. A role `mar_corpora_attestor` fica sem membros até processo de autorização de revisores independentes. Não usar a conta owner para nenhuma URL de aplicação.

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
