# MAR — entrada por catálogo central, descoberta KAVI e filtros documentais
Data: 17/11/2026. PR independente baseado em `main` (PRs #95/#98 integrados, Neon main e P0 em HOLD).

## Auditoria de causa
O leitor `load_published_kavi_rows(OUTPUT_DIR)` **já injeta as 200 fichas KAVI** em `build_research_video_catalog_frame`, com manifesto `published_partial_metadata`, `metadata_publication_approved=true`, `record_review_status=unreviewed`. A busca não exibe esses registros por padrão porque a caixa `Somente registros com link público de vídeo` é marcada inicialmente e remove `source_service=finna_api`, cujos links são apenas fichas. Navegação por dezenas de abas deixa a descoberta difícil. Não se deve inserir nova ficha ou tocar no CSV/manifesto aprovado.

## Mudança e contratos (pré-registrados)
1. O **catálogo central** vira landing page da UI; a extensa navegação institucional permanece acessível em modo secundário, sem suprimir relatórios.
2. Filtro de vídeos comprovadamente reproduzíveis fica **desligado por padrão** e, quando marcado, exige `media_access_status=verified_public_playback` e link de origem; nunca interpretar URL de ficha como prova de reprodução.
3. **Instituição** e **Situação documental** tornam-se filtros explícitos. Novos campos de projeção só para apresentação: legado = `Catálogo histórico · revisão não declarada`; KAVI = `Metadados publicados · cobertura parcial · ficha não revisada`; PR95 = `Metadados aprovados para publicação · mídia não verificada`. Não alegar que KAVI concluiu análise nº 82 ou que possui direitos de mídia.
4. Projeção KAVI usa **somente** o loader verificado por manifesto/SHA-256, transforma 200 registros em dados de catálogo (não vídeo incorporado), com `Finland`, `Finna / Elonet`, link HTTPS da própria origem e identificação estável, sem reprodução ou download.
5. Deduplicar por `(corpus normalizado, URL da ficha)` e `source_record_id` na camada KAVI; não eliminar itens distintos sem correspondência de identidade. Mantém dedup legado/admissão PR95.
6. Se KAVI falhar assinatura/contagem, permanecer fail-closed (zero fichas) e emitir aviso; não reaproveitar CSV bruto nem inventar catálogo aprovado. Metadados de acesso e curadoria visíveis por registro, sem falsas contagens.
7. Os painéis por unidade e a busca individual KAVI continuam disponíveis; nova UI não dispara coletor, backup, acesso Neon ou P0.

## Testes antes de merge
- A: índice publicado existente 200/200, manifesto parcial e zero reprodução verificada;
- B: correspondência de filtro "KAVI"/instituição e 200 fichas em modo global, sem marcação de "somente reprodução verificada";
- C: ao ativar "somente reprodução verificada", KAVI e fichas não verificadas ficam excluídas;
- D: filtro documental distingue KAVI parcial, PR95 metadata only e legado, sem elevar aprovação científica;
- E: dedup por ID e URL; KAVI inválido não entra;
- F: app abre no catálogo central, abas ficam secundárias e recuperáveis;
- G: CI `quality` em SHA final e depois em `main`;
- H: nenhuma migração, coletor, SECRET, media/player, new CSV ou mudança no P0.

Rollback: reverter import/projeção de pesquisa e controles de navegação; nenhuma mutação de estado ou metadados aprovados. Só fazer merge com CI verde e rule `quality` ativo.
