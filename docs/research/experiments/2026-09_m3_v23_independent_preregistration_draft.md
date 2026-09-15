# M3 2.3.0 — pré-registro da próxima validação independente

Preparado em 15/09/2026. **Minuta completa para revisão; ainda não selada nem executada.**

Identificador reservado no registro central: `MAR-T2A-M3-VAL-009`, posterior à CAL-008,
com status `reserved_draft_not_executed`. O candidato de referência é
`2.3.0-dev`, commit `bb52621862b973301f6fbe5330f2cd1203ab77b8`.
Referência de código não significa congelamento ou promoção.

## Pergunta e alcance

A tipagem do candidato generaliza para superfícies de entidades que não integraram
os conjuntos humanos anteriores de M3? O resultado será condicionado à descoberta
limitada do MAR. Não estimará prevalência, completude de descoberta, pertencimento
ao corpus, uso institucional de IA ou IA em conteúdo audiovisual.

A VAL-007 continua encerrada, o M3 2.2.0 não validado e o M4 bloqueado.

## Entidades propostas, em ordem de execução

| Código | Entidade | País |
|---|---|---|
| `cinematek` | CINEMATEK | Bélgica |
| `cinematheque-bretagne` | Cinémathèque de Bretagne | França |
| `dr` | DR / Gensyn | Dinamarca |
| `ert` | ERT | Grécia |
| `estonian_film_archive` | Arquivo de Cinema da Estônia / Arkaader | Estônia |
| `filmoteca_catalunya` | Filmoteca de Catalunya | Espanha |

As URLs de entrada estão no protocolo JSON e foram retiradas da configuração já
versionada do MAR. Não foram realizadas novas visitas ou previsões para escolhê-las.
São entidades novas em relação aos conjuntos humanos identificados de M3;
não se presume que nunca tenham sido coletadas pelo MAR nem que suas tecnologias
sejam inéditas. A auditoria de exposição a desenvolvimento adicional antecede o selo.

## Amostra e exclusões

- Profundidade máxima 2; até 8 páginas por entidade; timeout de 12 segundos;
  respeito a robots.txt e às barreiras de acesso.
- Selecionar as primeiras 6 URLs únicas e elegíveis por entidade na ordem do
  coletor congelado, até 36 unidades. A seleção ocorre antes da classificação.
- Manter erros de acesso e restrições como observações; não removê-los para
  melhorar o resultado. Não inserir URLs manualmente ou balancear por previsão.
- Excluir as 117 URLs dos conjuntos de 17 + 33 + 36 + 31 revisões anteriores.
  O manifesto anexo contém todas elas e os hashes SHA-256 das quatro fontes.
- Antes do selo, acrescentar qualquer material posterior de desenvolvimento e
  aliases conhecidos. 117 é a base comprovada, não um teto para exclusões.
- Verificar URL solicitada e redirecionada; remover fragmentos, normalizar host,
  esquema e porta padrão, preservando caixa do caminho e valores/ordem da query.
  Deduplicar globalmente; manter a primeira ocorrência e registrar as demais.
- Exigir pelo menos 24 unidades e 5 entidades. Se faltar cobertura, encerrar como
  amostra insuficiente antes da revisão. Não substituir entidades ou repetir
  coletas seletivamente. Só retomar uma interrupção com estado persistido idêntico.

## Métricas e gates

Mantêm-se os limiares pré-registrados da VAL-007. As sugestões anteriores de
F1 mínimo adicional ou aumento do limiar de acesso não foram adotadas.

| Dimensão | Condições necessárias |
|---|---|
| M3, nove classes | F1 ponderado ≥0,50; recall ≥0,50 em cada classe humana com suporte ≥5 |
| Elegibilidade de item para M4 | Precisão ≥0,80; recall ≥0,70; especificidade ≥0,85 |
| Condição por entidade | Para cada entidade com ≥2 itens humanos, recuperar pelo menos 1 |
| Acesso | Concordância exata ≥0,90, avaliada separadamente |

A matriz fina inclui todas as unidades, inclusive `unknown`, com linhas humanas
e colunas previstas. Publicar acerto exato, F1 ponderado, dois macro F1 (nove classes
e classes com suporte humano) e métricas por classe. No cálculo multiclasses,
divisões por zero recebem 0 e classes sem suporte são explicitadas.

No binário, excluir apenas `unknown` humano com item-level nulo. Uma abstenção do
modelo diante de item humano conta como FN. Publicar TP/TN/FP/FN, precisão, recall,
F1, especificidade e acurácia. Métrica binária com denominador zero recebe `null`.
O acesso usa todas as unidades e sua própria matriz; sucesso em acesso não compensa
falha semântica. Informar resultados e suporte por entidade, sem tratar traduções
ou páginas da mesma instituição como observações estatisticamente independentes.

IDs duplicados/ausentes/extras, previsões faltantes ou rótulos incompatíveis
invalidam a avaliação. Não reduzir denominadores para contornar inconsistências.

Decisão: `INVALID` para quebra de integridade; `FAIL` para qualquer critério
avaliável reprovado; `INCONCLUSIVE` se não houver reprovação demonstrada, mas
faltarem cobertura ou métricas obrigatórias definidas; `PASS` somente com todos
os gates avaliáveis e satisfeitos. Comparar valores sem arredondamento.
Um PASS sustenta uma decisão posterior de avanço; não aciona implantação automática.

## Cegamento, evidência e congelamento

O revisor humano classifica a página principal observada, com ID, data, justificativa
e referência da evidência em cada linha. Página pai e mídia ligada não substituem
a unidade. A classificação usa o snapshot; verificações posteriores da página viva
são contexto datado separado, sem reescrever a observação histórica.

Uma pessoa faz a revisão primária; não se alegará concordância entre avaliadores.
Esclarecimentos antes do freeze devem preservar emendas e ocorrer sem previsões.
Depois da abertura, divergências são achados da validação, não motivo para relabeling.

Sequência obrigatória:

1. Concluir os requisitos de prontidão usando apenas dados conhecidos.
2. Selar protocolo, candidato, base importada, coletor, configuração, gerador,
   avaliador, dependências, inventário de exclusões e manual de anotação.
3. Executar a coleta limitada, preservar snapshots e selecionar a amostra sem previsões.
4. Gerar e selar previsões antes de qualquer anotação; disponibilizar somente fila cega.
5. Concluir todas as revisões e persistir um manifesto separado de freeze humano.
6. Abrir previsões, avaliar uma vez e registrar os gates e limitações.

Previsões precisam de armazenamento durável restrito ao custodiante durante a revisão.
Hash público não autoriza publicar o conteúdo. Branch pública e artifact público de
Actions não asseguram cegamento. Definir custodiante, revisor e local de armazenamento
antes da execução; se essa separação não puder ser mantida, não iniciar a revisão.

## Requisitos ainda necessários antes de selar

O gerador atual importa o classificador 2.2.0 e inclui `collector_access_state`,
derivado da decisão automática, na fila humana. Portanto, não deve ser usado sem
adaptação: exigir seleção explícita do candidato, metadados corretos da versão,
fila sem nenhum campo previsto e evidências brutas separadas das decisões do modelo.
Também testar exclusões/deduplicação e fórmulas do avaliador antes de usar dados novos.

O registro central de VAL-007 e CAL-008 foi completado a partir dos artefatos
existentes, sem modificar as decisões históricas; VAL-009 foi reservado como minuta.
O novo módulo de prontidão seleciona antes de classificar, usa o candidato explícito
e produz fila humana por lista de campos permitidos. O calculador das métricas foi
testado com casos sintéticos e a matriz histórica da VAL-007. Essas verificações
não constituem execução independente. A minuta JSON original permanece preservada
como referência inicial; suas pendências devem ser lidas com o relatório abaixo.

Consultar [prontidão técnica e pendências de execução](2026-09_m3_v23_validation_readiness.md)
antes de qualquer selo ou coleta. Ainda é necessário integrar a proveniência do
coletor, implementar o executor que verifica os manifestos de freeze, auditar a
exposição adicional e definir custodiante, revisor e armazenamento restrito.

Nenhuma coleta, geração de previsões, revisão humana, alteração de gates históricos,
congelamento ou promoção foi realizada por este pré-registro em preparação.

## Artefatos

- [Protocolo computável](../../../data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_3_draft.json)
- [Manifesto das exclusões](../../../data/digital_infrastructure/ai_experiments/m3_surface_type_known_urls_exclusion_v2_3_draft.json)
- [Gates originais da VAL-007](../../../data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_2.json)
