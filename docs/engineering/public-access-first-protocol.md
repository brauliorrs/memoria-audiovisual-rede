# MAR — Protocolo obrigatório de descoberta do acesso público (antes de escolher o coletor)

**Versão:** 1.0.0 · **Data:** 13/10/2026  
**Relação com a metodologia:** complemento operacional de `docs/methodology/mar-scientific-methodology.md` e `docs/engineering/production-analysis-lifecycle.md`; não substitui protocolos científicos congelados nem autoriza novos instrumentos.

## Pergunta que comanda a investigação

> Por quais superfícies públicas uma pessoa pode encontrar, pesquisar, consultar ou visualizar informações de patrimônio audiovisual da instituição, e quais dessas superfícies admitem observação automatizada autorizada?

**NÃO começar procurando API, endpoint ou coletor.** Começar pelo objeto, pela instituição, pelas rotas publicadas e pela experiência observável de acesso. A interface web humana, a indexação por agregadores e a API são **canais distintos**, não alternativas mutuamente exclusivas.

### Ordem obrigatória para cada instituição

| Gate | O que investigar | Evidência mínima | O que não concluir |
|---|---|---|---|
| G0 — identidade e rotas | Site institucional e domínios de serviços oficiais/subordinados; rotas encontradas em links reais, não adivinhadas | URLs, vínculo institucional, datas, provenance | Host principal sem catálogo ≠ instituição sem catálogo |
| G1 — acesso pelo navegador | Catálogo especializado, motor de pesquisa pública, filtros, listas, fichas individuais, páginas de coleção e **agregadores** | URL de interface, percurso humano documentado, exemplo real de item, barreiras observadas | API falhou ≠ acesso público inexistente |
| G2 — natureza do acesso | Metadados visíveis, visualização em player, download, autenticação, diferenças de licença e custódia | Campo efetivamente observado + identificação da rota e responsável | Ficha ≠ vídeo; player ≠ permissão de download/reuso; índice em agregador ≠ custódia |
| G3 — viabilidade de coleta | Somente após G1/G2, verificar robots de **cada host**, termos, sitemap declarado, paginação da interface, exportações, feeds/OAI/IIIF, API documentada; verificar total/repetibilidade | Mecanismo de enumeração explicitamente descoberto, seus limites e resultados limitados, nunca tentativa em força bruta | Limite de enumeração ≠ indisponibilidade da fonte |
| G4 — decisão segregada | (a) acesso humano, (b) metadados, (c) mídia, (d) coleta automatizada autorizada, (e) cobertura/completude, (f) custódia/direitos, (g) admissão | Registro estruturado `docs/engineering/public-access-surveys/<unit_id>.json`, metodologia e aprovação humana | Não substituir ausência de teste por resultado negativo |

Em G1, visitar deliberadamente **todos** os tipos de superfície listados no registro, inclusive quando a API parecer suficiente. `not_assessed` ou limitação local impedem **encerramento definitivo de descoberta**, mas podem justificar um **HOLD provisório** de ingestão. Acesso por navegador, coleta automatizada e incorporação científica têm critérios independentes.

### Taxonomia de resultados de rota

- `observed_public`: houve acesso público efetivo e registrado (sem autenticação).
- `route_identified_unverified`: um link oficial foi encontrado, mas não houve teste de acesso real.
- `source_blocked`: bloqueio verificado no host/rota e no contexto registrado; não generalizar para todos os canais.
- `environment_limited`: DNS, sandbox, indisponibilidade de ferramenta ou infraestrutura do pesquisador impede a verificação; **NÃO** converter em fonte indisponível.
- `not_found_with_evidence`: rota/interface procurada sem evidência positiva; especificar percurso e escopo da busca, sem provar ausência institucional.
- `not_applicable_with_evidence`: tipo de rota justificadamente inaplicável ao serviço investigado.
- `not_assessed`: investigação ainda não executada — deve permanecer pendente.

**Fontes diferentes:** registrar separadamente `kavi.fi`, `elonet.finna.fi`, `finna.fi`, `api.finna.fi` (e qualquer outro host comprovado). A existência de catálogo Elonet não autoriza afirmar que sua enumeração é livre, nem substituir a inspeção de fichas pelo resultado da API. Para automatização, verificar `robots.txt` do host real, termos, não contornar 403/challenge e não adivinhar IDs.

### Critérios de decisão

- **PUBLIC_ACCESS_OBSERVED:** ao menos uma superfície humana pública comprovada e sua evidência. Admissibilidade ao corpus é **decisão separada**.
- **AUTOMATION_VERIFIED:** descoberta, permissão e ensaio limitado de um método de coleta com replay/contagem/proveniência pertinentes.
- **CORPUS_ADMITTED:** protocolo de inclusão próprio aprovado **fora deste inventário**; não decorre de `PUBLIC_ACCESS_OBSERVED`. O validador deste levantamento **rejeita** `decision=admitted`; a admissão é uma decisão controlada, independente.
- **AUTOMATION_VERIFIED requer evidências de quatro dimensões:** autorização de acesso/uso do endpoint (`authorization_evidence`), enumeração delimitada (`bounded_enumeration_evidence`), auditoria/replay independente (`replay_integrity_evidence`) e proveniência (`provenance_evidence`). Cada dimensão cita URL, data e observação revisáveis por humano. Endpoint publicamente alcançável **não** basta para declarar coletor verificado.
- **HOLD_INGESTION:** corpus não elegível neste momento; a investigação de superfícies pode seguir pendente com `investigation_complete=false`.
- **NO_PUBLIC_ACCESS_VERIFIED:** somente em escopo muito delimitado e após inspeção independente de rotas; nunca por falha de uma API ou do DNS local. Evitar afirmar indisponibilidade global.
- **PROCEED_NEXT:** permitir que a fila avance com um HOLD **provisório** protocolado, mesmo sem corpus admitido, desde que declare as superfícies examinadas, as não examinadas, seus motivos e a natureza não definitiva da conclusão. `environment_limited` em qualquer superfície, catálogo identificado mas não observado ou `human_public_access=unverified` proíbem marcar `investigation_complete=true` ou `hold_documented` final. Não chamar esse HOLD de ausência de acesso.

### Prevenção de viés de confirmação

Antes de decidir, responder e registrar as quatro perguntas de contraste:

1. **Hipótese alternativa:** Se a API não existisse, em qual site/catálogo um usuário normal encontraria o registro?
2. **Evidência contraditória:** Existe algum site secundário, busca, ficha ou agregador que refute a hipótese `sem acesso público`?
3. **Falha nossa ou da fonte?** DNS, seletor, parser, CI, permissões do runner e timeout são eventos do método até evidência em contrário.
4. **Qual é a afirmação máxima justificável?** Encontrabilidade de ficha, acesso a metadados, visualização, obtenção de mídia, permissão de reprodução e captura de corpus são seis afirmações diferentes.

Uma análise não deve consumir ciclos ilimitados tentando consertar a API se G1 sequer foi executado. Ao atingir um bloqueio técnico, retornar à descoberta de superfícies e decidir HOLD operacional de forma proporcional.

### Implementação e auditoria

O modelo estruturado está em `docs/engineering/public-access-surveys/TEMPLATE.json`; o validador `scripts/validate_public_access_survey.py` verifica **cobertura das classes, evidências e diferenciação dos estados**. Ele **não** testa automaticamente se URLs existem e não pode declarar descoberta efetiva apenas com um JSON preenchido: o revisor humano deve conferir URLs, páginas e vínculos reais.

Exemplo:

```bash
python scripts/validate_public_access_survey.py docs/engineering/public-access-surveys/TEMPLATE.json
# Esperado: INCOMPLETE, exit 2; não aprova um levantamento vazio.
```

Antes de fechar formalmente uma análise, registrar o inventário correspondente, executar o validador e arquivar a decisão na issue/PR. A transição para a próxima fonte não depende de promover todos os corpora; depende de **classificação honesta, investigação suficiente e documentação**.

### Correção retrospectiva nº 82 — KAVI/Finna

O trabalho anterior em `api.finna.fi` comprovou acesso a metadados, mas não substitui levantamento explícito de catálogo `elonet.finna.fi`, busca pública `finna.fi`, fichas e acesso por navegador. O PR #71 foi marcado **Draft** para evitar aprovação definitiva de HOLD antes de registrar esta lacuna. Este protocolo não muda o bloqueio de promoção: nenhum registro novo ou mídia é incorporado ao MAR. **Não tratar falha da API ou do runner como indisponibilidade institucional.**
