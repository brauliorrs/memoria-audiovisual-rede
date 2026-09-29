# VAL-009 — triagem metodológica de URLs e independência das entidades (minuta)

**Estado em 29/09/2026:** `HOLD`; verificação documental e offline, **sem parecer assinado** de revisor independente, sem novas visitas, previsões, congelamentos ou selo científico. A revisão detalhada está em `m3_surface_type_methodology_review_v2_3_draft.json`. Base documental: commit histórico `4544bbc40e076cd7a81800a3c93ebbfb8efae5b2`; a baseline `v0.1.0` e a VAL-007 permanecem intactas.

## Descoberta que altera a leitura da minuta

**As seis entidades propostas já constavam de coletas anteriores do projeto MAR, antes do desenvolvimento 2.3.0.** Os arquivos versionados `data/output/<corpus>_snapshot_metadata.json` registram a URL de origem **exatamente igual** à proposta no pré-registro e possuem tabelas `paginas_internas.csv` com registros vinculados ao mesmo endereço. A auditoria offline confere ambos os arquivos por Git blob e sua consistência com a minuta histórica.

| Entidade proposta | Corpus anterior | Metadata produzida (UTC) | Evidência |
| --- | --- | --- | --- |
| CINEMATEK | `cinematek` | 06/07/2026 15:30 | raiz idêntica ao pré-registro |
| Cinémathèque de Bretagne | `cinematheque_bretagne` | 19/06/2026 17:33 | raiz idêntica |
| DR/Gensyn | `dr` | 13/07/2026 18:12 | raiz idêntica; o coletor também usou API auxiliar |
| ERT | `ert` | 14/07/2026 18:54 | raiz idêntica |
| Arquivo de Cinema da Estônia/Arkaader | `efa_estonia` | 15/07/2026 19:38 | raiz idêntica; integração de APIs já existe |
| Filmoteca de Catalunya | `filmoteca_catalunya` | 17/07/2026 17:09 | raiz idêntica; o coletor também usou API auxiliar |

São registros **do corpus geral MAR**, não os rótulos humanos cegos das quatro rodadas anteriores de M3. Os 117 rótulos anteriores e as 20 páginas descobertas adicionalmente somam **137 URLs historicamente comprovadas** e têm natureza diferente dos seis snapshots gerais. Não há evidência apresentada de que o candidato M3 2.3 tenha sido diretamente ajustado pelos resultados dessas seis entidades; tampouco está comprovada sua ausência de exposição *indireta* ao ambiente geral de desenvolvimento. A igualdade de endereço de origem dos snapshots anteriores já impede denominá-las **instituições inéditas no projeto inteiro**.

### Escolha metodológica que precisa de revisor designado

**Caminho A — explicitar uma hipótese mais estreita:** amostra de instituições ausentes dos anteriores conjuntos *humanos cegos de M3*, mas **já conhecidas do corpus geral MAR**. Exige revisão documentada de eventuais decisões de engenharia/regra influenciadas por esse corpus, delimitação das inferências e atualização prospectiva e assinada do pré-registro antes de qualquer coleta nova. Não demonstra generalização para instituições inteiramente desconhecidas.

**Caminho B — manter uma hipótese de novidade institucional global:** redesenhar prospectivamente a seleção das entidades, com critérios anteriores à visita, evitando instituições existentes nos corpora e demais evidências de desenvolvimento. Requer novo quadro de elegibilidade e pré-registro aprovado; não permite substituir unidades após observar novas previsões ou usar os resultados para escolher alvos. Não se recomendam nomes de substitutas por desempenho.

Nenhum caminho foi aprovado automaticamente; a minuta computável anterior permanece inalterada e não selada.

## Triagem das 22 strings de testes

| Fonte versionada | Literais | Natureza verificada | Tratamento provisório |
| --- | ---: | --- | --- |
| `test_surface_typing.py` | 9 | Entradas de regressão do classificador M3; **7 são apenas fragmentos** de URLs concatenadas em Python | Não interpretar fragmentos como páginas completas. Recomenda-se reconstruir as 7 expressões e avaliar exclusão conservadora dos endereços reais usados nos testes, mediante assinatura do revisor. |
| `test_ai_surface_discovery.py` | 9 | URLs usadas por sessões HTTP simuladas, regras de escopo/robots e rejeição de mídia | Prova de teste do coletor, não de visita real nem de treino ou revisão de M3; não promover a exclusão comprovada automaticamente. |
| `test_estonian_film_archive_collection.py` | 1 | Ficha fictícia `Meediateek`, com parser Arkaader | Não prova alias da URL proposta. A plataforma Arkaader **já era conhecida** no MAR e a instituição já tinha corpus anterior; revisão em nível de plataforma/entidade é obrigatória. |
| `test_cinearchives_collection.py` | 3 | URLs em HTML fictício e teste do parser/metadata | Evidência de testes do coletor; não constitui prova de requisição HTTP ou alias de redirecionamento. |

Uma URL de teste não equivale a URL capturada, e uma URL parcial extraída de código não equivale à página usada no teste. Não há aqui nenhuma assinatura de revisor designado. No momento são **137 exclusões históricas comprovadas e 22 literais separados em triagem**, não 159 URLs comprovadamente visitadas nem 22 novos aliases. O inventário principal existente, que já contém os 117+20 e os 22 literais em categorias diferentes, não foi reescrito.

## Verificações e limites

`scripts/review_val009_methodology.py` faz duas modalidades: estrutura (22 itens, 7 fragmentos, seis alvos, bloqueio de selo, referências Git), e auditoria histórica completa em worktree no SHA fixado. O modo integral reutiliza a auditoria anterior dos 117+20, verifica a minuta antiga, relê metadata e tabelas dos seis corpora, atesta o Git blob efetivo e exige raiz e data coerentes. A presença de raízes nos registros históricos confirma **produção anterior de dados do corpus geral**; não reconstitui bytes HTTP ou evidencia treinamento do M3. A etiqueta `HOLD` permanece mesmo quando todos os testes passam.

**Pendências obrigatórias antes do selo:** reconstituir as 7 expressões concatenadas; obter decisão assinada para as 22 entradas e hipótese científica, auditar exposição indireta de design ao corpus global, aprovar inventário/aliases de forma prospectiva, fechar manual de anotação, designar custodiante e revisor distintos, implementar cofre restrito de previsões e testemunho autenticado. Nenhuma nova coleta, revisão cega ou previsão é autorizada por este PR.
