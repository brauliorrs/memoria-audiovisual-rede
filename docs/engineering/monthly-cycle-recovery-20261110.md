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
