# MAR — Czech TV: P0 de evidências e prova oficial de paginação
Data: 11/11/2026. Estado: **P0 LOCAL SINTÉTICO**; **P0 EXTERNO: HOLD**; **COMPLETUDE DO CATÁLOGO: HOLD**.

Este documento complementa `monthly-cycle-recovery-20261110.md`. Não autoriza coleta pública, download de mídia, atualização mensal ou acesso a Neon.

## 1. Auditoria de impacto antes da implementação

- Contratos já existentes: `scripts/czech_capture_receipts.py` cria recibos a partir de bytes fornecidos; `scripts/replay_czech_receipts_v2.py` reinterpreta links HTML e valida contra o contrato `scripts/audit_czech_completeness_v2.py`. Nenhum autentica a origem oficial, o total do catálogo ou o esgotamento real da paginação.
- Referência criptográfica já instalada: `memoria_audiovisual.kavi_finna_secure_backup`, que usa AES-256-GCM, diretórios privados, restore independente e verificação de estágio, mas é **exclusiva** para checkpoint `FinnaScope` e não pode respaldar automaticamente a Czech TV.
- Riscos: ausência de replay sem os bytes originais; falsa promoção por hash válido; vazamento de HTML ou tokens; arquivo ou chave em repositório/CI; restauração em diretório público; confundir discos temporários com armazenamento durável externo.
- Testes previstos: cifra e decifra isoladas, nonce aleatório, divergência da chave, alteração/truncamento de ciphertext e cabeçalho, âncoras externas (scope, manifesto e pins de recibos), rejeição da prova v2 inconsistente, nenhuma exposição de HTML no blob, preservação de flags HOLD. A integração de produção e a prova remota ficam fora do escopo.

## 2. Protótipo de pacote cifrado em memória

`scripts/czech_evidence_p0_offline.py` usa a biblioteca já fixada no projeto `cryptography==50.0.2` e AES-256-GCM, com **nonce aleatório novo** por pacote e cabeçalho autenticado (AAD) que vincula escopo, hash do manifesto, quantidade de páginas e digest do plaintext.

- Entrada: respostas HTML **sintéticas e limitadas**, recibos associados, hashes dos recibos, manifesto v2, hash externo do manifesto, URLs públicas exportadas, `scope_id` e chave de 32 bytes já fornecida em memória.
- Pré-condição: o replay offline (recibos → bytes → IDs reextraídos → checkpoints → auditor v2) deve passar; são recusados manifestos de catálogo integral, alterações e falhas de reconciliação. Dados novos não são buscados pelo módulo.
- O ciphertext só expõe um cabeçalho técnico sem IDs, URLs de episódios ou HTML. O payload original fica cifrado; no restore exige-se digest do ciphertext **fornecido independentemente**, SHA do manifesto, pins dos recibos e mesmo `scope_id`. A autenticação GCM e o replay completo são refeitos.
- Limites: até 20 páginas, 12 MiB de plaintext; tamanho excedente rejeitado; sem compressão de conteúdo controlado por terceiros; sem persistir ou imprimir chaves/HTML/credenciais.
- Saída: status `synthetic_encrypted_in_memory` ou `synthetic_restored_and_replayed_in_memory`; invariantes `source_attested=false`, `corpus_complete=false`, `durability_verified=false`, `production_gate=HOLD`.
- O código **não escreve arquivos**. Os testes com dados sintéticos podem copiar o blob cifrado para diretórios temporários distintos e verificar sua leitura, mas isso **não é backup remoto**. O procedimento tem propósito de laboratório; não alimentar com HTML real da instituição sem política de minimização e retenção aprovada.

### Execução de testes offline

`python -m unittest discover -s tests -p 'test_czech_evidence_p0_offline.py'`

Também deve passar a suíte geral de CI. Qualquer teste local com `durability_verified=true` ou `production_gate` diferente de `HOLD` é incorreto.

## 3. Gate P0 externo, ainda BLOQUEADO

Somente considerar o backup operacional aprovado quando **todos** os seguintes critérios forem comprovados com evidência independente:

1. **Reutilizar o Neon/PostgreSQL existente** como armazenamento operacional de checkpoints e metadados; identificar uma **cópia de segurança independente do domínio de falha do Neon** (não um novo banco), ou demonstrar uma política de exportação/recuperação independente equivalente. Esse destino deve preservar somente ciphertext, com identidade de acesso de menor privilégio, logs, versionamento e retenção protegida.
2. Chave **fora do Git e dos logs**, provida via secret manager, com procedimento de rotação, recuperação de desastre, política de acesso e sem armazenamento da chave junto ao único backup.
3. Política sobre preservação de **HTML público limitado** ou representação canônica auditável: verificar dados sensíveis/identificadores de sessão embutidos, autorizações de uso, minimização e prazo de retenção. Nunca preservar stream, vídeo, cookies, credenciais ou URLs assinadas.
4. Cifrar somente a evidência previamente auditada, subir **apenas ciphertext** e manifestos estritamente redigidos; confirmar SHA-256 no armazenamento remoto e âncora externa imutável.
5. Em **outro executor/ambiente**, baixar o backup por identidade separada, verificar SHA do blob, descriptografar com chave autorizada, refazer os checks de recibos e cadeia e comparar contagens com as âncoras independentes.
6. Medir retenção, isolamento de permissões, falha controlada e capacidade real de restauração; registrar relatório assinado/revisado sem segredos. Não aprovar P0 apenas porque um teste local passou.

O Neon **já mantém** índices/checkpoints operacionais no ambiente de validação do MAR. Seu uso está confirmado; ele não substitui, isoladamente, uma cópia recuperável fora do próprio serviço ou uma prova de restauração entre domínios de falha. O projeto KAVI já tinha P14 (prova remota entre ambientes) pendente; o presente trabalho não altera essa condição.

## 4. Prova de paginação oficial da Czech Television: problema aberto

Fonte pública consultada para **documentação**, sem disparar o coletor: https://www.ceskatelevize.cz/api/docs/ivysilani (Swagger API v1). O recurso `/ivysilani/videos/encodings` documenta os parâmetros `since`, `start`, `limit` e `page`, mas é descrito como uma **lista de codificações de vídeo por intervalo de tempo**, e não como enumeração pública de todos os programas/episódios do iVysílání. Outros recursos documentados retornam episódios por canal/data ou informações de episódios. Não há, nessa referência consultada, evidência suficiente de um **único catálogo público global**, um **total oficial estável** para todo o universo nem uma **prova inequívoca de fim de paginação global**.

Portanto, não adotar automaticamente `rel=next`, `?page=N` ou retorno vazio como prova de completude: o teste da ponte HTML v2 apenas constata ausência de contradição na amostra **sintética**. `source_declared_total` e `official_total_attested` permanecem sem comprovação real.

**Contrato que falta antes de qualquer sondagem autorizada:**
- identificar um universo **enumerável e nomeado** com documentação da fonte: catálogo público, filtro, programa ou recorte com total explícito;
- confirmar, para esse universo exato, o método oficial de paginação, a ordenação estável, possíveis sobreposições e o marcador terminal verdadeiro;
- confrontar total emitido **pela fonte** com IDs únicos efetivos, sem extrapolar de recorte para todo o organismo;
- preservar resposta e evidência de fronteira terminal para auditoria independente, dentro do P0;
- registrar versão/data do método, limites, `robots.txt` e condições de uso, antes de autorizar **uma única sonda limitada**;
- se algum requisito não puder ser comprovado, rotular `PARTIAL` / `HOLD`; nunca `COMPLETE_VERIFIED`.

## 5. Critérios de conclusão

**Entrega deste incremento:** protótipo de AES-GCM e restore em memória com testes sintéticos; análise documentada do marcador da API; **Neon/PostgreSQL externo já provisionado e auditado posteriormente**, mas sem prova operacional de backup independente/restauração da evidência Czech.

**BLOQUEADO:** prova operacional de recuperação independente, preservação de resposta real, proveniência de TLS/HTTP, catálogo completo, atualização automática, **novas escritas ou alterações de esquema no Neon**, merge em main e habilitação da fonte. A futura decisão P0 e a autorização de coleta são duas aprovações distintas.


## 6. Errata de infraestrutura — auditoria somente leitura em 11/11/2026

Correção da premissa inicial deste documento, após confirmação do ambiente existente: **o MAR tem armazenamento externo PostgreSQL/Neon operacionalmente provisionado**. Não se deve adquirir ou criar outro PostgreSQL para satisfazer o P0. A distinção é entre **armazenamento remoto existente** e **backup criptografado com recuperação independente ainda não demonstrada**.

Verificações read-only efetuadas no Neon conectado:
- Projeto `neon-erin-field` (`holy-bread-70461948`), AWS `us-east-1`, PostgreSQL 18.
- Branches `main` (`br-raspy-river-b8qx9oo9`), `mar-p0-validation-20261021` (`br-lingering-smoke-b8hjdnzb`) e `mar-p0-recovery-20261021` (`br-holy-dawn-b8z9t6yh`) encontram-se existentes, com estado `ready`.
- A branch de validação possui as tabelas `mar_p0.checkpoints`, `mar_p0.checkpoint_pages` e `mar_p0.raw_artifacts`: respectivamente **4**, **8** e **4** linhas no momento da consulta (contagens apenas, sem ler conteúdo dos payloads).
- As tabelas têm controles de SHA-256 no banco, foreign keys e constraints que proíbem `media_downloaded=true` e `promotion_authorized=true`; os dados operacionais têm portanto um destino externo já preparado.
- Na branch `main` **não** foram identificadas tabelas `mar_p0` na listagem disponível, o que confirma isolamento de validação e não deve ser interpretado como migração produtiva.
- Consulta à lista de snapshots do projeto retornou **nenhum snapshot listado**. A consulta aos calendários automáticos de snapshots das três branches retornou `schedule: []`. O indicador `history_retention_seconds=21600` nas configurações do projeto **não é substituto** de teste de restauração de backup externo.
- Nenhum bucket de object storage do Neon foi listado na branch de validação. Isso não invalida o PostgreSQL como armazenamento persistente de metadados; sinaliza apenas que **não foi comprovado** um segundo cofre de artefatos.
- Os metadados da branch `main` exibem restrições de operações marcadas `vercel production branch`, indicando associação com a Vercel no plano de controle Neon. O projeto MAR não foi identificado inequivocamente entre os projetos Vercel visíveis à conexão consultada; por isso **não afirmar** que algum projeto Vercel específico esteja armazenando ou recuperando evidências Czech.

**Nova decisão:** adotar o Neon existente como destino principal dos checkpoints/metadados quando o contrato de acesso e a operação autorizada forem aprovados. Não implantar banco redundante. Auditar o mecanismo concreto de backup/exportação para destino independente e o restore em ambiente isolado, com hashes verificados. Até esses testes reais, **P0 de durabilidade/recuperação continua HOLD**, mas **infraestrutura PostgreSQL externa está CONFIRMADA**. Nenhuma escrita de banco, restauração real, configuração de snapshots, coleta ou produção foi executada nesta auditoria.
