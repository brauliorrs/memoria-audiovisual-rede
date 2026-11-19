# MAR — Coerência das projeções científicas estáticas (18/11/2026)

## Decisão
O site Next.js continua com `output: "export"`, um único projeto Vercel `mar-public-site`, proteção de acesso preservada, sem consultas públicas diretas a Neon nem novas cobranças. **Uma coleta concluída ou um conector registrado não torna seus registros publicáveis.** O conteúdo derivado do Streamlit tem de acompanhar rigorosamente os snapshots científicos versionados.

## Contrato inicial implementado neste PR

1. `scripts/build_mar_site_research_projections.py` reconstrói, exclusivamente a partir de `data/output/`, as projeções agregadas `analytics-*.json`, `research-slices-*.json` e perfis de instituições `institution-profiles-*.json`. `--write` é execução explícita, revisável; sem a opção executa checagem de identidade por código e conteúdo, com falha segura diante de divergência.
2. O script compara integralmente os 62 relatórios por corpus e os recortes CSV de temas, plataformas e observações temporais, além dos dados institucionais e links de origem. Uma fonte nova não pode ser simplesmente adicionada à interface sem o registro coerente de inventário.
3. O Índice de Dados Públicos `public-access-observatory.json` possui notas de visita, direitos e estados G0/G1 revisados por humanos. O regenerador **nunca o sobrescreve**. Confronta as contagens históricas com as duas tabelas científicas originais, exige correspondência de unidades e mantém `recordDisplay=not_authorized_for_new_site`; se houver alteração, requer reconciliação curatorial independente antes da proposta de atualização.
4. `documented-cases.json` também não é regenerado automaticamente, pois suas decisões e evidências são interpretações documentais; o gate confirma publicação não autorizada e a origem das unidades citadas.
5. As fichas individuais KAVI usam outra autorização, com SHA-256 verificado pelo `scripts/check_mar_site_index.py`. O fluxo de projeção **não altera o catálogo KAVI nem os registros sob HOLD**. A nuvem de palavras continua exclusivamente agregada, com seu próprio teste de derivação.
6. `.github/workflows/mar-site.yml` passa a confrontar projeção e fonte antes do build. `.github/workflows/mar-site-projection-refresh.yml`, acionável manualmente, semanalmente ou após mudanças de fonte na `main`, recompõe conjuntamente os agregados, perfis e a nuvem de palavras, fixa o commit original por `scripts/pin_mar_site_research_snapshot.py` quando há atualização científica e abre **PR em rascunho sem automerge**. O workflow antigo `mar-wordcloud-refresh.yml` fica apenas manual, evitando PRs concorrentes. O bot aciona os testes necessários explicitamente porque PR criado com `GITHUB_TOKEN` não os dispara automaticamente; não altera banco, Streamlit, licenças ou proteção do Vercel.

## Gates obrigatórios para aceitar novo corpus

- **Ciência:** preservar corpus e observação originais, aprovar a incorporação científica em processo separado com evidência, testes e eventual restauração P0 quando aplicável.
- **Projeções:** todos os arquivos agregados atualizados na mesma revisão e invariantes verificados por corpus. Não misturar datas de observação de fontes diferentes. Evidências manuais de acesso só mudam com revisão explícita.
- **Publicação:** nenhuma mídia hospedada; metadados individuais somente com gates de direitos, revisão independente e manifesto apropriado. Índice histórico não é licença de reuso.
- **Homologação:** comparar números/tabelas/links e interface Streamlit versus Next.js, validar mobile e idiomas; conferir o SHA GitHub e deploy Vercel, ainda com acesso protegido.
- **Acesso público:** **último passo**, só após equivalência funcional, processamento de corpora, dossiê europeu e autorização humana expressa. `READY` não é lançamento.

## Limites e próximos reforços

Este é o primeiro contrato de **sincronização das projeções numéricas e institucionais**. Os registros de acesso e os 17 casos permanecem de atualização curatorial manual; não existe autorização de publicação em lote. Ainda faltam verificação E2E visual, uma trilha única de revisão de novos corpora com rebuild atômico e eventual configuração de Deployment Checks no Vercel, pois um check GitHub reprovado, isoladamente, não bloqueia necessariamente a implantação automática vinculada ao Git. Até essa garantia ser provada, a proteção SSO permanece indispensável.

A matriz de equivalência funcional permanece em `docs/engineering/mar-streamlit-vercel-functional-migration-matrix.md`; a memória canônica no Drive determina que o acesso público é a fase final.
