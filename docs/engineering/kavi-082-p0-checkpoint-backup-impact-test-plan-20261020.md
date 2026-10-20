# MAR / KAVI nº 82 — Gate P0: auditoria preventiva de backup restrito de checkpoints

**Pré-registro ANTES DOS TESTES E DO CÓDIGO.** Data 20/10/2026. Main auditada: `9a9b8828fae7fe9309d7f59546a1b525935a1585` (PR #88). Análise nº 82/issue #59 aberta. Nenhuma chamada HTTP nem coleta real, publicação, mídia ou permissão de cron autorizada.

## 1. Inventário e causa-raiz

1. `metadata_staging.stage_metadata` já mantém `checkpoint.json` e `raw/<sha[0:2]>/<sha>.json`, usando `FileWriteLock` + `RawArtifactStore`, atomicidade local, SHA-256, IDs e cursores; `_restore` rejeita alterações e duplicidades.
2. `scripts.audit_kavi_finna_staging.audit_finna_staging` faz replay e compara proveniência/custódia/rights com **evidence_sha256 e expected_total independentes**, imprime resumo redigido e não chama API.
3. `scripts.kavi_finna_epoch_recovery` controla epochs isolados; reinício somente sob evidência efetiva de expiração. A tarefa P0 não retoma tokens, nem altera a política de epochs.
4. `data/staging/` é ignorado no Git; **não existe prova de armazenamento durável, segredo criptográfico provisionado nem ACL de bucket/volume real**. O lote de 200 fichas publicado foi produzido por job descartável, não há cursor para “continuar na 201”.
5. O MAR tem Python >=3.11; dependências não incluem criptografia AEAD. Usar biblioteca mantida `cryptography==50.0.2` (release de 30/09/2026; AESGCM). **Nunca** implementar AES manualmente, nunca registrar chaves nem colocar cursors em Actions público/Drive sem proteção.

## 2. Matriz de impacto (ANTES da implementação)

| Alteração | Consumidores/contratos | Risco e efeito indireto | Teste e retorno |
| --- | --- | --- | --- |
| Backup de UM epoch auditado, sem nova coleta | `metadata_staging._restore`, `audit_finna_staging`, checkpoints e raw SHA, locks | respaldar checkpoint falso ou capturar enquanto está sendo alterado | P01/P02/P04; fonte inalterada |
| Criptografia autenticada AES-256-GCM | `pyproject.toml`, `requirements.txt`, runner CI | token visível no arquivo, chave fraca, nonce reutilizado, campos forjados | P01/P03/P05/P06; backup inútil sem chave |
| Diretórios privados/ACL locais e substituição atômica | arquivos staging, diretórios de backup e restauração | permissões públicas, symlink, arquivo parcialmente gravado, sobrescrever estado existente | P02/P07/P08/P10 |
| Restauração por outro processo e nova auditoria | `audit_finna_staging`, mesmo evidence_sha256/total, `FileWriteLock` | restaurar conjunto misto/fora de escopo ou token falso | P01/P04/P05/P09 |
| Entrada CLI sem exposição | logs GitHub, scripts, flags de segurança | segredo como argumento do processo/log, divulgação de cursor | P06/P11 |
| Zero efeito na pesquisa, publicação, cron e análise | `CORPORA`, 200 fichas e manifesto, relatórios PR87, planejador PR88, Streamlit/i18n | inferir autorização de atualização ou nº 83 | P12/P13 |
| Destino externo real e retenção | bucket/volume privado, KMS, ACL servidor, backup multi-runner | achar que teste no mesmo host é prova de durabilidade em nuvem | P14: **HOLD externo**, verificação operacional posterior |

## 3. Contrato e gates do incremento

**Primitiva existente, não outro coletor.** `backup_verified_epoch(source_dir, backup_file, evidence_sha256, expected_total, epoch_id, key)`: valida âncoras independentes e reexecuta auditoria offline, snapshot protegido por lock, inclui **exclusivamente** o `checkpoint.json` e objetos raw referenciados nele em contêiner zip em memória, então cifra todo o conjunto com AES-256-GCM, chave de 32 bytes por secret manager e nonce aleatório de 96 bits. O arquivo persistido contém magic/version, cabeçalho autenticado sem dados privados, nonce e ciphertext/tag; o cursor e os metadados de registros existem SOMENTE dentro da carga cifrada. Escrita 0600 com fsync e troca atômica, nunca sobrescreve arquivo de backup existente. Diretórios de origem e destino devem existir e ser propriedade/acesso restrito (POSIX 0700); symlinks proibidos. Limites explícitos de tamanho e número de artefatos; lotes maiores exigem etapa própria de engenharia/streaming, não aumento silencioso de limites.

**Restauração offline:** `restore_verified_epoch(backup_file, new_epoch_dir, evidence_sha256, expected_total, epoch_id, key)`. Falha por autenticação incorreta ou integridade de manifesto; rejeita traversal, symlinks, nomes não autorizados, arquivos duplicados, itens raw cujo hash discorde, extensão/caminho estranho, epoch/scope/total diferente. Reconstrói em diretório temporário restrito (arquivos 0600), chama a **mesma auditoria independente** antes de renomear para destino ainda inexistente. Sem clobber/merge de epochs. Uma chave incorreta ou ciphertext adulterado não pode revelar os dados nem gerar pasta final.

**Chave:** material vindo exclusivamente da variável de ambiente configurada por operador em secret manager (32 bytes base64), não do GitHub público nem argumento CLI; não registrar valor, derivar hash ou imprimir erro com dados privados. Gerência de rotação, recuperação de chave e KMS reais ainda precisam de decisão operacional.

**P0 offline DONE vs P0 operacional:** passar testes sintéticos de backup/restore, confidencialidade, detecção de alteração e ACL **não comprova** durable storage entre runners nem cópias remotas, versão do bucket ou política de retenção. P0 operacional só pode ser declarado depois de comprovar um backend externo concreto com ACL/criptografia em repouso e permissões, testar upload/download *do blob cifrado* entre dois ambientes isolados, comparar hashes, recuperar com a chave protegida, medir retenção e impedir exclusão acidental. Este incremento não instala nem escolhe silenciosamente serviço de armazenamento.

## 4. Testes pré-registrados (executar apenas offline com token sintético)

- **P01:** estágio parcial sintético auditado → backup encrypted → restauração em **outro diretório** → replay offline idêntico (contagem/hash/cadeia); zero fetch em restore.
- **P02:** arquivo cifrado com 0600 e dirs 0700, sem cursor sintético ou título em arquivo/cabeçalho/log.
- **P03:** chaves de tamanho/formato inválidos ou chave incorreta são rejeitadas antes de exposição ou escrita da pasta final.
- **P04:** checkpoint adulterado, hash de raw divergente, escopo e total externo errados bloqueiam backup ANTES de criar arquivo.
- **P05:** ciphertext, nonce, cabeçalho autenticado ou truncamento alterados bloqueiam restore antes da pasta final.
- **P06:** CLI sem `--key`, carrega `MAR_KAVI_BACKUP_KEY_B64` do ambiente, retorno público redigido; nenhuma API.
- **P07:** origem ou destino de backup e diretório de restore com perms abertas recusados; backup file symlink recusado.
- **P08:** destino de backup existente ou diretório de restore existente não pode ser substituído/apagado.
- **P09:** epoch/total/evidence divergente e formato/payload não autorizado bloqueiam restore.
- **P10:** falha ou interrupção ao construir o backup não deixa arquivo parcial utilizável; pastas temporárias não contêm plaintext persistente.
- **P11:** diretório original, checkpoint/raw, invariantes de `CORPORA` e relatórios já publicados permanecem imutáveis; ciclo mensal não ativado.
- **P12:** pacote nunca contém vídeo/stream ou mídia em si; apenas checkpoint e JSON raw de metadados.
- **P13:** testes existentes de staging, epoch, reconciliação e documentação KAVI integrados e CI final verde.
- **P14:** teste ponta a ponta em *armazenamento remoto efetivo* com IAM/KMS/backup/versionamento, restauração em segundo runner e auditoria de ACL. **DEFINIDO MAS NÃO EXECUTADO**; HOLD explícito até armazenamento autorizado.

## 5. Plano de reversão e critérios de conclusão

Não alterar `stage_metadata`, `kavi_finna_adapter`, `kavi_finna_epoch_recovery`, `kavi_finna_incremental_plan`, `kavi_finna_public_catalog`, `CORPORA`, CSVs/manifestos existentes, traduções, Streamlit ou cron. Módulo/CLI ficam isolados. Remover nova funcionalidade e dependency torna o comportamento anterior íntegro; backups cifrados externos são intencionalmente incompatíveis sem chave/sistema de decrypt e não devem ser destruídos inadvertidamente.

**Ready:** esta análise commitada, testes P01–P13 commitados ANTES do módulo, zero dados pessoais/segredos em CI. **Done offline:** testes próprios e suíte global no HEAD exato, P1/P2 resolvidos, merge seguro e verificação main. **Done operacional:** P14 real comprovado. A análise científica nº82 permanece OPEN e o P1 de coleta continua BLOCKED até P14 e autorização separada.
