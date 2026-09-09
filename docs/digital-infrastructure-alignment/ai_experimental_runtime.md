# Runtime experimental de IA

## Estado

A infraestrutura T0A está implementada estruturalmente e integrada ao ciclo do organismo em modo sombra. Ela não ativa indicadores científicos, não altera elegibilidade e não participa do cálculo do baseline oficial.

## Dimensões separadas

1. uso institucional de ferramentas de IA pelo arquivo ou agregador;
2. IA do observatório para detectar evidência de acervo audiovisual e presença pública de vídeo;
3. detecção de vídeo gerado ou materialmente modificado por IA no nível de item, versão ou segmento.

A segunda dimensão possui duas tarefas operacionais, portanto o runtime registra quatro tarefas:

- `institutional_ai_use`;
- `audiovisual_collection_detection`;
- `public_video_presence_detection`;
- `synthetic_video_detection`.

## Feature flags

Todas as flags permanecem desligadas por padrão.

```text
MAR_AI_EXPERIMENTS_ENABLED=false
MAR_AI_SHADOW_MODE=true
MAR_AI_INSTITUTIONAL_USE_ENABLED=false
MAR_AI_COLLECTION_DETECTION_ENABLED=false
MAR_AI_VIDEO_PRESENCE_ENABLED=false
MAR_AI_SYNTHETIC_VIDEO_ENABLED=false
```

A flag geral e a flag específica da tarefa precisam estar ativas simultaneamente. Enquanto o T0A estiver vigente, uma tentativa de executar com `MAR_AI_SHADOW_MODE=false` é rejeitada.

## Persistência

Os registros são append-only e separados do baseline oficial:

```text
data/digital_infrastructure/ai_experiments/ai_institutional_use.jsonl
data/digital_infrastructure/ai_experiments/ai_observatory_triage.jsonl
data/digital_infrastructure/ai_experiments/ai_synthetic_audiovisual_content.jsonl
data/digital_infrastructure/ai_experiments/ai_experiment_runs.jsonl
data/digital_infrastructure/ai_experiments/ai_human_reviews.jsonl
```

A criação dos arquivos ocorre apenas quando houver execução habilitada. O manifesto de execução registra tarefas ativas, flags, vínculo com o ciclo oficial, horários e estado final.

## Comportamento fail-open

- tarefa desativada não é executada;
- handler ausente gera estado `not_executed` quando a unidade de análise é compatível;
- exceção do classificador vira registro `error`;
- falha de armazenamento é isolada e registrada no resumo experimental;
- configuração inválida de IA desativa a camada experimental para aquela rodada;
- nenhuma dessas ocorrências altera o código de saída do ciclo oficial.

## Baseline determinístico

O primeiro runtime usa um baseline local de palavras-chave, estruturas e contagens já materializadas. Sua função é fornecer uma referência mensurável para comparação com futuros modelos, não simular que existe um classificador de IA validado.

Os baselines cobrem inicialmente:

- sinais públicos de uso institucional de IA;
- sinais de existência de acervo audiovisual;
- sinais de presença pública de vídeo.

A detecção de vídeo sintético permanece definida no contrato, mas só executa quando houver `item_id`, `item_version_id` ou `segment_id`. Ela não é aplicada automaticamente no contexto institucional.

## Evidência e proveniência

Cada registro pode preservar:

- entidade, observação, item, versão ou segmento;
- tarefa e dimensão;
- previsão e estado;
- confiança, quando aplicável;
- URL, artefato e trecho de evidência;
- modelo, fornecedor, versão e configuração;
- versão do prompt ou classificador;
- duração, custo estimado e erro;
- estado e decisão da revisão humana;
- identificador imutável e versão do registro.

## Amostra inicial

A amostra canônica está em:

```text
data/digital_infrastructure/ai_experiments/validation_sample_v1.json
```

Ela contém APE, Europeana, INA, BFI, ARCHIPOP e AAPB. A amostra é inicial, não é padrão-ouro e não representa ainda todos os continentes.

Validação:

```bash
python scripts/build_ai_validation_sample.py --check
```

## Ativação futura

Depois do baseline oficial, cada componente deverá ser validado separadamente por precisão, revocação, F1, matriz de confusão, falsos positivos, falsos negativos e erros por idioma. A ativação ocorrerá por tarefa e versão, nunca por aprovação genérica de toda a camada de IA.
