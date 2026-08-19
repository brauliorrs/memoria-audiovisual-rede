# Roteiro de validação da inteligência do MAR e das dimensões de IA

## Objetivo

Este documento organiza a ordem científica e operacional das validações relacionadas à automação e à IA no **Memória Audiovisual em Rede (MAR)**. Ele não cria novos indicadores nem altera o baseline oficial. Seu objetivo é impedir que três objetos distintos sejam confundidos:

1. **inteligência/automação utilizada pelo próprio MAR** para localizar, classificar, priorizar e expor evidências;
2. **IA utilizada pelas instituições observadas** em atividades relacionadas aos seus acervos audiovisuais;
3. **IA utilizada na produção ou modificação de conteúdos audiovisuais** pertencentes aos acervos observados.

A ordem de desenvolvimento e validação é sequencial: primeiro o MAR precisa observar corretamente as superfícies e unidades do corpus; depois as dimensões institucionais e de conteúdo podem ser extraídas sobre esse universo observado.

## Ordem de prioridade

### Camada 0 — núcleo observacional do MAR

**Prioridade atual.**

O MAR precisa demonstrar que consegue, de forma auditável e reproduzível:

- executar os corpora ativos;
- materializar snapshots, proveniência e evidências;
- preservar URLs e estados de acesso;
- distinguir instituição, superfície de acervo, página geral, índice, registro, item, versão e segmento;
- identificar e expor superfícies públicas relevantes;
- manter histórico longitudinal sem sobrescrever observações anteriores;
- publicar apenas produtos derivados aprovados.

Esta camada é pré-condição para interpretações científicas posteriores.

### Camada 1 — inteligência/automação do MAR

**Em andamento e prioridade de validação.**

No código, parte dessa camada aparece como `observatory_ai_triage`. A expressão metodológica preferida é **inteligência/automação do MAR**, porque os mecanismos atuais podem ser regras determinísticas, heurísticas ou modelos de IA.

Funções centrais:

- detectar sinais de acervo audiovisual;
- detectar presença de vídeo público;
- reconhecer o tipo de superfície observada;
- distinguir página geral de item audiovisual;
- localizar candidatos em nível de item;
- priorizar evidências para revisão humana;
- apoiar, sem substituir, decisões curatoriais.

Os resultados desta camada medem a capacidade metodológica do observatório. Eles **não são resultados sobre adoção de IA pelas instituições**.

## Validações da Camada 1

### M1 — detecção de acervo audiovisual

Pergunta: o MAR identifica corretamente que a superfície ou instituição apresenta evidência observável de acervo audiovisual?

Estado: **em andamento**.

### M2 — detecção de vídeo público

Pergunta: o MAR identifica corretamente sinais de vídeo publicamente observável?

Estado: **em andamento**.

### M3 — resolução de superfície e unidade

Pergunta: a URL candidata corresponde ao tipo de unidade que o MAR atribuiu a ela?

A primeira versão conservadora da tipagem foi implementada em `src/memoria_audiovisual/digital_infrastructure/surface_typing.py`. O vocabulário operacional mantém distintas as classes:

- `homepage`;
- `institutional_landing_page`;
- `archive_landing_page`;
- `search_or_index`;
- `news_or_editorial`;
- `item_record`;
- `audiovisual_item`;
- `restricted_or_unavailable`;
- `unknown`.

Somente `item_record` e `audiovisual_item` são classes item-level. Um vídeo incorporado em página geral não é suficiente para transformar a superfície em item audiovisual. Bloqueios, erros de acesso e ambiguidades também permanecem separados de classificações negativas.

O gerador `scripts/build_surface_type_review_queue.py` produz dois artefatos separados: previsões automáticas e fila cega de revisão humana. O revisor não recebe a previsão do mecanismo durante a anotação. Os testes controlados e o workflow `Quality Checks` passaram integralmente em 19 de agosto de 2026.

Estado: **implementado estruturalmente; validação humana empírica em andamento**.

### M4 — resolução de candidato em nível de item

Pergunta: quando uma tarefa exige um item audiovisual, o gerador entrega de fato uma URL de item, versão ou segmento, em vez de uma página geral?

Estado: **em andamento**.

A primeira revisão manual da fila `ai-archive-two-gate-candidates-v1` mostrou dois candidatos e ambos falharam neste primeiro teste de elegibilidade:

- ECPAD: a URL candidata era uma página geral de arquivos;
- INA: a URL candidata era uma página institucional/principal com links para outras áreas do acervo.

Interpretação: **0/2 URLs candidatas eram unidades audiovisuais elegíveis em nível de item**. Esse resultado não permite inferir ausência de IA, ausência de acervo ou falha das instituições. Ele revela uma limitação de resolução/seleção de URL no gerador de candidatos e orienta o próximo aperfeiçoamento da inteligência do MAR.

### M5 — pertencimento ao corpus

Pergunta: um item identificado pertence efetivamente ao corpus/acervo observado e materializado pelo MAR?

Estado: **em andamento**. Não foi alcançado pelos dois candidatos da primeira revisão porque ambos falharam em M4.

### M6 — observabilidade pública do item

Pergunta: a superfície pública específica do item permanece acessível e avaliável no momento da observação?

Estado: **em andamento**. Não foi alcançado pelos dois candidatos da primeira revisão.

## Camada 2 — IA institucional

**Em andamento. Não priorizar ativação científica antes da consolidação das Camadas 0 e 1.**

Pergunta científica:

> Há evidência pública verificável de que a instituição utiliza IA ou aprendizado de máquina em uma função concreta relacionada ao acervo audiovisual?

A unidade de observação pode ser uma instituição, projeto, sistema, serviço ou processo. A evidência pode estar em páginas internas, documentação, relatórios, notícias institucionais, projetos, APIs ou outras superfícies públicas pertinentes; ela não precisa estar na homepage nem em uma ficha audiovisual.

Funções possíveis incluem transcrição automática, reconhecimento de fala ou imagem, OCR, enriquecimento de metadados, classificação, restauração, recomendação, busca, tradução, direitos e outras funções definidas no protocolo de sistemas de IA.

Regras:

- uma menção genérica a IA não prova uso institucional;
- ausência de detecção não prova ausência institucional;
- o procedimento precisa declarar quais superfícies foram examinadas;
- positivos exigem evidência pública verificável e revisão humana;
- projeto de pesquisa, piloto e operação devem permanecer distintos.

Estado: **em andamento**.

## Camada 3 — IA na produção ou modificação de conteúdo audiovisual

**Em andamento. Não ativada como indicador científico.**

Pergunta científica:

> Há evidência verificável de que IA participou da produção ou modificação de um item, versão ou segmento audiovisual pertencente ao corpus observado?

### C1 — Porta 1: identificação terminológica/contextual

Objetivo: reconhecer evidência textual, estruturada ou técnica de participação de IA na produção ou modificação audiovisual.

Estado: **validada para a versão atual do protocolo**, exclusivamente como mecanismo de identificação terminológica/contextual. Essa validação não demonstra presença de IA em nenhum acervo.

### C2 — Porta 2: confirmação no acervo observado

A Porta 2 é sequencial e só produz ocorrência positiva quando todas as condições são satisfeitas:

1. a URL representa item, versão ou segmento audiovisual elegível;
2. o item pertence ao corpus observado;
3. existe superfície pública específica e acessível;
4. a evidência de IA está inequivocamente vinculada àquele item.

Estado geral: **em andamento**.

Na primeira revisão manual, somente a primeira condição foi efetivamente testada, porque os dois candidatos falharam nela. As condições de pertencimento, acesso e vínculo da evidência permanecem em andamento.

### C3 — classificação do papel da IA

Classes operacionais atuais:

- `ai_assisted_production`;
- `materially_ai_modified`;
- `partially_synthetic`;
- `fully_synthetic`;
- `no_verified_ai_evidence`;
- `not_assessable`.

Estado: **em andamento para validação em itens reais do corpus**. A calibração terminológica existente não substitui validação ecológica em itens efetivamente observados pelo MAR.

## Estado consolidado

| Bloco | Validação | Estado |
|---|---|---|
| Núcleo MAR | execução, snapshots, proveniência, superfícies e exposição | **em andamento — prioridade atual** |
| Inteligência/automação MAR | M1 detecção de acervo | **em andamento** |
| Inteligência/automação MAR | M2 detecção de vídeo público | **em andamento** |
| Inteligência/automação MAR | M3 tipo de superfície/unidade | **implementado estruturalmente; validação humana em andamento** |
| Inteligência/automação MAR | M4 candidato real em nível de item | **em andamento; primeira revisão 0/2** |
| Inteligência/automação MAR | M5 pertencimento ao corpus | **em andamento** |
| Inteligência/automação MAR | M6 observabilidade pública do item | **em andamento** |
| IA institucional | evidência pública de uso institucional ligado ao acervo | **em andamento** |
| IA no conteúdo | C1 Porta 1 terminológica/contextual | **validada para o protocolo atual** |
| IA no conteúdo | C2 Porta 2 completa | **em andamento** |
| IA no conteúdo | C3 classe de participação da IA | **em andamento** |

## Decisão de prioridade após a primeira revisão da Porta 2

A primeira revisão da Porta 2 não será tratada como falha metodológica nem como resultado negativo de IA. Ela demonstrou que o gerador atual pode selecionar uma URL geral presente em um registro materializado mesmo quando a tarefa posterior exige uma unidade audiovisual em nível de item.

A prioridade passa a ser melhorar e validar a **inteligência/automação do MAR na resolução de superfícies e unidades**, antes de ampliar a validação de IA institucional ou repetir a Porta 2 em escala.

As demais dimensões permanecem **em andamento**, preservando seus artefatos, decisões e protocolos já produzidos.

## Próximo portão

A próxima etapa é materializar uma **amostra real e cega de superfícies públicas** a partir da exploração controlada do MAR e revisar humanamente a tipagem. A amostra deve conter páginas institucionais, entradas de acervo, índices/buscas, páginas editoriais, fichas de item, itens audiovisuais e casos não avaliáveis quando existirem.

Antes de uma nova rodada de IA institucional ou de IA em conteúdo, o MAR deve demonstrar em amostra humana que consegue:

1. distinguir páginas gerais de fichas de item;
2. localizar URLs específicas de itens quando elas existem;
3. registrar corretamente casos em que não existe superfície específica acessível;
4. manter a ligação entre item, corpus, URL, evidência e snapshot;
5. expor esses estados sem transformar não detecção em ausência.

Somente depois dessa validação a expansão das Camadas 2 e 3 deve voltar a ser prioridade científica.
