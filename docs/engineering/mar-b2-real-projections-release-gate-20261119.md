# MAR — Consolidação da Arquitetura B2: projeções reais e gate de build (19/11/2026)

**Status:** revisão em PR #125, empilhado sobre #124 → #123 → #121. Sem merge, deploy autorizado, alteração de SSO ou abertura pública.

## 1. Fonte científica e reconstrução em Python

O comando `python3 scripts/build_mar_site_projections_b2.py --check` recalcula semanticamente **34 projeções atuais**: seis lotes de relatórios agregados (62 corpora), dezesseis lotes de recortes CSV por corpus, sete lotes de perfis de instituições com conferência dos CSVs e preservação de lacunas curatoriais, o painel piloto de pesquisa (quatro corpora), nuvem de palavras pelo algoritmo já usado no MAR, e três arquivos de decisões HUMANAS congeladas (KAVI, inventário de acesso e casos documentados). O arquivo externo de geometria geográfica continua separado; o mapa é calculado dos recortes geográficos.

O gerador não cria instituições fictícias quando os CSVs do APE contêm dados incompletos; conserva campos vazios do histórico revisado. A ordem editorial do painel piloto também é preservada. Uma mudança de nomes, URLs, instituição, lista de corpus ou permissão de publicação que exija nova revisão científica/curatorial resulta em **HOLD**, sem aceitar uma mudança silenciosa.

O comando `--stage-dir /tmp/<diretorio-novo>` não altera `site/data`. Emite as 34 projeções e **um manifesto único**, com SHA-256 de insumos científicos e saídas e um epoch SHA-256 determinístico, por gravação isolada e rename atômico. A versão inicial tem `status=REVIEW_ONLY_NOT_PUBLICATION_AUTHORIZATION`, sem assinaturas de aprovação. O teste de stage é verificável com o conjunto real congelado.

## 2. Bloqueio no build efetivo

O próprio `site/package.json` executa `site/scripts/verify-scientific-snapshot.cjs` ANTES de `next build`. Adicionalmente, `site/next.config.ts` chama o mesmo verificador, evitando que um Build Command personalizado invoque `next build` diretamente e ignore o script npm.

O verificador funciona sem acesso à árvore Python na máquina de build. Enquanto não existir um manifesto aprovado, confere **os Git blob IDs dos 33 JSONs científicos** com a trava congelada do PR #121, o roster exato dos arquivos e os direitos curatoriais: 200 fichas KAVI metadata-only, índice de acesso que não concede licença, casos não autorizados para publicação e nuvem de palavras agregada. Bloqueia qualquer JSON novo, excluído, alterado isoladamente ou mudança indevida de permissões.

Um futuro arquivo `site/data/scientific-release-manifest.json` só será aceito se tiver **o mesmo schema do candidato Python** (`mar-scientific-release-v1`), `status=APPROVED_FOR_PROTECTED_BUILD`, referências verificáveis de admissão científica, revisão curatorial e commit aprovado, além do SHA-256 de TODAS as projeções e epoch verificado. Meramente criar um manifesto vazio não contorna o bloqueio.

**Limite técnico:** não foi configurado nem homologado um Deployment Check de promoção na plataforma Vercel. O gate implementado impede **novos builds inconsistentes** que usem a configuração Next.js aprovada, mas a promoção manual de um deployment previamente pronto exige processo de aprovação separado. Não confundir CI aprovado com promoção autorizada.

## 3. Automação de nuvem temporariamente suspensa

A automação antiga de refresh semanal/push da nuvem podia propor apenas um JSON isolado. Isso conflita com o bundle científico atômico. Durante B2, o workflow `mar-wordcloud-refresh.yml` fica **manual, somente leitura e sem permissão de escrita**, sem publicar um PR parcial. A nuvem só volta a atualizar automaticamente como parte do gerador de pacote integral aprovado.

## 4. Testes e requisitos ainda pendentes

- `tests/test_mar_real_site_projections_b2.py`: paridade histórica real, manifesto de staging externo, restrição contra sobrescrita, preservação de ordens e lacunas curatoriais.
- `site/tests/scientific-build-gate.test.cjs`: adulteração de um relatório, arquivo extra, tentativa de publicar fichas indevidas, bypass de manifesto e baseline válido.
- `tests/test_mar_b2_synthetic_integration.py` do PR #124: admissão fictícia de 62 → 63 corpora, coerência transversal e rollback.

**Ainda necessário para B2 operacional:** incluir um corpus REAL após decisão científica documentada e atualização curatorial independente; recalcular todos os componentes afetados com o mesmo epoch, inclusive compatibilidade do piloto e registradores TypeScript se a quantidade de lotes crescer; revisão e integração dos PRs empilhados; configurar proteção de promoção Vercel e paridade funcional Streamlit → Next.js. O site não está autorizado para o público, e os corpora sob HOLD não recebem fichas/mídias.

**Ordem proposta de revisão:** PR #121 → #123 → #124 → #125. Nenhuma mudança direta em `main`, em metadados KAVI, no banco Neon, no Streamlit ou nas configurações de proteção da Vercel.
