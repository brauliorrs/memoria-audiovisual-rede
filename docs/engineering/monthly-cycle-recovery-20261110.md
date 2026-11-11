# MAR — auditoria e correção do ciclo mensal (10/11/2026)

## Evidência e fronteiras

Fonte primária: GitHub Actions **Organismo Mensal** em
[2026-11-01, run #41326600431](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/41326600431).
O ciclo em `main` percorreu 60 corpora, com 52 sucessos e 8 falhas,
terminando com exit code 1. Isso não é um erro de deploy Vercel e não está
relacionado à integração experimental Psycopg/Neon do PR #90.

Os scripts escreveram um manifesto local do ciclo, mas a etapa de upload
do workflow foi pulada após o comando terminar com erro. O registro por
corpus, contendo as oito falhas, não ficou disponível como artefato do run.

## Diagnóstico por fonte, extraído do log

| Corpus | Evidência observada | Tratamento |
| --- | --- | --- |
| APE / Archives Portal Europe | HTTP 403 no PDF oficial `20251215_OnlyInstitutionsWithContent.pdf` | HOLD da fonte. Não contornar controle 403 nem usar fonte não oficial como se fosse APE |
| ASIM / Mallorca | zero fichas audiovisuais retornadas por rota EFG | Revisar acesso público, consulta e parser, com fixture genuína |
| Bundesarchiv | zero registros analíticos da rota EFG | Reavaliar rota de catálogo institucional e suas condições de acesso |
| Bulgarian National Film Archive | zero registros analíticos da rota EFG | Revalidar via catálogo oficial, não inferir itens a partir de páginas gerais |
| CICLIC | zero fichas audiovisuais apesar de rota responder | Investigar paginação/AJAX e atual HTML com testes determinísticos |
| Czech Television / iVysílání | corpus/catalogo analítico vazio | Revisar seletor, paginação e URLs públicos; não usar dados fabricados |
| Eye Filmmuseum | zero de 630 registros esperados na amostragem | Verificar se endpoint de fragmentos mudou; manter discrepância explícita |
| Filmoteca Valenciana | zero de 60 mínimo, antigo domínio `www.restauracionesfilmoteca.com` | Código corrigido para domínio IVC oficial `restauracionsfilmoteca.ivc.gva.es`, com páginas espanholas `/es/archivo/…` e fichas `/es/ficha/…`, sujeito a teste controlado |

A rota institucional nova da Filmoteca Valenciana e seus seis índices
de ficção/não ficção foram confirmados por páginas oficiais do IVC:
https://restauracionsfilmoteca.ivc.gva.es/es/ .
A mera existência da rota não prova que todas as fichas tenham player
público nem que o piso 60 seja atingido. Os testes do PR são offline.

## Alterações mínimas e contratos preservados

1. O workflow passa a preservar `observatorio_ciclo_mensal.json`,
   `observatorio_resultados_ciclos.csv` e
   `observatorio_linha_do_tempo_ciclos.csv` mesmo que o comando de
   coleta falhe, com retenção limitada. Os artefatos completos continuam
   exclusivos de ciclos bem-sucedidos.
2. Cada resultado de corpus passa a identificar
   `failure_stage=collection|validation|snapshot`, sem alterar os
   estados `success`/`failed`, a contagem de falhas ou o código final
   diferente de zero quando necessário. O campo é mantido no manifesto
   e no CSV histórico.
3. A Filmoteca passa a consultar apenas um conjunto fixo de sete índices
   oficiais em espanhol e as fichas deduplicadas por ID Vimeo. Sem
   baixar vídeos, sem player hospedado no MAR. Um índice indisponível
   força `integrity_status=instavel` e
   `collection_complete=false`. O piso de 60 vídeos **não foi
   reduzido** e não se declara restauração concluída sem nova validação.
4. Os demais sete conectores não são classificados como corrigidos:
   permanecem bloqueados individualmente até inspeção de respostas
   atuais, atualização de parser/rota e teste com evidência pública
   legítima. Não desativar a auditoria global nem trocar `failed`
   por `success` para fazer o CI passar.

## Plano de testes e limites

- Testes offline para URLs e deduplicação da Filmoteca, rejeição de
  listagem indisponível, contagem de falhas, estágio de erro e upload
  do manifesto no caso de falha.
- CI normal da branch de correção; **sem invocar** `Organismo Mensal`
  completo, sem baixar mídia, sem conectar à branch principal Neon,
  sem executar migrações de banco.
- Após CI, sonda unitária por instituição com poucas requisições
  públicas e autorização explícita antes de reconstruir todo o corpus.
- A integração PostgreSQL isolada do PR #90 passou em 10/11/2026,
  mas o Gate P0 **permanece HOLD** até backup criptografado em destino
  externo independente e restauração comprovada. O ciclo mensal não
  pode usar esse armazenamento experimental automaticamente.

## Gate de saída para cada uma das oito falhas

Uma fonte só volta a `success` após evidências recentes de acesso
permitido, extração válida, contagem coerente, links/proveniência
preservados e aprovação do verificador de corpus, sem ampliar a coleta
sem autorização.


## 10/11/2026 — tratamento individual dos sete corpora ainda falhos (PR #91)

Além da preservação de evidências e da Filmoteca Valenciana, as sete
origens receberam análise individual, controles e testes isolados.
**Nenhuma está classificada como recuperada no ciclo mensal real.**

| Fonte | Alteração concreta | Prova que falta |
| --- | --- | --- |
| APE | `ape.py`: HTTP 403 e 429 do PDF oficial viram `ApePublicAccessHold` com erro não sensível; nunca simula PDF nem tenta acesso alternativo não autorizado. `test_ape_access_hold.py` verifica. | Volta de acesso público permitido ao documento, ou rota oficial equivalente documentada e autorizada |
| ASIM | Parser passou a usar `parse_efg_search_page`: decodifica identificadores `asim%3A%3A`, deduplica e rejeita links fora do domínio EFG. | EFG devolver fichas válidas e o verificador do ASIM confirmar registros reais |
| Bundesarchiv | Mesmo parser compartilhado para `barch::`, com restrição HTTPS/domínio; a página oficial do Bundesarchiv confirma o Digitaler Lesesaal como catálogo contextual, **não** como substituição automática do EFG. | Prova de páginas públicas com itens fílmicos e respectiva disponibilidade, sem afirmar streaming universal |
| BNFA | Mesmo parser para `bnfa%3A%3A`; o EFG ainda indexa uma coleção de vídeos, mas links indexados não são prova de acesso na hora da coleta. | Retorno real do EFG, análise dos status HTTP e das fichas, sem uso de espelho |
| CICLIC | `ciclic.py`: quando a resposta AJAX retorna sem fichas na primeira página, uma única consulta adicional ao índice público HTML pode descobrir fichas `/NNN-slug`; HTTPS e domínio institucional obrigatórios; parser deduplica. | Observar HTML real, verificar fichas, controle de paginação e validação do corpus |
| Czech Television | `czech_television.py`: se `__NEXT_DATA__` não trouxer programas, extrai poucos links públicos de `/porady/{id-slug}/` como **candidatos**, sem alegar `isPlayable`. Somente episódios cuja ficha `mediaMeta.isPlayable` seja verdadeira entram no catálogo. | Confirmar fichas e reprodução disponíveis com base em resposta atual; não colher conteúdo não autorizado |
| Eye Filmmuseum | `eye.py`: filtro antigo `with film fragment` sem total declarado gera `eye_film_fragment_filter_not_confirmed`; dados gerais do catálogo não podem ser marcados `integro` como se fossem 630 fragmentos. | Encontrar recorte oficial contemporâneo para fragmentos efetivamente visíveis, com contagem e páginas verificadas |

**Sonda pontual opt-in:** `scripts/probe_monthly_sources.py` aceita uma
fonte por chamada (`ape`, `asim`, `barch`, `bnfa`, `ciclic`,
`czech_tv` ou `eye`). Por padrão só imprime um plano sem rede. A sonda
*live*, quando autorizada, exige `--execute` e a variável temporária
`MAR_SOURCE_PROBE_APPROVED=yes`. Primeiro consulta uma única vez o
`robots.txt` do host com limite de 64 KiB. Só acessa o índice público quando
as regras permitem; ausência, erro ou bloqueio de robots gera HOLD sem tocar
no catálogo. Em seguida realiza no máximo um GET HTTPS (até 128 KiB de HTML),
sem redirecionamentos, mídia/PDF ou armazenamento de HTML. Emite somente
status, categoria, tamanho, hash da amostra e marca textual. **HTTP 200 não
equivale à confirmação do corpus.** As respostas 403/429 preservam o bloqueio.
O operador deve observar adicionalmente os termos de uso da origem.

Workflow isolado `.github/workflows/monthly-source-probes.yml`: somente PR #91,
etiqueta explícita `mar-source-probes-approved`, por `brauliorrs`, branch
exata, primeira tentativa, sem segredos, Ubuntu 24.04 e sete jobs sequenciais
(`max-parallel: 1`); cada job trata uma fonte e não realiza validação de
corpus nem modifica produção. Não executar a etiqueta antes de Quality Checks
aprovado para o commit revisado.

Testes offline adicionados:
`test_monthly_source_probes.py`,
`test_monthly_efg_provider_links.py`,
`test_ape_access_hold.py`, novos testes de Czech Television,
CICLIC e Eye. Nenhuma sonda live foi acionada, nem o ciclo dos 60
corpora. Sem alteração no PR #90, no Neon de produção ou na `main`.

Evidências públicas consultadas:
- APE: https://www.archivesportaleurope.net/find-an-institution/
- ASIM: https://www.europeanfilmgateway.eu/content/Arxiu%20del%20So%20i%20de%20la%20Imatge%20de%20Mallorca%20%28Palma%29
- Bundesarchiv: https://www.bundesarchiv.de/en/research-our-records/research-by-media-type/films/
- BNFA (índice EFG): https://www.europeanfilmgateway.eu/search-efg/bnfa
- CICLIC: https://memoire.ciclic.fr/films-d-archives
- Czech TV: https://www.ceskatelevize.cz/ivysilani/kategorie/4029-kultura/katalog/
- Eye: https://filmdatabase.eyefilm.nl/en/collection/film-history/film

**Decisão:** manter o refresh automático com estado de falha quando o
verificador reprovar; não substituir registros que faltam por amostras
artificiais, não converter erros em sucesso e não autorizar coleta massiva.


## 10/11/2026 — estágio incremental de Eye e Czech TV

Após [sondas estruturais #42885575326](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/42885575326) e [sondas do parser #42886797652](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/42886797652), ambas limitadas e verificadas, foi implementado o **estágio experimental** em `scripts/probe_staged_eye_czech.py`, com workflow `staged-eye-czech-probe` protegido pela etiqueta **`mar-staged-eye-czech-approved`** no PR #91. Sem etiqueta, não existe operação viva. Apenas `brauliorrs`, branch exata, PR #91 e primeira tentativa podem disparar o job. Usa Ubuntu 24.04, sem segredos, sem Neon.

**Eye Filmmuseum:** uma consulta ao `robots.txt`; acesso no máximo às páginas 0, 1 e 2 do filtro oficial de fragmentos (duas páginas adicionais à amostra inicial). A cada página, exige HTTP 200, HTML limitado a 512 KiB, o mesmo total declarado de fragmentos e entre 1 e 20 fichas com URL HTTPS da instituição. Os identificadores são deduplicados entre páginas e os estados cumulativos ficam em checkpoints JSON após cada etapa, com SHA-256 da resposta e cadeia de hashes. O resultado `STAGED_PASS` **não** certifica as 630 fichas ou seu player.

**Czech Television:** uma consulta ao `robots.txt`, um índice público de cultura, exatamente um programa escolhido entre os candidatos reconhecidos, e exatamente um episódio indicado na página desse programa. Só uma ficha com `mediaMeta.isPlayable=True` e ID no HTML do episódio confirma a disponibilidade declarada **nos metadados públicos**. Não abre, reproduz ou baixa o stream; não tenta outros programas nem episódios após uma falha. A amostra do catálogo pode ser truncada, mas as páginas do programa e do episódio não podem ser. O resultado `STAGED_PASS` **não** confirma direitos de reprodução em todas as regiões.

As duas sondas observam o `robots.txt` antes das consultas, aplicam intervalo mínimo de 1 segundo ou o `Crawl-delay` publicado (até 30 s; acima disso: HOLD), não seguem redirecionamentos e não aceitam URLs de outro domínio ou mídia. Qualquer erro leva a `HOLD`, sem nova tentativa automática. Não são produzidas planilhas ou fichas de produção.

**Checkpoints e recuperação:** cada job salva `data/probe-staged/{eye,czech_tv}.json` ao iniciar e após cada passo; o GitHub Actions publica esses arquivos com `always()` mesmo se o estágio for HOLD, em artifacts com retenção de **30 dias**. O arquivo contém proveniência mínima, hash dos fragmentos HTML (não os conteúdos brutos), IDs públicos e deduplicação. Isso permite auditoria e comparação, mas **não** é um checkpoint de armazenamento externo durável, nem implementa retomada automática após os 30 dias. Não substitui o Gate P0 para Postgres (backup externo independente e restauração).

**Testes planejados e critérios de saída:** `tests/test_staged_eye_czech_probe.py` cobre limite de três páginas Eye, deduplicação, cadeia de integridade e falhas de filtro/403; para Czech TV cobre exatamente um programa e um episódio, sinal `isPlayable` e HOLD sem fallback. Validar o Quality Checks do commit final antes de aplicar a etiqueta. Depois executar no máximo um estágio autorizado; auditar logs e artifacts. **Validação completa dos corpora continua pendente** mesmo com estágio bem-sucedido.

**Escopo de HOLD:** APE, ASIM, Bundesarchiv, BNFA e CICLIC continuam bloqueados conforme evidências anteriores. O estágio não aciona o ciclo mensal nem altera a `main` ou Neon.


## 10/11/2026 — resultado real do estágio Eye/Czech TV (#42890273211)

Execução controlada [GitHub Actions #42890273211](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/42890273211), na branch isolada do PR #91, com SHA revisado `3621f15f0db564061c592b61b7aa3307c7277c19`. Os dois jobs foram executados, com artefatos JSON preservados, mesmo quando um job retornou exit 2. **A execução global ficou vermelha devido ao HOLD correto do episódio Czech TV**, não a falha de instalação/CI nem a downloads.

| Origem | Evidência estruturada | Checkpoint | Conclusão |
| --- | --- | --- | --- |
| Eye Filmmuseum | páginas 0, 1 e 2: **10 + 10 + 10** fichas; **30 IDs distintos**, **0 duplicatas**; total **630** declarado e estável; robots respeitado com 10 s de intervalo | [Artefato Eye #13798660391](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/42890273211/artifacts/13798660391); cadeia SHA-256 `fea4d73288205ece1fc7821bc565079e4eed5ce08db5a02d330df38a586988d0` | **STAGED_PASS**, apenas páginas de metadados; 630 fichas e disponibilidade dos respectivos players **não validadas** |
| Czech Television | índice HTML público com **6** candidatos (amostra truncada); **um** programa ID `12701251153` com **10** URLs de episódios; examinada **uma** URL de episódio, cujo parser não confirmou `mediaMeta.isPlayable=True`; nenhum ID de episódio materializado | [Artefato Czech #13798810475](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/42890273211/artifacts/13798810475); cadeia SHA-256 `f8ab06981e5074927b00c7ae6b03c7d8632a1c1ada21920bfe42a8ef0b69fc0f` | **HOLD** com razão `czech_episode_not_playable_in_public_metadata`; não inferir indisponibilidade generalizada, pois pode haver ausência/mudança de estrutura `__NEXT_DATA__` |

A cadeia de hashes foi **recalculada independentemente** a partir das etapas de cada JSON e conferiu em ambos os artefatos. A retenção do GitHub é **30 dias**, não backup durável nem checkpoint operacional para recomeçar os 630 registros automaticamente. Não foram extraídos HTML bruto, vídeo ou URLs de mídia, e não ocorreram escritas em produção.

**Nota de proveniência corrigida após a execução:** os artefatos históricos contêm `head_sha=4523b4ab1536da887e7997d48072f08aa247127d`, que é o SHA sintético da execução `pull_request`, não o verdadeiro HEAD `3621f15f0db564061c592b61b7aa3307c7277c19`. A partir do commit subsequente, o workflow injeta `MAR_PROBE_HEAD_SHA` com o HEAD revisado e registra também `workflow_sha`. Os artefatos históricos permanecem imutáveis e são auditados segundo a revisão indicada no próprio GitHub Actions; não confundir os dois SHAs.

**Gate:** Eye aprovado somente para o recorte 3 páginas / 30 registros; Czech permanece HOLD, sem nova tentativa automática. Nenhum corpus foi marcado como completo; não rodar os verificadores integrais antes da coleta autorizada/validada e não unir o PR #91 à `main` com base apenas neste teste. Próxima investigação Czech: determinar, com nova autorização e evidência pública pontual, se `mediaMeta` está ausente ou se informa `isPlayable=False`; só então revisar o parser ou selecionar uma nova amostra declarada. Os demais cinco corpora continuam HOLD.


## 11/11/2026 — diagnóstico diferencial Czech TV autorizado como próximo estágio

O Quality Checks [#42892094100](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/42892094100) terminou em **success** no commit `c83410a3a0dda0d87415767837c633e77f1913c8`.

Para resolver o HOLD da única amostra Czech TV sem mascarar indisponibilidade, o estágio `scripts/probe_staged_eye_czech.py` foi ampliado com `classify_czech_episode_metadata`, um classificador **somente de HTML público** que diferencia, antes do parser existente:
- ausência de `__NEXT_DATA__`, JSON inválido ou estrutura inesperada;
- ausência de `mediaMeta` no caminho esperado e ausência da chave `isPlayable`;
- `isPlayable=False` explícito, sinal não booleano ou `True` sem identificador;
- confirmação apenas de `isPlayable=True` com identificador explícito (ainda sem testar reprodução real).

O checkpoint registra classificação, indicadores de presença, hash de HTML e cadeia SHA-256; **não armazena HTML bruto, mídia ou URLs de streaming**. Para não trocar a amostra silenciosamente, o único programa elegível é o ID `12701251153` observado na sonda anterior, e há no máximo um episódio candidato (o primeiro encontrado, que pode mudar se o índice mudar). HTTP, robots, crawl-delay, HTTPS/mesma origem e política de HOLD permanecem intactos. O workflow de etiqueta `mar-staged-eye-czech-approved` executa **apenas `czech_tv`** neste novo estágio; o Eye validado previamente não será reconsultado. Nenhum validador integral ou refresh mensal foi habilitado.

A classificação diferencial melhora o diagnóstico, mas **não é prova de reprodução** nem libera o corpus. Qualquer teste live precisa ser executado somente após aprovação do Quality Checks do SHA alterado e deve conservar a mesma etiqueta opt-in. O PR #91 permanece draft.


## 11/11/2026 — confirmação do objeto público de episódio

**Fase de descoberta, sem alteração inicial de parser:** [Quality Checks #43061462821](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43061462821) aprovou o commit `b9664628`. Na sonda controlada [#43062051588](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43062051588), apenas Czech TV, o checkpoint [#13873073900](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43062051588/artifacts/13873073900) demonstrou `__NEXT_DATA__.props.pageProps.data.episode`, com campos `isPlayable`, `nextEpisode`, `playabilityError` e `show`; o caminho antigo `data.mediaMeta` não apareceu. Também há JSON-LD do tipo `TVEpisode` e metadados `og:video`. Os 48 nós de estrutura foram percorridos sem truncamento. Cadeia SHA-256 `8924b06bc6d3ce88faefac4b80ef5395280cb2ce07cca13d79437ad9031803d9` validada por recomputação.

**Fase de confirmação de tipos e identidade:** [Quality Checks #43062466707](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43062466707) `success` no commit `93d33b38`; sonda pontual [#43063049600](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43063049600), ainda 1 programa ID `12701251153` e apenas 1 episódio, confirmou na amostra pública:
- `data.episode.isPlayable` é o booleano **True**, e não uma string ou simples presença de chave;
- `data.episode.id` e `data.episode.idec` estão presentes; `title` também;
- campos estruturais observados incluem `description`, `durationText`, `year`, `uploadDate` e `show`;
- o parser legado continuou retornando `HOLD` porque examinava apenas `mediaMeta`.

Checkpoint [#13873039680](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43063049600/artifacts/13873039680), cadeia SHA-256 `f68158e86d3299bfc5052ba249bc24913bf4955b289800f90a8f19a053869074`, validada por recomputação. Apenas nomes de campos, presença, booleanos categóricos e hashes foram registrados; nenhum HTML, token, mídia, URL de streaming ou conteúdo de episódio foi armazenado.

**Correção isolada em PR:** `parse_czech_television_episode_page` passa a aceitar `data.episode` além do legado `data.mediaMeta`. Só materializa registro com `isPlayable is True` e identificador público; se quaisquer formatos coexistentes contiverem `False` explícito, falha em modo fechado. A sonda staged usa o mesmo contrato, distingue a proveniência `metadata_path_used` e continua marcando `actual_stream_playback_verified=False`. Foram adicionadas regressões offline para estrutura atual, falso/ausente/string, ausência de ID, contradição entre sinais, continuidade do legado e integração do coletor com fetch simulado.

**Gate mantido:** a observação prova disponibilidade declarada nos metadados de **um** episódio, não reprodução efetiva, direitos globais ou integralidade do corpus. `STAGED_PASS` não autoriza `check_czech_television_outputs.py` sobre material de produção nem refresh mensal; PR segue draft, `main` e Neon intactos. A aprovação do Quality Checks do SHA da correção e uma última sonda limitada são necessárias para registrar o efeito real do parser novo. O Eye permanece no estágio previamente validado, sem novas consultas.


## 11/11/2026 — contrato de completude Czech Television (v1, fail-closed)

**Auditoria de impacto:** `collect_czech_television_dataset` tratava `integrity_status="integro"` para qualquer lista não vazia de episódios e `scripts/check_czech_television_outputs.py` aceitava `video_links_total>=1`; isso convertia **acesso a uma ficha** em **aprovação do corpus**. O recorte atual é explicitamente MVP (no máximo seis programas x dois episódios por programa), **não** enumeração de todos os episódios públicos da Czech Television. Os arquivos históricos de 07/07/2026 com 10 links não comprovam cobertura atual nem total institucional.

**Novo contrato explícito:**
1. **Registros acessíveis (access):** fichas com URL de episódio na origem oficial, identidade e `isPlayable=True` nos metadados públicos. A coleta delimitada pode listar essas fichas e conservar `status=ok` como **acesso ao endpoint**, mas não marcar corpus completo. Contagens, links únicos e domínio são reconciliados pelo checker.
2. **Amostra validada (staged):** somente a comprovação independente, obtida mediante checkpoint cuja cadeia foi recalculada e comparada com a amostra específica. Uma referência que parece SHA-256 ou a mera contagem de fichas **não equivale** a essa auditoria. O pipeline mensal não importa automaticamente os artefatos temporários das sondas, portanto gera `validated_sample_records=0`, `sample_validation_status=not_attested_in_this_run` e `sample_checkpoint_reference=null`. As evidências pontuais Eye/Czech permanecem separadas no histórico de probes; não alteram o status do corpus mensal.
3. **Corpus completo (full):** exige universo público explicitamente definido, total declarado pela fonte, enumeração e deduplicação integral, paginação comprovadamente esgotada, ausência de páginas falhas e checkpoint de proveniência **validado independentemente**. No contrato **v1** essa reexecução independente ainda **não existe**; portanto `corpus_complete=false` em todos os snapshots produzidos pelo coletor e o checker retorna **HOLD (exit 1)** até com JSON aparentemente completo e hashes autodeclarados. Proibido converter o MVP em `COMPLETE_CORPUS_VERIFIED` sem implementar uma verificação v2 de evidências externas.

**Alterações isoladas:** `czech_television.py` fixa `integrity_status=instavel`, `priority_review=True` e publica os contadores separados; `pipeline.py` exporta os novos campos no resumo CSV; `snapshot_metadata.py` adiciona `coverage.contract_version=1` e as declarações negativas explícitas. O verificador rejeita snapshots antigos sem contrato, arquivos ausentes, divergência de contagens, link fora da origem, duplicidade, falta de provas `isPlayable=True`, inconsistencia do resumo e qualquer alegação integral sem auditoria externa. O resultado negativo **não apaga os registros coletados**; mantém a evidência parcial disponível para investigação.

**Testes determinísticos offline** em `tests/test_czech_television_completeness.py`: um e dez registros acessíveis continuam HOLD; snapshot legado bloqueado; amostra com SHA não verificado não vira validada; snapshot com alegação de total integral forjado não passa; duplicata falha; builder do snapshot não importa automaticamente evidência externa. Teste preexistente do coletor ajustado para não esperar `integro` numa amostra de um episódio.

**Restrição operacional:** não rodar o pipeline mensal das 60 fontes, nenhum lote maior Czech TV, nenhum download audiovisual, nem escrita/merge em `main` ou Neon. O Gate P0 de checkpoints duráveis continua independente. Eye já tinha contagem integral nominal de 630 em seu checker e mantém **somente** STAGED_PASS de 30 fichas, sem ampliar sua amostra automaticamente. Critérios de saída futuros: fonte autorizar varredura delimitada, demonstrar enumeração/total oficial, armazenar manifesto protegido com digest verificável, repetir auditoria independente e só então propor contrato v2 e decisão de promoção.
