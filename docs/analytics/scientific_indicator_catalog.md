# Catálogo científico dos indicadores

## Objetivo

O catálogo científico explica por que cada indicador existe, qual pergunta responde, como deve ser interpretado e quais conclusões não podem ser extraídas dele.

Ele complementa, mas não substitui, o registro metodológico:

```text
indicator_catalog.json
→ justificativa científica e interpretação

methodology_registry.json
→ fórmula, variáveis, estados e limitações operacionais
```

## Campos obrigatórios

Cada indicador registrado deve declarar:

- identificador e versão;
- título;
- pergunta científica;
- justificativa da escolha;
- dimensão observada;
- interpretação;
- aspectos que não mede;
- relação com outros indicadores;
- referência à metodologia correspondente.

O índice de acesso também declara a regra do corpus: bancos comerciais pagos são identificados e catalogados no registro de descoberta, mas não integram o corpus científico nem o denominador.

## Barreira de execução

O executor analítico carrega o catálogo antes de calcular o snapshot. A execução é bloqueada quando:

- um indicador registrado não possui ficha explicativa;
- existe ficha sem implementação correspondente;
- faltam pergunta científica, justificativa ou interpretação;
- não há declaração explícita das limitações;
- a combinação de identificador e versão está duplicada.

Assim, nenhum novo indicador poderá entrar silenciosamente no motor apenas com código e fórmula.

## Indicadores documentados na versão 1.0.0

```text
audiovisual_archive_access_index@1.0.0
api_coverage@1.0.0
interoperability_coverage@1.0.0
iiif_coverage@1.0.0
oai_pmh_coverage@1.0.0
dublin_core_coverage@1.0.0
schema_org_coverage@1.0.0
json_ld_coverage@1.0.0
interoperability_index@1.0.0
```

## Distinção central

O índice de acesso mede a proporção de arquivos elegíveis acessíveis sem cadastro, pagamento ou solicitação formal. Os demais indicadores observam infraestrutura, metadados e interoperabilidade. Portanto, maior maturidade técnica não deve ser interpretada automaticamente como maior acesso público.

## Versionamento

Mudanças apenas editoriais podem incrementar a versão do catálogo. Alterações na pergunta científica, interpretação ou justificativa que modifiquem o significado do indicador devem ser acompanhadas de revisão metodológica e avaliação sobre a necessidade de nova versão do próprio indicador.
