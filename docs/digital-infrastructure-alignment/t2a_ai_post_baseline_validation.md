# T2A — validação pós-baseline dos componentes de IA

## Objetivo

O T2A avalia os componentes experimentais de inteligência artificial depois do congelamento do baseline operacional oficial. Nenhum resultado desta etapa modifica o T2, seus denominadores, os nove indicadores oficiais ou a elegibilidade dos corpora.

## Fila inicial de revisão

A fila canônica está em:

`data/digital_infrastructure/ai_experiments/t2a_human_review_queue_v1.json`

Ela foi derivada do artefato do ciclo integral T1 (`full-observatory-cycle-31038017955`) e contém 18 unidades:

- seis entidades da amostra inicial;
- três tarefas com registros no T1;
- 15 previsões experimentais reais;
- três lacunas explícitas do APE, cujo coletor falhou antes da geração dos sinais experimentais.

As lacunas não recebem previsão presumida.

## Rótulos humanos

Cada unidade deverá receber:

- `review_status`: `completed`, `confirmed`, `corrected` ou `rejected`;
- `human_label`: `positive`, `negative`, `ambiguous` ou `not_assessable`;
- `human_decision`: justificativa sintética da decisão;
- `reviewer_id`: identificador estável do revisor;
- `reviewed_at`: timestamp UTC;
- `review_notes`: observações adicionais e conflitos de evidência.

Casos ambíguos e não avaliáveis são preservados, mas não entram na matriz binária.

## Métricas

O avaliador calcula, por tarefa e no agregado:

- verdadeiros positivos;
- falsos positivos;
- verdadeiros negativos;
- falsos negativos;
- precisão;
- revocação;
- F1.

Também produz cortes por:

- idioma;
- geografia;
- tipo de instituição ou estrato analítico.

O relatório permanece em estado `pending_human_review` enquanto houver unidades pendentes. A conclusão da anotação não ativa automaticamente nenhum componente: cada tarefa recebe uma decisão científica posterior e independente.

## Critério para decisão de ativação

A decisão deverá ser tomada separadamente para:

1. presença institucional de IA;
2. detecção de acervo audiovisual;
3. detecção de presença pública de vídeo;
4. detecção de vídeo sintético, quando existir amostra item a item.

Além das métricas globais, deverão ser examinados falsos positivos e negativos por idioma e tipo institucional, estabilidade entre versões, tempo e custo. A aprovação de uma tarefa não autoriza as demais.

## Limitação atual

A tarefa `synthetic_video_detection` não integra a primeira fila porque o T1 coletou sinais em nível de entidade e não produziu unidades item/versão/segmento. Essa tarefa continuará bloqueada até existir amostra audiovisual específica e revisão humana no nível correto.
