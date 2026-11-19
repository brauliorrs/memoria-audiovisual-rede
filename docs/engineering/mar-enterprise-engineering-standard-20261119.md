# MAR — padrão obrigatório de engenharia para F01–F13

**Vigência pretendida:** 19/11/2026, após revisão/merge. **Dono do estado da fila:** [issue #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128). **Manifesto verificável:** [mar-implementation-stage-gates.json](mar-implementation-stage-gates.json). **Situação inicial:** F00 concluída; somente F01 ativa; F02–F13 bloqueadas.

## Propósito

Estabelecer um SDLC uniforme inspirado em NIST SSDF, OWASP ASVS, engenharia de releases, SRE e métricas DORA, sem prometer certificação/conformidade integral e sem contratar novos serviços. O controle serve à engenharia e à integridade das decisões científicas, que **não** são realizadas pelo CI.

Fontes: [NIST SP 800-218 SSDF](https://csrc.nist.gov/pubs/sp/800/218/final), [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/), [Google SRE Release Engineering](https://sre.google/sre-book/release-engineering/), [DORA](https://dora.dev/). Preservar também as políticas existentes: [quality-hardening](quality-hardening.md), [release-policy](release-policy.md), [release-checklist](release-checklist.md) e [produção científica](production-analysis-lifecycle.md).

## Fluxo obrigatório por etapa

| Gate | Momento | Evidência mínima exigida | Responsável pela decisão |
|---|---|---|---|
| G0 — Ready | Antes da implementação | ID ativo; finalidade; baseline SHA; inventário de impacto; contratos; riscos de dados, direitos e segurança; testes e rollback desenhados | Revisão técnica |
| G1 — Implementação | Durante a etapa | PR de escopo único, alteração mínima, contratos e testes versionados; sem efeito colateral em corpora, Neon principal ou acesso público | Autor e revisor de código |
| G2 — Verificação técnica | Antes da conclusão | Testes positivos e adversariais, lint/tipos no escopo, CI na revisão exata, provas de reprodutibilidade, acesso negado e rollback | CI + revisão das evidências |
| G3 — Aceite funcional | Depois dos testes | Fluxo real ou ensaio controlado demonstrado, critérios da matriz cumpridos, divergências resolvidas e documentação atualizada | Revisor humano da funcionalidade |
| G4 — Revisão científica/curatorial | Quando a etapa afeta método, corpus, indicadores, evidências ou direitos | Revisão humana independente documentada no escopo apropriado; manutenção de HOLD quando faltam provas | Responsável científico/curatorial, independente do CI |
| G5 — Encerramento operacional | Depois de G0–G4 aplicáveis | PR revisado e integrado, SHA, testes, risco residual, rollback, observabilidade, registro na issue #128 e próximo gate desbloqueado | Revisor humano da etapa |
| G6 — Autorização pública | Somente F13 | Autorização expressa do responsável, revisão de direitos/segurança e versão exata do deploy | Responsável do projeto; jamais CI |

**Regras inegociáveis:** teste verde significa somente teste verde; merge significa código integrado; uma tela existente não significa equivalência funcional; homologação técnica não concede validação científica; acesso público a catálogo de terceiros não concede licença de redistribuição; manifesto estático aprovado não libera mídia. A separação fica registrada como decisões distintas.

## Definition of Ready — antes de codificar

1. Conferir main no SHA exato e issue #128, mantendo apenas a primeira etapa não concluída em estado active ou hold.
2. Registrar matriz ALTERAÇÃO → COMPONENTES IMPACTADOS → EFEITOS INDIRETOS → TESTES → ROLLBACK; discriminar Python, Streamlit, Neon, projetores, Next.js, CI, direitos e proteção Vercel.
3. Definir pré-condições, entradas, saídas, erros, regras de idempotência, invariantes, decisões humanas e condições de HOLD.
4. Escrever plano de testes positivos, negativos, de integração, limites e rollback. Testes devem preceder ou acompanhar código de produção alterado.
5. Explicitar a não mudança: congela corpora e instrumentos científicos, credenciais, status de publicação, Vercel SSO e serviços pagos fora do escopo.

## Definition of Done — para marcar qualquer F01–F13 como completed

1. PR e diff revisáveis e rastreados por SHA; artefatos de engenharia na main.
2. Matriz de impacto, contratos e estado de migração atualizados.
3. Suite pertinente de testes positivos **e negativos** concluída no commit exato e sem ocultar testes falhos.
4. Aceite funcional independente de CI registrado como decisão humana.
5. Plano e ensaio de reversão adequado ao risco anexados.
6. Revisões extras de segurança, banco, recuperação, acessibilidade, cientificidade ou curadoria quando exigidas pela etapa.
7. Links rastreáveis e revisão do que permanece em HOLD, sem promoção implícita de instrumento, corpus ou fichas.
8. Checkpoint da issue #128 com evidência de PR/CI/revisão e status da próxima etapa.
9. **Para F13 somente:** autorização expressa e específica de abertura pública; a área administrativa deve continuar protegida.

## Implementação do bloqueio estrutural no CI

O manifest mar-implementation-stage-gates.json apresenta todas as 14 etapas, seus estados, freeze de funcionalidades e flag de acesso público. scripts/check_mar_implementation_queue.py valida a ordem sequencial e rejeita avanço sem os anexos mínimos por etapa; tests/test_mar_implementation_queue.py inclui casos adversariais. O workflow Quality Checks executa o validador com --check-pr e os testes offline antes de instalar dependências.

Todo pull request **enquanto houver uma etapa ativa** deverá declarar **uma única linha** no corpo: `MAR-STAGE: F01` (substituindo pelo estágio ativo na data do PR). O **PR de encerramento de F01 (ou qualquer etapa intermediária)**, quando o manifesto aponta para a próxima etapa ativa, precisa declarar exatamente duas linhas consecutivas: `MAR-STAGE: F01` e `MAR-TRANSITION: F01->F02` (substituindo os IDs sequenciais). O validador confere que a etapa encerrada possui todos os gates exigidos e que a próxima é a imediatamente seguinte; um marcador isolado não conclui a etapa. A própria PR de encerramento F13 pode conservar `MAR-STAGE: F13` quando o manifesto passa a `active_stage: null`. **Depois de F13**, PRs novos passam a usar `MAR-QUEUE: COMPLETE`. A revisão humana da veracidade das evidências permanece obrigatória. O CI rejeita ausência, duplicação, marcadores inválidos e tentativa de referenciar etapas futuras. Este marcador não prova que o código está realmente em escopo: a revisão humana inspeciona o diff.

Os testes adversariais usam **fixtures fixas da fila F01** e casos sintéticos inteiramente evidenciados de avanço F02–F13, enquanto um teste separado verifica o manifesto real. Assim o avanço legítimo da fila não quebra falsamente o CI; a validade da fila real continua obrigatória.

Cada evidência de conclusão deve estar associada a um documento ou execução rastreável no GitHub, SHA completo, resultado e ator identificável. Os gates manuais exigem reviewed_by humano e result accepted, nunca github-actions, bot ou automation. O script verifica forma e ordem; **não é assinatura criptográfica de autoria, não visita links, nem aprova cientificamente o conteúdo**. A autenticidade de evidências, independência efetiva de revisores e adequação metodológica dependem de revisão humana/controle de acesso no GitHub.

O status humano é mantido na issue #128. O manifesto versionado representa o gate executável correspondente. Em toda transição, atualizar ambos no mesmo PR/checkpoint e verificar concordância; falta de concordância mantém HOLD.

## Gates extras por etapa

| Etapa | Prova específica obrigatória além de impacto, contratos, testes positivos/negativos, aceite humano, rollback e revisão |
|---|---|
| F01 | Matriz de migração com equivalência rastreável e seus bloqueios de direitos |
| F02 | Revisão de segurança e restauração independente em ambiente isolado |
| F03 | Revisão de segurança e privilégios separados no Neon |
| F04 | Revisão do escopo científico e integridade do ledger de admissão |
| F05 | Revisão do escopo científico, hashes/denominadores e pacote atômico |
| F06 | Revisão de escopo científico e prova de que execução não é autorização de publicação |
| F07 | Revisão de segurança, acesso negado e ausência de segredos ao cliente |
| F08 | Observabilidade, defasagem de epoch e falhas registradas |
| F09 | Acessibilidade e revisão PT/EN/ES nos fluxos migrados |
| F10 | Revisão científica/curatorial por instituição; HOLD preservado sem prova |
| F11 | Revisão científica, de segurança e do deploy privado exato |
| F12 | Revisão científica, matriz completa e prontidão para recuperar versão anterior |
| F13 | Autorização expressa do usuário, revisão de direitos, segurança e deploy |

## Garantias e limitações

- **Fail-closed na revisão:** o CI deve falhar se o manifesto, a ordem, os anexos ou o marcador do PR estiverem incorretos. PRs existentes que não tiverem o marcador precisam ser adequados antes de nova integração.
- **Sem certificação automática:** checks verdes são necessários, mas insuficientes para conclusão técnica, funcional ou científica. Nenhum campo aprovado pelo script concede direitos a uma fonte.
- **Sem alteração de produção nesta adoção:** documentos, testes e workflow; Neon principal, Vercel SSO, site, Python científico e corpora inalterados.
- **Sem falso bloqueio de trabalho científico:** durante a fila não se incorpora novo corpus; após a fila, o ciclo científico mantém gates específicos, em vez de ser aprovado por estado de deploy.
- **Medição:** iniciar registros de falhas, tempo de recuperação e lead time quando houver evidência operacional real; não inventar SLO ou taxa de sucesso.

## Aplicação imediata

F01 continua em execução. O próximo ato é fechar a matriz por fluxo com caminhos de implementação, testes e evidências; somente após PR revisado e aceite humano poderá ser marcada completed, iniciando F02. A proteção pública da Vercel permanece ativa.
