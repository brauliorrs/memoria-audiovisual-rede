# MAR — análise nº 82: protocolo preventivo de ampliação incremental KAVI/Finna

**Protocolo PRÉ-IMPLEMENTAÇÃO — commit anterior aos testes e ao código.** Base da main conferida: `56723f5c8dc36a85baa4eba170ca383ea1cc79b0`, PR #87 integrado. Issue #59 aberta. **Esta etapa é offline e não solicita API, não baixa mídias, não ativa periodicidade nem publica lote novo.**

## 1. Estado e inventário de dependências (não redescobrir marcos concluídos)

- Lote publicado: `data/output/kavi_mar_metadata_links.csv` e manifesto com 200 fichas Finna, 200 links de fichas `recordPage`, cobertura parcial de 200/138.399 no snapshot de 19/10/2026 (0,1445% de uma faceta API, NÃO do universo de filmes ou vídeos disponíveis).
- PR #87 já fornece `kavi_finna_metadata_reports.py` e quatro relatórios derivados para completude dos metadados. Nenhum relatório novo deve alterar essa fonte sem aprovação.
- `metadata_staging.py::stage_metadata`: **já possui checkpoint.json local, arquivos raw endereçados por SHA, validação de IDs entre páginas, detecção de ciclos de cursor, verificação de contagem e gravação atômica**. `_restore` faz replay; não reimplementar.
- `kavi_finna_adapter.py::FinnaMetadataSource`: campo `recordPage`, preflight de facetas institucionais e `format=Video`, paginação oficial `resumptionToken`; sem `fullRecord`, imagens ou vídeo.
- `scripts/kavi_finna_batch_gate.py::execute_verified_batch`: limite 1–25 páginas, auditoria offline antes/depois, validação de expiração e `expected_total` externo na retomada. `scripts/audit_kavi_finna_staging.py` comprova integridade local, **não** consistência temporal de um snapshot remoto.
- `scripts/kavi_finna_epoch_recovery.py`: controlador offline de epochs isolados e orçamento de reinício **somente com expiração efetivamente comprovada**, sem retry automático e sem presumir fuso de `expires`.
- `kavi_finna_mar_index.py::project_record` e `project_staged_catalog`: projeção documental com IDs, `recordPage` e direitos desconhecidos, originalmente em **preview**, não autopublicação. `kavi_finna_public_catalog.py` valida o CSV e manifesto **publicados**, cuja integridade não permite modificá-los silenciosamente.
- **Lacuna efetiva:** o primeiro lote em `main` veio de um ensaio temporário cujo diretório com tokens foi descartado; NÃO há cursor persistente que autorize retomar a partir do registro 201. Ainda não há serviço de backup protegido nem gate de reconciliação entre epochs/snapshots e alterações/remoções.
- `CORPORA['kavi_kuvi']`: `published_index_active=true`, `organism_active=false`, `monthly_refresh_enabled=false`, `counts_as_analyzed_corpus=false`. FINA/Ninateka polonesa é entidade distinta; análise nº 82 ainda aberta, nº 83 não iniciado.

## 2. Matriz de impacto PRELIMINAR: alteração → dependências → risco conhecido → regressão → rollback

| Incremento | Componentes/consumidores | Risco/equívoco a evitar | Testes pré-definidos | Rollback |
| --- | --- | --- | --- | --- |
| Comparação offline entre lote público e proposta de novo epoch | `kavi_finna_public_catalog`, `kavi_finna_mar_index.INDEX_FIELDS`, dados aprovados/relatórios PR87 | Publicar candidato não auditado; comparar apenas número de linhas e perder IDs; supor mesma ordem | I1–I5 | Excluir novo módulo; CSV original intacto |
| Deduplicar pelo ID da fonte e detectar atualização de descritores | `source_record_id`, `recordPage`, direitos, campos descritivos do índice | Tratar mesmo título como mesmo filme, ou mesmo ID alterado como nova obra | I3, I4, I6 | Propostas não promovidas, recomputar offline |
| Identificar ausências em observação incompleta | `status=partial/complete`, total da API, `api_snapshot_freshness_verified` | Exclusão falsa por página não vista, expiração de cursor ou ordem variável | I5, I7 | Sempre estado `not_observed`, nunca exclusão |
| Evolução de checkpoint persistente e epochs | `stage_metadata`, `_restore`, `RawArtifactStore`, `FileWriteLock`, `kavi_finna_epoch_recovery`, armazenamento | Copiar token ao GitHub; misturar epochs; reusar token após vencimento; confiar em backup sem SHA | I8–I11 (pré-registrar; implementação posterior) | Manter raw local protegido, invalidar proposta |
| Controle de publicação e atualização documental | `kavi_finna_public_catalog`, `kavi_finna_metadata_reports`, `app/streamlit_app.py`, `CORPORA`, `quality.yml` | Alterar manifestos, relatórios e dashboard antes da aprovação, iniciar job periódico | I11–I14 | Nenhuma escrita na fonte nesta fase |
| Interface multilíngue (somente se UI mudar) | `i18n.py`, `tests/test_i18n.py` | Regressão A14 já conhecida no PR87 | I14 | Nenhuma mudança de UI nesta fase |

## 3. Contratos de projeto e invariantes

**Desenho de 3 camadas — não substituir componentes já auditados:**
1. **Staging restrito persistente, por epoch**: origem privada, fora de `data/output` e do Git público. Guardar `checkpoint.json` e `raw/` SHA completos, inclusive token apenas no repositório protegido, cifra/controle de acesso/retention/backup a configurar. A persistência efetiva **NÃO** será declarada até haver backend privado e teste de restauro. Um manifesto público REDIGIDO (hashes, contagens, IDs de epoch não sensíveis) nunca incluirá cursor opaco.
2. **Reconciliação documental OFFLINE**: reler o catálogo publicado por `load_published_kavi_rows`; importar preview de outro epoch somente com validação anterior pelo estágio existente, confirmar identidade de fonte e fingerprint da carga, comparar `source_record_id` e campos permitidos. Produzir candidatos `new/changed/unchanged/unseen`, marcados para revisão. **Um manifesto de preview/autodeclaração de auditoria não representa prova independente de auditoria nem autoriza publicação.**
3. **Publicação explicitamente aprovada**: gate futuro, transação atômica de novo CSV/manifesto, checagem de direitos, proveniência e consistência, regeneração de relatórios e rollback. **Não implementado/ativado neste incremento**. Ausência na enumeração não autoriza apagar; uma remoção exigirá evidência específica na plataforma de origem ou política científica posterior.

**Sinalização científica:** fonte `Finna API/KAVI`; datas e totais específicos do epoch; contagem de fichas novas/alteradas versus obra reproduzível; zero confirmação de custódia, direitos de mídia ou playback sem auditoria adicional. `film_candidate` continua classificação de prefixo, não filme validado.

**Identidade:** somente `source_record_id` na mesma fonte e mesmo escopo identifica atualização. Títulos iguais não autorizam deduplicação de obras; serviços Elonet/Elävä muisti/Elokuvapolku/Ritva só serão reconciliados com IDs cruzados comprovados. A ordenação de resultados não representa identidade.

**Checkpoint/reinício:** validar hash da pasta raw, cadeia de cursores, contagem imutável de preflight e escopo com o código existente ANTES de qualquer retomada. `resumptionToken` pertence a UM epoch; se expirar, interromper e exigir nova decisão humana/documentada, não gerar offset, não “pular” páginas. Fuso ambíguo permanece HOLD segundo contrato atual. **Novo epoch precisa começar pelo início**; o lote antigo de 200 fichas não tem cursor retomável.

**Janela de rede — gate posterior**: obrigatória aprovação nominal do domínio e rota no `robots.txt` atual, termos da API, orçamento de páginas/limites e `delay`, evidência de escopo, política de 429/5xx (HOLD, sem retry agressivo), destino protegido, prazo de validade de token e monitoramento de direitos. Não estabelecer frequência nem agendamento antes da primeira execução incremental autorizada.

**Falha segura:** se escopo, SHA, total ou campo crítico não forem comprovados, abortar ANTES de escrever; não publicar IDs/cursors de staging nem inventar URLs; manter registros anteriores intactos.

## 4. Plano de testes escrito ANTES de código

| ID | Cenário sintético/offline | Expectativa |
| --- | --- | --- |
| I1 | Baseline 200 fichas/manifesto válidos, candidato de epoch novo com fingerprint e 2 IDs idênticos | `unchanged=2`, `baseline_unseen=198`; proposta HOLD, nenhuma publicação |
| I2 | Candidato novo com outro ID institucional e `recordPage` fornecido | `new=1`, sem URL gerada a partir do ID |
| I3 | Mesmo ID com título/ano/assunto alterado | `changed=1`, delta declarado por campo e **não nova obra** |
| I4 | Candidato repete mesmo ID duas vezes, ou fingerprint diverge | Rejeição fail-closed, sem relatório de sucesso |
| I5 | Duas fichas diferentes com título idêntico | Permanecem IDs distintos, nenhuma falsa fusão |
| I6 | Alteração de URL `recordPage` para outro ID, mídia MP4, query/fragment | Rejeição; não criar link especulativo |
| I7 | Snapshot `partial`, ou mesmo `complete` sem estabilidade externa confirmada | Ausentes são `not_observed`, **nunca removidos**, HOLD para publicação |
| I8 | Token bruto ou campo `resumptionToken` inserido no preview do planejador | Rejeição antes de retornar relatório; nenhuma credencial exposta |
| I9 | Mistura de `scope_sha256` / institution / epoch ou data inválida | Rejeição, preservar baseline |
| I10 | Evidência declarada, mas não validada independentemente | Saída `proposal_only`, `publication_authorized=false`, nunca conclusão de coleta |
| I11 | Adicionar código sem ativação do organismo | `organism_active=false`, `monthly_refresh_enabled=false`, `counts_as_analyzed_corpus=false` e 82 em aberto |
| I12 | Fonte publicada adulterada | Leitor existente rejeita antes da comparação |
| I13 | Testes dos 200 itens e relatórios PR87 | Sem alterações e `quality` integral verde |
| I14 | UI não modificada neste incremento | Nenhuma tradução nova exigida; se houver mudanças futuras, i18n/es/en obrigatório |

**Definition of Ready**: este pré-registro + evidências do código + testes I1–I12 adicionados antes do planejador. **Definition of Done (Fase offline)**: os testes específicos e integrações anteriores passam; pacote puramente funcional, sem escrita/HTTP e saída redigida; CI geral verde; revisão P1/P2 resolvida; PR mergeado só depois da prova; Drive atualizado.

## 5. Gates futuros, expressamente FORA do incremento atual

**GATE P0 armazenamento protegido**: escolher serviço real de backup com ACL, criptografia e retenção, testar gravação/restauro de diretório de estágio real e verificar integridade. GitHub Actions efêmero ou artefato público NÃO equivale a persistência de cursor.

**GATE P1 revalidação de acesso**: robots/termos no dia, preflight e orçamento máximo definido, operador autoriza uma tentativa controlada com `--execute`. Sem autorização, somente simulações offline.

**GATE P2 snapshot/reconciliação**: auditoria SHA de cada página, identificação de época, comparabilidade de totais, links por ficha e candidatos de update/delete separados; nenhuma remoção por ausência em lote parcial.

**GATE P3 publicação:** autorização de release documental, geração atômica de CSV+manifesto e relatórios, revisão de URLs/direitos e rollback; nenhuma automatização ou cron até aprovação futura.

## 6. Registro de riscos (sem criar riscos novos fictícios)

- R1 **resolvido** PR86: CORPORA ≠ análise concluída.
- R2 **controlado** PR85–87: `recordPage` não é vídeo público nem licença da mídia.
- R3 **resolvido no escopo** PR87: relatórios documentais.
- R4 **pendente previamente conhecido**: persistência protegida, expiração de cursor, múltiplos epochs, reconciliação. Este trabalho prepara testes e projeções **sem** executar coleta.
- R5 **pendente**: deploy Streamlit não inspecionado; sem impacto direto aqui.
- R6 **regressão evitável controlada**: internacionalização introduzida no PR87 e corrigida; como UI não muda agora, não criar strings novas.
