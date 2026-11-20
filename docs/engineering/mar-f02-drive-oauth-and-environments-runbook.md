# MAR F02 — Preparação de credenciais para backup criptografado no Google Drive pessoal

**Situação:** etapa F02 ACTIVE/HOLD, mesmo após o aceite explícito do risco não-WORM em 19/11/2026. Este manual não executa OAuth automaticamente, não ativa o cron, não dá acesso público ao site e não modifica a branch Neon main.

## Comprovado no Neon (somente validação)

- Projeto Neon: `holy-bread-70461948`; origem: branch de **validação** `br-lingering-smoke-b8hjdnzb`, database `neondb`, schema `mar_p0`.
- Role criada: `mar_p0_backup_reader`, com access `read_only` restrito a `mar_p0`; `NOINHERIT`.
- SQL do preflight foi executado **autenticado como essa role** e passou 21 verificações: `SELECT` nos três objetos esperados, zero DML, zero privilégios administrativos, zero grants fora de escopo e nenhuma membership. 4 checkpoints, 8 páginas e 4 artefatos estavam presentes na inspeção de inventário. A branch principal foi preservada.
- **Pendente:** a credencial de conexão ainda não foi instalada em um GitHub Environment. Rotacionar a senha dessa role **pela interface segura do Neon**, gerar/copiar o DSN da mesma branch, role e database e colocá-lo diretamente no Secret `MAR_P0_READONLY_DATABASE_URL` do ambiente de exportação. Não enviar DSN, senha ou chave AES a chat/Drive/repositório/log.

## 1. Autorizar o Google Drive sem conceder acesso amplo

1. No [Google Cloud Console](https://console.cloud.google.com/), criar ou selecionar um projeto OAuth sob a **mesma conta Google pessoal** do Drive já escolhido. Habilitar a **Google Drive API**.
2. Configurar a tela de consentimento Google Auth Platform para o proprietário da conta, habilitando somente o escopo `https://www.googleapis.com/auth/drive.file`. Criar cliente **Desktop app** e baixar o arquivo de credenciais OAuth apenas para o próprio computador. Seguir as exigências de publicação/verificação do Google antes de confiar em refresh tokens para cron permanente; clientes em modo de teste podem ter tokens de curta duração.
3. Em um computador de confiança com navegador e Python 3.11+, executar a preparação **local**, nunca no GitHub Actions público. Guardar o JSON do Google e o resultado somente numa pasta privada fora do repositório, protegida contra outros usuários locais:

```bash
python -m pip install 'google-auth-oauthlib>=1.2,<2' 'google-api-python-client>=2.187,<3' 'google-auth>=2.43,<3' 'cryptography>=50,<51'
mkdir -p "$HOME/.config/mar-f02/segredos"
chmod 700 "$HOME/.config/mar-f02/segredos"
# Copie o JSON Desktop para ~/.config/mar-f02/segredos/cliente-google.json
chmod 600 "$HOME/.config/mar-f02/segredos/cliente-google.json"
# Exporte previamente MAR_P0_GOOGLE_DRIVE_FOLDER_ID APENAS no terminal local,
# se a pasta originalmente selecionada foi compartilhada com o aplicativo via Picker.
python -m scripts.mar_f02_drive_oauth_bootstrap \
  --client-json "$HOME/.config/mar-f02/segredos/cliente-google.json" \
  --output "$HOME/.config/mar-f02/segredos/mar-f02-github-secrets.json" \
  --execute
```

4. O escopo `drive.file` **não oferece acesso automático** a uma pasta criada pelo conector ChatGPT: a pasta original precisa ser autorizada ao aplicativo pelo **Google Picker** (fluxo do próprio cliente). O script **recusará** essa pasta caso não consiga verificá-la como privada e acessível. Não ampliar silenciosamente o OAuth para `drive`.
5. **Alternativa expressa do operador, mantendo exclusivamente o mesmo Drive pessoal:** criar uma pasta **privada e nova, propriedade do aplicativo**, ao autorizar o OAuth. Para isso, omitir a variável de pasta `MAR_P0_GOOGLE_DRIVE_FOLDER_ID` e adicionar `--create-app-folder` à execução acima. O aplicativo cria a pasta `MAR - Backup Neon Criptografado (app)` no Drive do proprietário e confere seus metadados. O ID dessa **nova pasta** é salvo apenas no JSON local privado. Não confundir a pasta antiga, vazia, com destino homologado.
6. Após autenticar, o script só imprime o status de sucesso; **nunca** imprime Client Secret, refresh token ou ID da pasta. Se houver erro, o resultado é `HOLD` e nenhum Secret é instalado automaticamente. O JSON privado criado tem permissão exclusiva `0600` e caminho fora do repositório; instale os Secrets e, depois, retire o arquivo do dispositivo conforme a política local de custódia (atenção a backups automáticos do próprio sistema).

Referências técnicas: [OAuth Drive file](https://developers.google.com/workspace/drive/api/guides/api-specific-auth), [Google Picker](https://developers.google.com/workspace/drive/picker/guides/web-picker), [OAuth offline access](https://developers.google.com/identity/protocols/oauth2/web-server).

## 2. GitHub: criar ambientes protegidos e configurar Secrets diretamente na interface

Acessar **Settings → Environments** do repositório `brauliorrs/memoria-audiovisual-rede` e configurar os dois ambientes `mar-p0-drive-export` e `mar-p0-drive-recovery`, com política de branch restrita à `main`. Limitar os revisores e decisões de aprovação conforme a capacidade real de operação (um ambiente com revisão manual exigirá aprovação em cada execução, inclusive agendamentos).

| Secret | Exportação | Recuperação |
| --- | --- | --- |
| `MAR_P0_DRIVE_OAUTH_CLIENT_ID` | Sim | Sim |
| `MAR_P0_DRIVE_OAUTH_CLIENT_SECRET` | Sim | Sim |
| `MAR_P0_DRIVE_OAUTH_REFRESH_TOKEN` | Sim | Sim |
| `MAR_P0_GOOGLE_DRIVE_FOLDER_ID` | Sim | Sim |
| `MAR_P0_RESTORE_AES_KEY_HEX` | Sim | Sim |
| `MAR_P0_READONLY_DATABASE_URL` | **Somente exportação** | **Não** |

A chave AES deve ser uma chave aleatória de 32 bytes (64 caracteres hexadecimais), gerada em ambiente seguro e conservada no gerenciador de senhas. **A mesma chave** é necessária para o runner de recuperação, mas nunca deve ser incluída no Drive, na documentação ou em logs. O ambiente de recuperação **não** deve receber DSN de origem Neon. Os Secret devem ser cadastrados diretamente na interface do GitHub — a conexão deste chat não os instala.

Referência: [GitHub Environments / Secrets](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

## 3. Homologação manual sem ativar cron

A `main` contém dois workflows. Eles são **fail-closed** quando as variáveis abaixo estão ausentes:

| Variável GitHub Actions | Finalidade | Estado até homologação |
| --- | --- | --- |
| `MAR_P0_GOOGLE_DRIVE_BACKUP_TEST_ENABLED` | Autoriza **somente** disparos manuais (workflow_dispatch), com Secrets disponíveis | Ausente até revisão, depois `true` para teste acompanhado |
| `MAR_P0_GOOGLE_DRIVE_BACKUP_ENABLED` | Autoriza o cron diário e o teste semanal agendado | **Não configurar** antes da homologação |

Com Environments e Secrets instalados, usar **Actions → MAR F02 Drive encrypted backup and isolated restore → Run workflow** na `main`, depois de autorizar temporariamente apenas a variável **TEST**. Conferir a conclusão dos jobs **export** e **isolated-restore** em runners separados: snapshot cifrado gerado a partir de Neon validação, SHA de readback idêntico e prova de `pg_restore` no PostgreSQL local isolado. Não publicar conteúdo, tokens ou hashes de senha.

Após mais de 24h, usar **Actions → MAR F02 verify an older encrypted Drive backup → Run workflow**, ainda com apenas a variável **TEST**; confirmar que cópia antiga foi recuperada, autenticada e restaurada. A variável de produção e o cron diário só poderão ser ligados **após** registrar provas da restauração, custódia de Secrets, quota, política de retenção e aceite operacional final na issue #128.

**Regra de falha:** qualquer erro de OAuth, acesso à pasta, grant SQL, SHA, AES-GCM, resto de hash ou integridade implica `HOLD`. Não contornar falhas alargando escopo OAuth nem reutilizar a role escritora `mar_p0_limited`.

## 4. Estado e revogação

No estado atual: reader validada no Neon **validação**; acesso OAuth do runner e Secret ainda não homologados; pasta Drive sem backup real recuperável; rotina desligada; root Neon e site privado preservados. O risco não-WORM foi aceito pelo proprietário **apenas nesta fase preliminar**.

Para parar a operação, remover/definir `false` para ambas as variáveis de ativação, revogar ou rotacionar OAuth e credencial de backup por canais protegidos e reter os backups existentes para investigação. Para evoluir à produção, reavaliar WORM e opções de retenção fora do alcance deste aceite preliminar.
