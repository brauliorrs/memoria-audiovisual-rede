# Protocolo de alegações, correções e contestações

## Objetivo

Reduzir erro, dano reputacional e falsa certeza em registros relativos a instituições, fornecedores, contratos, tecnologias, IA, acesso e avaliações analíticas.

## Tipos de enunciado

- `direct_observation`: observação técnica diretamente reproduzível;
- `documented_fact`: afirmação sustentada por fonte documental identificada;
- `institutional_statement`: declaração da própria instituição ou fornecedor;
- `third_party_report`: informação de terceiro identificável;
- `analytical_inference`: inferência explícita baseada em evidências e método;
- `risk_assessment`: avaliação segundo regra versionada;
- `unverified_claim`: alegação ainda não confirmada;
- `methodological_note`: explicação sobre cobertura, detector ou limitação.

A camada pública deve indicar claramente o tipo de enunciado e evitar apresentar inferência como fato documentado.

## Regras gerais

- detecção de software não prova relação contratual;
- presença de marca não prova fornecimento atual;
- anúncio institucional não prova operação continuada;
- ausência em portal ou superfície pública não prova inexistência;
- valor contratual não deve ser estimado sem método documentado;
- nomes comerciais e razões sociais devem ser resolvidos separadamente;
- não detecção de IA não prova ausência de uso institucional;
- possível desaparecimento não equivale a descontinuação confirmada;
- avaliação de risco deve indicar regra, fatores e data de referência.

## Correções

Uma correção registra:

- objeto, evento, indicador ou produto afetado;
- versão anterior;
- tipo de erro ou necessidade de atualização;
- origem da correção;
- evidência nova ou regra aplicável;
- impacto sobre snapshots, comparações, indicadores e textos públicos;
- responsável pela decisão;
- datas de recebimento, decisão e publicação;
- necessidade de republicação, supressão ou retirada.

Correções não apagam versões anteriores. Quando não houver mudança no mundo observado, a correção deve ser classificada como curatorial, técnica, editorial ou metodológica, e não como evento empírico.

## Contestações

Instituições, fornecedores, pesquisadores ou demais interessados podem apresentar contestação documentada. O processo deve disponibilizar um canal identificável na documentação ou vitrine pública quando esta for implantada.

Estados:

- `received`;
- `under_review`;
- `additional_evidence_requested`;
- `accepted`;
- `partially_accepted`;
- `rejected_with_reason`;
- `withdrawn`;
- `closed`.

## Registro mínimo da contestação

- identificador;
- solicitante e forma de contato, tratados conforme política de dados pessoais;
- objeto e versão contestados;
- fundamento apresentado;
- evidências fornecidas;
- data de recebimento;
- responsável pela análise;
- medidas cautelares;
- decisão e justificativa;
- impacto e revisão publicada;
- data de encerramento.

## Medidas cautelares

Durante a revisão, o conteúdo pode ser:

- marcado como contestado;
- acompanhado de nota contextual;
- temporariamente suprimido;
- mantido apenas em camada restrita;
- retirado da geração de indicadores;
- preservado sem alteração quando a contestação não apresentar risco ou evidência suficiente.

A medida cautelar deve ser proporcional, temporária e registrada. Supressão ou retirada cautelar não implica reconhecimento automático de erro.

## Decisão

A decisão deve considerar:

- qualidade e pertinência das evidências existentes e novas;
- proporcionalidade do enunciado;
- possibilidade de reprodução da observação;
- impacto científico e público;
- direitos de terceiros;
- necessidade de revisão independente;
- efeito sobre produtos derivados.

A rejeição deve apresentar motivo. A aceitação parcial deve identificar exatamente quais elementos foram alterados e quais permaneceram.

## Prazos e governança

Prazos operacionais e responsáveis devem ser definidos antes da primeira publicação institucional ampla. Enquanto essa governança não estiver formalizada, o projeto deve evitar prometer tempos de resposta específicos.

## Transparência

Quando juridicamente e eticamente possível, o histórico público deve informar que houve correção, contestação, supressão ou retirada, sem expor dados pessoais desnecessários nem reproduzir integralmente documentos protegidos.

## Estado atual

O modelo de revisão e publicação versionada suporta correções sem sobrescrita. O fluxo institucional de recebimento, análise e resposta a contestações ainda precisa ser formalizado antes da vitrine definitiva e da primeira publicação científica oficial.