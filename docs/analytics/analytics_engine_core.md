# Núcleo analítico versionado

## Finalidade

A camada `memoria_audiovisual.analytics` interpreta produtos já preservados pela plataforma. Ela não coleta páginas, não altera snapshots, não escreve no ledger e não modifica publicações curatoriais.

O primeiro contrato de entrada é a matriz `parameter_coverage.json`, porque ela distingue detecção, ausência, erro, lacuna e impossibilidade de avaliação.

## Componentes

- `IndicatorContext`: restringe uma execução a um único snapshot.
- `Indicator`: contrato abstrato de cálculo, versão e metodologia.
- `IndicatorRegistry`: impede duplicidade de identificador e versão.
- `AnalyticsEngine`: executa indicadores em ordem determinística.
- `IndicatorResult`: registra numerador, denominador, unidade, versão e dimensões auxiliares.

## Regras metodológicas iniciais

Os indicadores de cobertura usam como denominador apenas corpora avaliáveis.

Estados incluídos:

```text
detected
not_detected
unknown
```

Estados excluídos:

```text
error
not_assessable
missing_observation
```

A exclusão é registrada no próprio resultado. Portanto, um percentual nunca deve ser interpretado sem o denominador e a lista de corpora excluídos.

## Indicadores iniciais

- `api_coverage@1.0.0`;
- `interoperability_coverage@1.0.0`.

As definições e limitações ficam versionadas em:

```text
data/templates/analytics/methodology_registry.json
```

## Garantias

- nenhum indicador pode misturar snapshots;
- duplicidades de cobertura por corpus e grupo são bloqueadas;
- resultados precisam apontar para o mesmo indicador, versão e snapshot executados;
- falhas são explícitas e, por padrão, interrompem a execução;
- a metodologia é identificada separadamente da versão do código do indicador.

## Próxima integração

O próximo incremento deverá criar o executor e o armazenamento dos produtos:

```text
data/digital_infrastructure/analytics/<snapshot_id>/snapshot_indicators.json
data/digital_infrastructure/analytics/indicator_history.jsonl
```

A persistência deverá ser append-only para o histórico e impedir sobrescrita de uma execução já consolidada com a mesma combinação de snapshot, indicador e versão metodológica.
