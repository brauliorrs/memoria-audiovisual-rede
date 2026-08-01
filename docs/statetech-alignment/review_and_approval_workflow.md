# Fluxo de revisão, aprovação e publicação

## Estados do registro

```text
draft
collected
pending_review
under_review
needs_evidence
probable
confirmed
inconclusive
false_positive
not_assessable
approved_for_snapshot
published
superseded
withdrawn
```

## Fluxo padrão

1. **Criação** — registro e proveniência mínima são criados.
2. **Triagem** — validações sintáticas, integridade de identificadores e presença de evidência.
3. **Revisão especializada** — análise técnica, institucional, contratual, temporal ou de IA.
4. **Decisão curatorial** — confirmação, probabilidade, inconclusão, falso positivo ou impossibilidade de avaliação.
5. **Elegibilidade para snapshot** — somente registros com integridade e estado permitido.
6. **Fechamento de ciclo** — congelamento no snapshot e geração de manifesto.
7. **Cálculo de indicadores** — somente sobre dados elegíveis e denominadores documentados.
8. **Revisão de publicação** — cobertura, comparabilidade, licença, limitações e conflito de interesse.
9. **Publicação** — geração de produto versionado.

## Revisão por criticidade

### Criticidade comum

Exige um revisor curatorial independente do coletor.

### Criticidade elevada

Inclui contratos, identificação de fornecedor, fluxos transfronteiriços, uso operacional de IA e dependência crítica. Exige revisão especializada e aprovação curatorial.

### Criticidade alta ou crítica

Inclui risco alto/crítico, alegação de reconhecimento facial, processamento de dados pessoais, contrato de alto valor ou afirmação potencialmente reputacional. Exige dupla revisão e aprovação do `senior_curator`.

## Prazos e expiração

A política não presume que uma confirmação permaneça atual indefinidamente. Cada classe de variável terá janela de revalidação:

- disponibilidade técnica e acesso: 90 dias;
- API, busca, interoperabilidade e plataformas externas: 180 dias;
- fornecedor e tecnologia estrutural: 365 dias;
- contrato: conforme vigência e atualização da fonte;
- natureza institucional: 730 dias, salvo evento de mudança;
- IA operacional: 180 dias;
- risco: revisto a cada snapshot anual ou evento material.

Registro expirado não é apagado; passa a exigir revalidação para produtos correntes.

## Reabertura

Um registro confirmado poderá ser reaberto por:

- nova evidência contraditória;
- mudança empírica;
- expiração da validade;
- correção curatorial;
- migração de schema;
- contestação documentada;
- erro de resolução de entidade.

## Aprovação de snapshot

O fechamento exige:

- ausência de erros bloqueantes de integridade;
- relatório de cobertura;
- lista de pendências e exclusões;
- identificação dos agentes responsáveis;
- versões de schema, metodologia e regras;
- aprovação do `snapshot_manager` e de um `senior_curator`.

## Aprovação de indicador

Exige:

- definição versionada;
- numerador, denominador e universo explícitos;
- cobertura acima do limite mínimo;
- comparabilidade declarada;
- ausência de registros pendentes materialmente relevantes;
- revisão do `indicator_steward`;
- autorização de publicação quando destinado ao público.

## Retirada e correção pública

Produto publicado não será silenciosamente substituído. Estados possíveis:

- `active`;
- `superseded`;
- `corrected`;
- `withdrawn`;
- `archived`.

Correções deverão apontar para a versão anterior, explicar motivo, alcance e impacto analítico.
