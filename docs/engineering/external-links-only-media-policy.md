# MAR — entrega de acesso audiovisual por links externos

**Decisão de arquitetura, 13/10/2026:** MAR é um observatório e índice de metadados e rotas públicas, **não** uma plataforma de hospedagem, espelhamento ou distribuição de arquivos audiovisuais.

## Finalidade científica e relação com as instituições

**Decisão explícita da coordenação:** o MAR é uma plataforma de **estudo, descoberta, integração intelectual, contextualização e análise comparativa** de acervos audiovisuais dispersos. A instituição ou a plataforma responsável pelo conteúdo deve receber **a visita, o acesso e a visualização**. Não é objetivo do MAR atrair ou contabilizar visualizações que caberiam aos portais de origem, centralizar players, agregar audiências ou se apresentar como titular das obras.

### Política de encaminhamento do visitante

- Sempre que houver ficha estável da **obra** na instituição, preferi-la ao arquivo de mídia ou a um agregador intermediário. A ficha de origem deve exibir o contexto, os créditos e as condições de acesso.
- Quando houver uma página própria de vídeo no canal oficial da instituição (por exemplo, YouTube/Vimeo), o botão pode abrir **aquela página externa**, sem iframe ou reprodução incorporada ao MAR.
- Quando o único campo capturado for um endereço direto de arquivo/stream (MP4, WebM, HLS/M3U8, DASH/MPD etc.), **não usar esse arquivo como botão de visualização**. Se existir uma página institucional verificável, oferecer "Visitar catálogo da instituição" e declarar que a ficha específica ainda não foi identificada. Se não houver destino institucional confiável, não inventar URL ou afirmar que há vídeo acessível.
- O link direto para o arquivo pode continuar **preservado como evidência técnica no conjunto de metadados sujeito a controles de acesso e direitos**, mas deve ser distinguido de `record_page_url` e do destino público de navegação. A transformação HTTP/HTTPS (por exemplo, codificar espaços) afeta apenas o destino derivado, jamais altera a URL-fonte no registro científico.
- Atribuir instituição, plataforma, proveniência e data da última observação. O MAR não reivindica direitos sobre obras indexadas e não altera as condições estabelecidas pelos titulares.
- Links externos reduzem questões de hospedagem e redistribuição, **mas não eliminam automaticamente todas as obrigações de direitos autorais, licenciamento de metadados e privacidade**. Cada fonte continua sujeita ao respectivo protocolo.
- O MAR pode estudar e contar **registros, links e indicadores científicos**, sem confundir tais métricas com visualizações de vídeo. Não fazer proxy, embeds, redirects com tracking obrigatório nem fetch de mídia para medir audiência.

## Princípio operacional

1. **Coletar:** páginas, metadados descritivos, URLs, identificadores, informações de acesso, hashes e evidências técnicas limitadas, conforme escopo autorizado/robots/termos. Quando permitido e necessário para auditoria, snapshots de respostas **textuais** podem ser preservados sob acesso restrito; não são arquivos audiovisuais.
2. **Armazenar:** índice estruturado de metadados, URL canônica de ficha/permalink quando houver, URL de acesso ao player na origem se documentada, instituição, plataforma, tipo de acesso (descritivo, streaming livre, autenticado, pago, geobloqueado, indisponível), data/hora de observação e proveniência.
3. **Apresentar:** resultados paginados ou filtrados e botão **abrir na instituição/plataforma de origem**. Nunca pré-carregar players, fazer proxy, servir vídeos, transferir streams, embutir iframe externo, copiar thumbnails de origem ou efetuar download de bytes de mídia para o MAR.
4. **Exportar:** CSV/JSON de metadados (incluindo links) continuam permitidos e separados de conteúdo audiovisual. Evitar dados pessoais e os campos sujeitos a licenças restritivas.
5. **Verificar:** validade das rotas, redirects, mudança de conteúdo e desaparecimentos devem ser observados em **sondas de metadados/HTTP autorizadas**, sem solicitar bytes de arquivos de vídeo. O status declarado no MAR corresponde à última observação, nunca garante que o vídeo segue disponível no momento do clique.
6. **Proveniência:** indexação por agregador não prova custódia do item; a URL da ficha institucional deve ser preferida em relação a uma URL de MP4 ou recurso transitório com token. Registrar `record_page_url`, `access_url` e `media_asset_url` como papéis separados se existirem, e **nunca** expor links de mídia assinados/efêmeros como permalink.
7. **Condições de acesso:** um link externo pode apontar para ficha apenas descritiva, player restrito, vídeo público, login ou paywall; não afirmar `vídeo disponível` somente porque um campo `video_link` está preenchido. Um vídeo embutido in-app também pode causar transferência de mídia no navegador do usuário; evitar.
8. **Segurança:** links externos somente com esquema HTTP/HTTPS e sem credenciais; não renderizar URL não confiável como Markdown interpolado ou HTML. Não seguir redirects para contornar login, paywall ou proteção anti-bot.

## Auditoria de implementação (estado em main antes deste PR)

- `app/streamlit_app.py` já fornece `[Abrir vídeo](...)`, link para a instituição e catálogo textual filtrável; CSV/JSON são **metadados**.
- **Desvio localizado:** `st.video(row["video_link"])` em YouTube e `components.iframe(...)` em Vimeo, ambos na ficha institucional, criam reprodução dentro do observatório. Não comprova hospedagem pelo MAR, mas contradiz a navegação estritamente por links.
- Coletores amostrados: `ina.py`, `euscreen.py`, `europeana.py`, `aapb.py`, `iwm_film.py`, `kavi_finna_adapter.py`. As rotinas inspecionadas geram metadados e URLs, sem encontrar instruções de download de arquivos audiovisuais. **Esta amostra não é auditoria estática exaustiva dos ~60 corpora ativos**.
- O README descreve snapshot público de aproximadamente **277 MB**. Não é prova de arquivos audiovisuais hospedados: representa a massa de artefatos/dados públicos reportada pelo projeto. Ainda assim, gera risco de custo de inicialização e carga do Streamlit; link-only não resolve sozinho o peso dos metadados.

## Alteração deste PR

A ficha institucional deixa de chamar `st.video` e `components.iframe`. Em vez disso, abre um link externo validado (HTTP/HTTPS), com indicação de que o destino pode exigir autenticação ou ter condições de direito próprias. O restante da coleta e as métricas permanecem intocados. `tests/test_external_links_only.py` proíbe novos players e testes de URL impedem esquemas inseguros. A exportação CSV/JSON de metadados é preservada.

## Aperfeiçoamento de encaminhamento institucional

O contrato `choose_origin_destination` define `record_or_platform` para ficha/página de vídeo pública segura, `institution_home` quando há apenas arquivo de mídia e existe endereço institucional de fallback, e `unavailable` quando não é possível apontar um destino de consulta confiável. A identificação de mídia direta inclui extensões no caminho, nomes de arquivo em parâmetros de consulta, as rotas específicas `cna.kiss.lu/getMedium/<hash>` e `prod.media.memobase.ch/memo/<id>` e um campo MIME explícito quando disponível. Para Cinémémoire, o campo de proveniência `partner_site` frequentemente aponta uma ficha `notice?num_seq=<id>`; esse registro **prevalece** sobre a página genérica do catálogo. Em Cinémathèque suisse, o `partner_site` pode apontar um registro de metadados na API pública Memobase, **não um player público confirmado**. O botão nunca deve prometer disponibilidade de vídeo a partir de um localizador técnico. **Não inferir MIME de descrições textuais livres**, pois podem apenas citar o formato de um audiovisual que tem ficha pública. O estado `institution_home` **não significa que a obra esteja disponível naquele catálogo**. O próprio painel sinaliza a ausência de ficha específica.

Os modos de consulta por tema e por instituição usam links derivados (páginas da plataforma ou catálogo institucional); o CSV/JSON e o registro científico preservam o campo original de descoberta separado da experiência de clique. Assim, o visitante não é encaminhado a um arquivo MP4 isolado, e o histórico bruto de evidência não é apagado.

## Melhorias incrementais posteriores (não incluídas neste PR)

- Padronizar todas as colunas URL do catálogo com `st.column_config.LinkColumn` e normalização HTTP/HTTPS antes de renderizar; priorizar **fichas originais permanentes** em relação a streams diretos.
- Criar contrato por registro com `source_record_url`, `platform_url`, `access_url`, `access_status`, `last_checked_at`, `link_health`, `evidence_url` e `rights_status`, incluindo `unknown` e restrições. Não converter inferências em confirmação.
- Auditoria estática do repositório inteiro + teste CI contra escrita binária de vídeo, extensões `.mp4`, `.webm`, `.mov`, `.mkv` e downloads diretos de media URLs. APIs textuais e seus snapshots seguem permitidos.
- Performance: perfilar carregamento dos atuais CSVs/snapshots, aplicar cache discriminado por versão, leitura seletiva por colunas, paginação de resultados e eventual índice leve por corpus. **Evitar presumir que o snapshot de 277MB está sendo integralmente carregado a cada visita** antes de medir.
- Monitoramento ético de links quebrados com baixa frequência, diferenciando 403/429, falhas locais de DNS, links removidos e rotas que exigem sessão; nunca contornar proteções nem alegar indisponibilidade institucional sem evidência.

**Resultado desejado:** MAR tem papel de **índice de descoberta, contextualização e pesquisa**; o arquivo audiovisual permanece e é acessado na plataforma de origem, conforme condições do custodiante.
