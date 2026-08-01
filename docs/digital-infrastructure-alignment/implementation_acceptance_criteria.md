# Critérios de aceite da implementação

## Critérios transversais

Um módulo somente será considerado concluído quando:

- possuir contrato de entrada e saída versionado;
- preservar proveniência e agente responsável;
- não sobrescrever histórico;
- validar referências e estados controlados;
- produzir erros explícitos, sem preenchimento silencioso;
- possuir testes unitários e de contrato;
- documentar limitações e casos não avaliáveis;
- não expor registros pendentes na camada pública.

## Aceite por fase

### Núcleo de dados
- IDs estáveis e únicos;
- versões encadeadas;
- referências válidas;
- registros serializáveis segundo schemas.

### Ingestão
- cada observação vinculada a fonte, método e data;
- artefato bruto identificável;
- transformação registrada;
- falhas preservadas como estado, não descartadas.

### Curadoria e qualidade
- decisão humana identificada;
- conflitos de interesse registrados;
- bloqueios críticos respeitados;
- aptidão específica por finalidade.

### Snapshots
- manifesto completo;
- conteúdo imutável após fechamento;
- hash ou identificador verificável;
- schema e metodologia declarados.

### Comparação longitudinal
- diferenças classificadas;
- cobertura e comparabilidade verificadas;
- correções separadas de mudanças empíricas;
- resultados inconclusivos não convertidos em tendência.

### Indicadores
- fórmula e denominador versionados;
- cobertura mínima aplicada;
- confiança e limitações publicadas;
- supressão automática quando exigida.

### Publicação
- manifesto disponível;
- licença e limitações declaradas;
- snapshot de origem identificável;
- retirada ou substituição preservando versões anteriores.
