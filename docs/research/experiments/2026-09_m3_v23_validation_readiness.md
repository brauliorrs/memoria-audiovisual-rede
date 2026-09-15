# VAL-009 / M3 2.3.0 — prontidão técnica

15/09/2026. Estado: **preparação em desenvolvimento; não selada, não executada**.
VAL-007 permanece encerrada; M3 2.2.0 não validado; M4 bloqueado.

## Implementado

- `surface_review_v23.py`: seleção na ordem pré-registrada, limites por entidade e
  totais, exclusões das URLs solicitadas e finais, deduplicação global e auditoria
  de cada registro, inclusive os que excedem os limites. Seleção antes da classificação.
- Normalização conservadora: esquema/host em minúsculas, remoção de porta padrão
  e fragmento; preservação da caixa do caminho e dos valores/ordem da query.
- Uso explícito de `2.3.0-dev`, com versão correta nos metadados. Fila humana por
  lista fechada de campos; nenhuma decisão automática de superfície ou acesso.
  Erros de acesso continuam elegíveis. Amostra insuficiente não gera previsões
  nem libera fila de revisão.
- `surface_metrics_v23.py`: matrizes fina e de acesso, F1 ponderado, dois macro F1,
  binário, resultados por entidade e gates com os limiares originais. IDs ausentes,
  extras ou duplicados e rótulos incompatíveis resultam em INVALID. Abstenção do
  modelo em item humano conta como FN; apenas unknown humano/nulo sai do binário.
  Denominador binário zero produz null. FAIL prevalece sobre INCONCLUSIVE.
- Registro central: VAL-007 e CAL-008 adicionados a partir das conclusões já
  versionadas; VAL-009 reservado como `reserved_draft_not_executed`. Registros
  anteriores preservados. O novo script usa o schema vigente e hashes das fontes.
  O helper antigo `register_m3_val007_cal008.py` usa outro formato e não foi executado.

## Verificação

62 testes focados passaram: seletor, fila cega, calculador, gerador histórico e
candidato. Apenas fixtures conhecidas e URLs sintéticas de example.org.
Suíte completa: **811 testes e 2 subtestes passaram**. Validação semântica do
registro aprovada; registros anteriores, classificador 2.2.0 e artefatos v2_2
conferidos byte a byte contra o commit de origem, sem alterações.
A matriz publicada da VAL-007 foi expandida em pares sintéticos para verificar
aritmética: 7/31, F1 ponderado 0,2828236279849183, TP=2/TN=16/FP=0/FN=12.
Isso testa as fórmulas; não reclassifica páginas nem altera a avaliação histórica.
As entidades desses pares são sintéticas; o teste por entidade usa casos separados.

Os módulos não coletam páginas, gravam previsões, verificam um freeze ou autorizam
divulgação. Seus resultados são explicitamente de desenvolvimento. Mesmo PASS
numérico mantém `m4_scaling_allowed=false`.

## Pendências que impedem selar e executar

1. **Proveniência do coletor e snapshots.** O coletor histórico pode substituir a URL
   solicitada pela final e não oferece todo o contrato de snapshot do novo seletor.
   Adaptar uma via 2.3 com preservação de ambas, evidência bruta durável e referência
   verificável para cada registro, inclusive erros/restrições. Não preencher a URL
   solicitada por suposição. O novo seletor recusa sua ausência.
2. **Executor e manifestos.** Integrar seleção, armazenamento e calculador a um
   executor que valide SHA-256/commits, versão, integridade da amostra, conclusão
   humana, identificação/data/justificativa, freeze humano e ordem da divulgação.
   O calculador atual verifica a integridade das linhas e a aritmética; não certifica
   autenticidade, independência ou cronologia. Não usá-lo como avaliação oficial isolada.
3. **Exposição adicional e manual.** Conferir fixtures/URLs/aliases posteriores às
   117 exclusões, fontes e entidades; preparar o manual final de anotação, completar
   o inventário e selar dependências, base importada, wrapper, coletor, configuração,
   gerador, avaliador e protocolo. Os testes novos usam domínios sintéticos.
4. **Cegamento operacional.** Registrar custodiante, revisor e local durável de acesso
   restrito para previsões. A função de desenvolvimento devolve fila e previsões
   separadamente em memória; isso não implementa controle de acesso. Não publicar
   previsões em branch ou artifact público durante a revisão. Inspecionar também
   os snapshots referenciados para impedir vazamento de decisões automáticas.

Concluir os itens técnicos com dados conhecidos. Só depois das condições operacionais
definidas e do selo, executar a coleta única, congelar previsões, revisar todas as
unidades cegamente, congelar humanos e abrir as previsões para avaliação formal.
