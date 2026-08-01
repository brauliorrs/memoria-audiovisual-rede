# Protocolo de alegações, correções e contestações

## Objetivo

Reduzir risco de erro, dano reputacional e falsa certeza em registros relativos a instituições, fornecedores, contratos, tecnologias, IA e riscos.

## Tipos de enunciado

- `direct_observation`: observação técnica diretamente reproduzível;
- `documented_fact`: fato sustentado por fonte documental identificada;
- `institutional_statement`: declaração da própria instituição ou fornecedor;
- `third_party_report`: informação de terceiro confiável;
- `analytical_inference`: inferência explícita baseada em evidências;
- `risk_assessment`: avaliação segundo regra versionada;
- `unverified_claim`: alegação ainda não confirmada.

A camada pública deverá identificar claramente o tipo de enunciado e seu nível de confiança.

## Regras para fornecedores e contratos

- detecção de software não prova relação contratual;
- presença de marca não prova fornecimento atual;
- anúncio institucional não prova operação continuada;
- valor contratual não deve ser estimado sem método documentado;
- ausência em portal de compras não prova inexistência de contrato;
- nomes comerciais e razões sociais devem ser resolvidos separadamente.

## Correções

Uma correção deverá registrar:

- objeto afetado;
- versão anterior;
- motivo;
- origem da correção;
- evidência nova;
- impacto sobre indicadores e snapshots;
- responsável pela decisão;
- data da alteração;
- necessidade de republicação.

## Contestações

Instituições, fornecedores, pesquisadores ou demais interessados poderão apresentar contestação documentada. O registro deverá assumir um dos estados:

- `received`;
- `under_review`;
- `additional_evidence_requested`;
- `accepted`;
- `partially_accepted`;
- `rejected_with_reason`;
- `withdrawn`;
- `closed`.

## Medidas cautelares

Durante revisão de alegação sensível, o conteúdo poderá ser:

- marcado como contestado;
- temporariamente suprimido;
- mantido apenas em camada restrita;
- substituído por nota metodológica;
- retirado da geração de indicadores.

A retirada cautelar não implica reconhecimento automático de erro.