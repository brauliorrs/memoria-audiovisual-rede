# MAR F02 — destino de backup: Google Drive pessoal (decisão de arquitetura)

**Decisão do proprietário, 19/11/2026:** usar o **mesmo Google Drive pessoal** que já hospeda a memória privada de desenvolvimento do MAR. A pasta exclusiva `MAR — Backups Neon (criptografados)` foi criada sob a pasta `ChatGPT`, ao lado do documento de memória. A leitura de metadados pelo conector Google Drive confirmou **pasta não compartilhada**, com permissão de **proprietário único**. Por privacidade, **não registrar aqui o ID ou URL do diretório pessoal**; o identificador operacional somente poderá ser instalado em configuração protegida após a autorização da aplicação de backup.

**Status de engenharia: DESTINO DEFINIDO, NÃO OPERACIONAL.** Nenhuma cópia real do Neon foi enviada. Nenhum novo Secret, OAuth client, job agendado, quota, serviço de retenção ou restauração foi homologado. **F02 permanece active/HOLD, F03–F13 blocked, public_access_authorized=false.**

## Escopo explícito e invariante de direitos

O backup cobre **somente metadados científicos e checkpoints autorizados** do schema `mar_p0` da branch de validação Neon; não contém mídia audiovisual, bytes de terceiros, arquivos sob HOLD, nem representa promoção de novos corpora. A branch principal Neon e o Vercel protegido ficam intocados. A fonte deverá usar login exclusivo `mar_p0_backup_reader`, com preflight live já testado em laboratório nos PRs #138/#140; **ainda não instalado** na branch de origem autorizada. Não reutilizar `mar_p0_limited` como leitor de backup.

## Arquitetura selecionada

1. **Exportação sob acesso mínimo.** Executar `pg_dump` em processo isolado, apenas após passar o verificador online de grants de tabela/coluna, ownership, memberships, funções SECURITY DEFINER e zero acesso a outros schemas. Em caso de falha, **não ler dados nem tentar upload**.
2. **Criptografia ANTES do Google Drive.** Usar o envelope já especificado em `scripts/mar_p0_offsite_pg_restore.py`: AES-256-GCM autenticado, header de proveniência, fingerprint de esquema/linhas e SHA-256 do ciphertext. O Drive jamais recebe plaintext, URL Neon, senha ou chave de descriptografia.
3. **Upload por OAuth do proprietário, com acesso limitado.** Usar aplicativo/cliente de backup separado e o escopo `https://www.googleapis.com/auth/drive.file`, preferencialmente com autorização da pasta por **Google Picker**, para restringir acesso aos objetos selecionados/criados pelo aplicativo. A pasta previamente criada via conector ChatGPT **não fica automaticamente acessível a outro OAuth client** sob `drive.file`: precisa ser aberta/escolhida para esse aplicativo. Se essa associação não for possível, criar pasta nova **pelo próprio aplicativo de backup** na mesma conta, após decisão documentada; **não** pedir escopo total `drive` silenciosamente. A conexão Google Drive desta conversa **não é Secret exportável nem credencial de GitHub Actions**.
4. **Um arquivo novo por execução.** Nome neutro com timestamp UTC, identificador de execução e SHA-256, sem nomes de corpora/linhas. Não sobrescrever arquivo anterior. Registrar ID privado do objeto, hash, tamanho, versão do envelope e instante UTC em manifesto restrito. Confirmar upload por **download autenticado e SHA-256 idêntico**; upload HTTP 2xx sozinho não é prova de recuperação.
5. **Restauração independente.** Um runner distinto deverá recuperar o ciphertext do Drive usando credencial autorizada, verificar SHA-256 e etiqueta AES-GCM e executar `pg_restore` em PostgreSQL descartável. Conferir estrutura, contagens e digests; testar periodicamente cópia com mais de 24 horas e, ao amadurecer o histórico, cópias com 30–90 dias. Falha de qualquer etapa mantém o gate em HOLD e emite alerta **sem dados sensíveis**.
6. **Retenção operacional mínima de 90 dias.** Não excluir automaticamente arquivos antes de 90 dias. A limpeza posterior só poderá existir com contagem de cópias suficientes, último backup íntegro, restauração recente comprovada e autorização explícita; preferir inicialmente **nenhuma exclusão automática**. Monitorar quota do Google Drive pessoal (compartilhada com Gmail e Fotos). O espaço disponível e a dimensão de 90 cópias **ainda não foram medidos**.
7. **Segredos e controle de acesso.** OAuth refresh token, credenciais de Neon e chave AES em ambientes/secrets protegidos e separados; nunca no Drive, Git, memória de desenvolvimento, registros de CI ou chat. Token pessoal confere risco sobre a conta privada: limitar escopo e rotação, registrar acessos e evitar compartilhar a pasta. Não habilitar job pelo simples merge de código.
8. **Ativação por opt-in** `MAR_P0_GOOGLE_DRIVE_BACKUP_ENABLED=true` **somente** depois de testes e aceite específico do responsável único na issue #128; no estado atual, a variável não foi configurada e **não há cron em execução**.

## Impedimento de classificação como WORM/imutável

**Google Drive pessoal não é WORM Object Lock Compliance.** Ser proprietário, manter revisões ou não excluir por política **não impede** que o titular da conta ou um agente com credenciais amplas apague arquivos. Portanto:

- **Decidido:** Google Drive pessoal como destino de cópia externa cifrada e retenção **operacional** planejada para 90 dias.
- **Aceite humano explícito em 19/11/2026:** o proprietário confirmou em resposta direta que aceita, **somente durante o desenvolvimento preliminar**, o risco de exclusão acidental, indevida ou maliciosa das cópias mantidas no Google Drive pessoal **sem WORM/Object Lock**. A decisão é limitada ao destino Drive selecionado e não inclui produção, abertura pública, mudança do Neon root ou integração de corpora. Registro versionado em `mar-f02-google-drive-personal-backup-decision.json` e issue #128.
- **Controles compensatórios mantidos:** AES-256-GCM antes do upload, SHA-256 com readback, acesso mínimo, backups individuais, sem exclusão automática, retenção operacional pretendida de 90 dias e restauração independente comprovada. **Nada disso torna o Drive imutável ou prova retenção já observada.**
- **Exceção de imutabilidade, não encerramento F02:** o requisito WORM fica **formalmente dispensado apenas para a fase preliminar**, por aceite explícito do risco residual. Os gates operacionais (OAuth, reader, backups atuais/antigos, restauração, quota, custódia, rollback e aceite final) continuam HOLD. PR #92 e #93 permanecem sem ativação e não constituem escolha operacional. Reavaliar imutabilidade antes da fase de produção.

## Gate F02: aceite técnico mínimo antes de cron

| Gate | Evidência obrigatória | Situação em 19/11/2026 |
| --- | --- | --- |
| Pasta privada do mesmo Drive | Metadados do Google Drive: proprietário único e não compartilhada | **VERIFICADO** |
| Acesso OAuth à pasta pelo executor | Scope drive.file, Google Picker/ownership testado, sem acesso excessivo | **PENDENTE** |
| Reader Neon no ambiente autorizado | Login separado, sem DML ou acesso extra em teste real | **Só LAB** |
| Backup externo cifrado corrente | SHA-256 pós-upload e readback completos | **PENDENTE** |
| Restauração independente atual/antiga | Runner diferente, `pg_restore`, esquema/contagens/digests | **PENDENTE** |
| Retenção mínima 90 dias | Inspeção histórica, quota e rotina de detecção de perda | **PENDENTE** |
| Imutabilidade 90 dias | Drive sem WORM; risco residual aceito explicitamente pelo responsável somente para desenvolvimento preliminar | **EXCEÇÃO DOCUMENTADA — sem WORM** |
| Autorização de cron | Opt-in, controles de Secrets/Environments, revisão owner_only | **PENDENTE** |

**O aceite de risco não ativa o backup nem substitui restauração real.** Não criar um "backup" fictício na pasta como prova operacional. Um arquivo de demonstração cifrado pode testar o acesso quando OAuth estiver pronto, mas deve ser identificado como `test-vector`, nunca confundido com exportação de dados reais do MAR.

## Referências oficiais

- Google Drive API: escopos `drive.file` e uso com Google Picker: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Drive API: upload e recuperação de arquivos: https://developers.google.com/workspace/drive/api/guides/manage-uploads
- Google Drive: quota pessoal compartilhada: https://support.google.com/drive/answer/9312312
- AWS S3 Object Lock como opção de WORM independente: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
- Fila MAR: https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128
