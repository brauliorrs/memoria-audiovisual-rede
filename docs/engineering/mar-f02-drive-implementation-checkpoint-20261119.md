# MAR F02 — Implementação executável Drive-only / checkpoint 19-11-2026

**Etapa:** F02 ACTIVE/HOLD, F03–F13 BLOCKED. **PR:** #142, DRAFT. **Fonte:** somente branch Neon VALIDATION, esquema `mar_p0`. **Destino:** Google Drive pessoal, previamente escolhido, com arquivos cifrados. Sem acesso público.

## O que está implementado, mas ainda não ativado

- `scripts/mar_p0_offsite_pg_restore.py`: transportado do laboratório do PR #93 sem integrar a opção Vercel, com teste live de privilégios SQL do `mar_p0_backup_reader` antes do `pg_dump`, AES-256-GCM autenticado e verificação de fingerprints em restauração PostgreSQL isolada.
- `scripts/mar_p0_offsite_google_drive.py`: OAuth `drive.file` separado do conector ChatGPT, verificação da pasta privada, upload somente de ciphertext, SHA-256 por leitura autenticada, recibo privado e recuperação de cópias antigas por listagem independente.
- `mar-f02-google-drive-backup.yml`: exportação e restore em **dois runners diferentes**, com `MAR_P0_GOOGLE_DRIVE_BACKUP_ENABLED == 'true'`; variável ausente/desligada = jobs skipped; execução em `main` e environments protegidos.
- `mar-f02-google-drive-old-recovery.yml`: semanal, recupera cópia de 24–192h sem criar nova mídia ou ler diretamente a fonte Neon.
- `tests/test_mar_p0_offsite_google_drive.py` e `tests/test_mar_p0_offsite_pg_restore.py`: testes offline de ciphertext, tampering, SHA, não overwrite, idade, escopo de pasta, grants e isolamento. CI valida a revisão exata; um CI verde não demonstra segurança de serviços vivos.

## Operação bloqueada (não confundir com código concluído)

1. Conceder acesso ao diretório privado ao **cliente OAuth de backup independente**, com o escopo `https://www.googleapis.com/auth/drive.file` e sem conceder Drive inteiro; conexão ChatGPT não é reutilizável no CI. Validar upload de vetor teste antes de usar dado real.
2. Provisionar `mar_p0_backup_reader` read-only **na branch de validação**; essa role foi validada somente no LAB. Não modificar Neon root nem reutilizar `mar_p0_limited` (escritor).
3. Configurar Secrets restritos nos Environments `mar-p0-drive-export` e `mar-p0-drive-recovery` (URL da branch de validação, ID de pasta, OAuth Client ID/Secret/Refresh e chave AES), com aprovação e limitação à main. **Não colocar valores de Secret no Git/Drive/chat/log.**
4. Homologar execução real, readback, SHA-256, restauração independente e recuperação após 24h, com retenção observada e quota monitorada.
5. Registrar decisão humana explícita de risco residual: Drive pessoal não possui retenção WORM/Object Lock 90 dias. Política de 90 dias sem limpeza automática **não oferece imutabilidade**.
6. Revisar demais achados P0 do Neon root (histórico 6h, proteção/snapshots não verificados como corrigidos). Alterações no banco principal requerem aprovação específica.

## Gate de encerramento

**F02 somente pode mudar para DONE** quando #128 receber provas da execução real (run/HEAD/SAFETY PASS), restore independente atual e histórico, custódia/ACL verificada, plano de rollback e aceite explícito owner_only incluindo o risco do Drive. Até isso, PR #142 pode avançar tecnicamente, mas F02 permanece HOLD. Não habilitar publish/Neon root, não migrar F03 ou novos corpora.

## Reversão / falhas

- Falha em preflight, OAuth, SHA, pasta privada, envelope AES ou restore: **HOLD**, nenhum dado em plaintext no Drive; job interrompe sem ação em Neon root.
- Desativar imediatamente `MAR_P0_GOOGLE_DRIVE_BACKUP_ENABLED`; revogar/rotacionar tokens e conta Neon dedicada no ambiente autorizado; restaurar o código anterior via Git se preciso. Não excluir backups no Drive como parte do rollback.
- O código não executa exclusão de backups; 90 dias só podem ser comprovados com histórico real de arquivos e inspeção posterior.

Referências: [fila #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128), [PR #141](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/141), [PR #142](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/142).
