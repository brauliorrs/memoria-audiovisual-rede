# MAR — KAVI/Kuvi #82: mapa de subdivisões, acesso público e função documental

**Data da observação:** 2026-10-15  
**Status:** descoberta institucional documentada; **HOLD provisório de admissão**, sem coleta de mídias e sem prova de enumeração exaustiva.  
**Unidade institucional:** Finnish Arts and Culture Agency (Kuvi), sucessora das atribuições de KAVI (National Audiovisual Institute) e SEA. O identificador histórico de pesquisa `fiaf-kavi` não representa necessariamente a denominação legal atual.

## Erro metodológico que este levantamento corrige

A URL institucional [Film Archive](https://kavi.fi/en/elokuva-arkisto-2-2/) apresenta **sete links de serviços**. Eles são *subdivisões de navegação do setor de filmes*, **não necessariamente sete acervos custodiais nem sete corpora independentes**. A presença do catálogo Elonet jamais pode esgotar a inspeção do KAVI/Kuvi. A infraestrutura Finna hospeda serviços diferentes, e o mesmo filme pode aparecer em mais de um serviço.

| Serviço ligado a Film Archive | Superfície / vínculo oficial | Função documentada e acesso observado | Tratamento no MAR |
|---|---|---|---|
| **Elonet** | https://elonet.finna.fi/ ; https://kavi.finna.fi/Content/faq?lng=en-gb | Filmografia e video-on-demand; itens podem ter apenas metadados se os direitos não permitirem exibição. A página institucional e a FAQ indexada confirmam sua função. A navegação direta na raiz Elonet retornou 403 **neste ambiente**, mas links efetivos de Elokuvapolku abriram as fichas [Vaimoke (1936)](https://elonet.finna.fi/Record/kavi.elonet_elokuva_117938) e [Mieheke (1936)](https://elonet.finna.fi/Record/kavi.elonet_elokuva_118019). Isso confirma acesso humano a registros específicos, não enumeração do catálogo. | Candidato a registros de obras: examinar busca, ficha/permalink, diferença entre *catalogado* e *disponível online*. Não inferir indisponibilidade nem coleta permitida. |
| **Elävä muisti** | https://elavamuisti.fi/ ; https://kavi.finna.fi/elavamuisti/Content/faq | Serviço editorial de memória audiovisual: documentários, cinejornais, filmes publicitários e ficção; reúne ativos de Film Archive e de Radio and Television Archive. A FAQ registra migração ao Finna em **01/12/2021**. Redirecionamento para www e acesso direto bloqueados neste ambiente. | Candidato a descoberta **curatorial** e páginas de conteúdo audiovisual; conferir se seus itens reapontam ao mesmo registro Elonet e evitar duplicidade de corpus. |
| **Kino Regina** | https://kinoregina.fi/ | Cinema presencial, agenda de sessões, mostras e programação; site público aberto. | Fonte de programação/contexto expositivo; não promover uma sessão a registro audiovisual custodiado. |
| **Bio Valentin** | https://kavi.fi/en/film/bio_valentin/ | Cinema interno em Kaikukatu com 44 lugares, sessões e eventos; página pública aberta. | Serviço presencial; não tratar página do cinema como coleção digital. |
| **Regional Film Series** | https://kavi.fi/en/aluesarjat/ | Circuito de exibições em **oito cidades**, programação sazonal; página pública aberta. | Contexto cultural/programação; não incluir sessões como obras sem identificação da ficha da obra. |
| **Film Education** | https://kavi.fi/en/elokuvakasvatus-2/ | Página institucional de educação cinematográfica; aponta para Elokuvapolku e Elävä muisti. | Contextualização educativa, não corpus autônomo. |
| **Elokuvapolku** | https://elokuvapolku.kavi.fi/ ; https://elokuvapolku.kavi.fi/katso-elokuvia/ | Portal público educativo com trechos, filmes integrais, documentários, publicidade e materiais didáticos. Parte do catálogo é livre; outras obras exigem credenciais solicitadas para usos educativos. Página e listagem públicas abertas. | Candidato a fichas/trechos e perspectivas de análise fílmica, com classificação de acesso por obra; separar *trecho* de *longa* e cruzar os registros do Elonet. |

**Evidências primárias:** menu institucional e descrição geral (https://kavi.fi/en/elokuva-arkisto-2-2/); descrição do acervo online e do atual gestor (https://kavi.fi/en/film/); atribuições do Elävä muisti e do Elokuvapolku (https://kavi.fi/en/elokuvakasvatus-2/); FAQ indexada do Elävä muisti (https://kavi.finna.fi/elavamuisti/Content/faq); FAQ do Elonet (https://kavi.finna.fi/Content/faq?lng=en-gb); restrições específicas de filmes escolares (https://elokuvapolku.kavi.fi/katso-elokuvia/). Conferência realizada em 2026-10-15; alguns destinos são observados diretamente por leitura, outros somente por documento institucional/índice de busca; NÃO confundir os dois.

## Área adicional, fora destas sete entradas: Rádio e Televisão

A navegação institucional possui **Radio and Television Archive (RTVA)** como **outra área** (https://kavi.fi/en/radio-and-television-archive/). A base pública [Ritva](https://rtva.kavi.fi/) permite pesquisa de dados de programas, canais e acervos. O próprio órgão esclarece que as gravações completas podem ser ouvidas/assistidas em **pontos de consulta autorizados**, não em reprodução doméstica pela internet: https://kavi.fi/radio-ja-televisioarkisto/ohjelmien-katselu-ja-kuuntelu/ . Assim, `Ritva: metadados pesquisáveis` **não equivale** a `vídeo online livre`. Acessos atuais/termos de consulta e a enumeração deverão ser auditados antes de qualquer coletor.

## Normalização a aplicar no MAR

1. `institution`: Kuvi (histórico KAVI, registro da investigação #82); `service`: Elonet, Elävä muisti, Elokuvapolku, Ritva etc.; `collection/fonds`: somente quando demonstrado; `item`: obra/programa com identificador.
2. Para cada resultado, conservar `discovery_url`, `canonical_item_url`, `service`, `custodian`, `rights/access` e evidência de acesso. Se houver somente uma página temática, não inventar ficha de obra.
3. Quando o mesmo filme for apresentado pelo Elonet, Elävä muisti e Elokuvapolku, reconciliar obra por ID/proveniência demonstráveis; manter **várias rotas de descoberta** sem triplicar obras nem apagar o contexto curatorial.
4. O visitante deve ser enviado à **página específica da instituição detentora ou responsável pelo serviço**. O MAR não baixa mídia, incorpora players, hospeda arquivos nem transfere a audiência para si.
5. Acesso público via site, disponibilidade efetiva de vídeo por obra, autorização de automação e admissão científica são **quatro avaliações independentes**. Não deduzir nenhuma das demais a partir de um HTTP 403, de uma página indexada ou de sucesso da API.

## Decisão limitada e próxima etapa

- **Confirmado:** sete subdivisões navegacionais ligadas ao arquivo de filmes e uma área adicional RTVA/Ritva; descrição institucional pública de audiovisual em Elonet, Elävä muisti, Elokuvapolku e pesquisa pública Ritva.
- **Não verificado:** acesso de todas as fichas e execução dos players, direitos por item, enumeração completa, limites/robots por host, desduplicação efetiva e admissão ao corpus. **Verificado por navegação:** duas fichas individuais Elonet a partir de hyperlinks do Elokuvapolku.
- **Estado da investigação #82:** `hold_provisional`, `investigation_complete=false`. Não rotular KAVI/Kuvi/Elonet como indisponível; nenhuma promoção/ingestão.
- **Próximo ensaio limitado:** examinar por navegador uma ficha específica de cada um de Elonet, Elävä muisti e Elokuvapolku (e busca Ritva separadamente), registrar IDs, origem e disponibilidade da obra; interromper honestamente após bloqueio. API só é considerada **depois** da classificação das superfícies públicas.
