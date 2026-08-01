# Arquitetura da auditoria de infraestrutura digital

## Finalidade

Esta camada observa como arquivos, cinematecas, emissoras e agregadores disponibilizam seus acervos em superfícies digitais públicas. Ela complementa a análise de visibilidade audiovisual com uma leitura da infraestrutura técnica que sustenta encontrabilidade, descrição, interoperabilidade, acesso e estabilidade.

A auditoria não tenta reproduzir integralmente a arquitetura interna das instituições. Ela registra apenas sinais verificáveis nas rotas públicas observadas.

## Princípios

1. **Separação entre detecção e afirmação.** Um sinal técnico é registrado como evidência; somente após validação pode sustentar afirmação institucional.
2. **Ausência de sinal não equivale a ausência da tecnologia.** Sistemas podem operar no servidor sem exposição pública.
3. **Rastreabilidade.** Toda detecção deve preservar rota, data, status HTTP, evidência e método.
4. **Não intrusão.** A ferramenta não contorna autenticação, paywalls, geobloqueios, robots.txt ou mecanismos de proteção.
5. **Comparabilidade controlada.** Resultados são comparáveis somente quando derivados de superfícies equivalentes e classificados com o mesmo contrato de dados.
6. **Versionamento longitudinal.** Mudanças técnicas devem ser observáveis entre snapshots sem sobrescrever evidências anteriores.

## Fluxo lógico

```text
CORPORA
  -> seleção de rotas públicas
  -> coleta HTTP controlada
  -> detectores heurísticos
  -> registro bruto de evidências
  -> classificação de confiança
  -> validação metodológica
  -> snapshot longitudinal
  -> indicadores e visualização
```

## Camadas

### 1. Registro de corpora

Origem: `src/memoria_audiovisual/corpora.py`.

Responsabilidades:

- identificar a unidade observada;
- distinguir agregador de instituição custodial;
- fornecer a rota pública inicial;
- preservar escopo, completude e limite técnico;
- impedir mistura entre unidade institucional e plataforma tecnológica.

### 2. Coleta

Origem: `scripts/audit_digital_infrastructure.py`.

Responsabilidades:

- selecionar corpora;
- aplicar timeout e identificação do agente;
- registrar redirecionamentos e URL final;
- limitar a coleta às superfícies públicas;
- produzir saídas CSV e JSON equivalentes.

### 3. Detecção

Origem: `src/memoria_audiovisual/digital_infrastructure_audit.py`.

Grupos analíticos:

- `technology`: CMS, frameworks e softwares de repositório;
- `api_service`: REST, GraphQL, OpenAPI, OAI-PMH, SPARQL e IIIF;
- `metadata_format`: JSON-LD, Schema.org, Dublin Core, EAD, METS, MODS, MARC, EDM, PBCore e EBUCore;
- `interoperability`: IIIF, OAI-PMH, OpenSearch, RSS/Atom, sitemap e Linked Open Data;
- `search`: formulários, busca facetada e sinais de motores de indexação;
- `restriction`: autenticação, cadastro, assinatura, geobloqueio, direitos condicionados e restrições de indexação;
- `ai_evidence`: declarações públicas de IA, aprendizado de máquina, transcrição automática, reconhecimento de fala, visão computacional ou classificação automatizada.

### 4. Evidência

Cada sinal deve manter categoria, valor detectado, origem da evidência, trecho ou chave observada, URL observada e final, data da observação, detector, confiança automática e situação da validação humana.

### 5. Validação

A validação não altera o registro bruto. Ela acrescenta uma camada curatorial separada.

Estados permitidos:

- `pending_review`;
- `confirmed`;
- `probable`;
- `inconclusive`;
- `false_positive`;
- `not_assessable`.

### 6. Snapshot longitudinal

Chave recomendada:

```text
corpus_code + observed_url + detector_group + detected_value + observation_date
```

O histórico não deve ser deduplicado apenas pelo corpus. Uma mesma instituição pode trocar de CMS, endpoint, padrão de metadados ou política de acesso ao longo do tempo.

## Produtos de dados

Saída bruta:

- `data/output/digital_infrastructure_audit.csv`;
- `data/output/digital_infrastructure_audit.json`.

Saída curada futura:

- `data/output/digital_infrastructure_audit_validated.csv`;
- `data/output/digital_infrastructure_audit_validated.json`.

Histórico futuro:

- `data/output/digital_infrastructure_audit_timeline.csv`.

## Indicadores previstos

Somente registros validados devem alimentar indicadores públicos:

- unidades com API pública detectada;
- unidades com IIIF ou OAI-PMH;
- unidades com metadados estruturados;
- diversidade de padrões por país e tipo institucional;
- mecanismos de busca estruturados;
- restrições públicas detectáveis;
- dependência de plataformas externas;
- sinais públicos de IA aplicada à descrição ou recuperação;
- mudanças de tecnologia entre snapshots.

## Limites interpretativos

A auditoria observa a superfície pública, não a infraestrutura integral. Sem triangulação adicional, os resultados não permitem afirmar toda a pilha tecnológica, fornecedor contratado, arquitetura interna, ausência definitiva de IA, interoperabilidade organizacional ou conformidade jurídica e de segurança.