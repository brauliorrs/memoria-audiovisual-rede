# Engenharia operacional do MAR: corpus contínuo + instrumentos validados

**Política de arquitetura vigente a partir de 30/09/2026.**

O MAR passa a operar em duas trilhas independentes e coordenadas:

1. **Trilha do corpus:** identificação, priorização, incorporação, atualização, checks e snapshots de instituições e agregadores;
2. **Trilha dos instrumentos:** desenvolvimento, validação, documentação e eventual promoção de ferramentas analíticas.

A expansão do corpus **não fica bloqueada** porque M3, M4 ou outra ferramenta ainda está em desenvolvimento. Reciprocamente, uma ferramenta experimental **não entra na produção** apenas porque seu código existe ou seus testes unitários passam.

## 1. Fluxo operacional

```text
FILA DE INCLUSÃO
      |
      v
sondagem -> gate de inclusão -> pipeline do corpus -> check -> corpus ativo/snapshot
                                                   |
                                                   v
                                  instrumentos de produção admitidos
                                                   |
                                                   v
                                      produtos analíticos descritivos

LABORATÓRIO DE INSTRUMENTOS
      |
implementação -> testes -> validação de eficácia -> documentação -> decisão de promoção
                                                           |
                                                           +--> registro production
                                                           +--> continua experimental
```

## 2. Regra de inclusão de novos corpora

A ordem de trabalho vem de `observatorio_fila_pesquisa_europa.csv`. O seletor
`memoria_audiovisual.inclusion_queue` apenas materializa os próximos candidatos
que já estejam na camada `fila_definitiva_um_por_um`, com decisão
`avaliar_arquivo_individual_um_por_um`.

Ele **não incorpora automaticamente** nenhuma instituição.

Cada candidato continua obrigado a satisfazer seu `inclusion_gate`, normalmente
por prova de rota pública audiovisual, metadados adequados ou catálogo coletável.
A incorporação exige pipeline próprio, outputs, snapshot e checks.

Comandos:

```bash
python scripts/next_inclusion_candidate.py --limit 3
python scripts/run_observatory_cycle.py
```

O primeiro comando agenda trabalho; o segundo executa corpora já ativos. A passagem
de candidato para corpus ativo continua sendo uma decisão metodológica versionada.

## 3. Regra de instrumentos analíticos

O registro canônico está em
[`analysis-instrument-registry.json`](../methodology/analysis-instrument-registry.json).

Há três estados:

- `production`: pode ser executado no ciclo oficial dentro do escopo validado;
- `evidence_capture_only`: pode coletar evidência para revisão, mas não publicar
  automaticamente uma conclusão científica;
- `experimental`: isolado da produção.

O executor `scripts/run_approved_analysis.py` rejeita, em modo fail-closed,
instrumentos experimentais ou não registrados.

### Produção atual

Dois instrumentos entram na análise automática após **um ciclo completo e bem
sucedido** dos corpora:

- auditoria descritiva de acesso restrito;
- indicador de registros públicos materializados.

Sua eficácia e seus limites estão documentados em
[`validated-analysis-instruments.md`](../methodology/validated-analysis-instruments.md).

A auditoria de infraestrutura digital permanece como **captura de evidência**:
pode rodar em processo próprio e alimentar revisão humana, mas uma detecção
heurística não vira afirmação institucional automaticamente.

M3, M4, avaliação de relevância da busca e índice composto de visibilidade
permanecem experimentais.

## 4. Ordem correta do ciclo

O `run_observatory_cycle.py` agora:

1. atualiza registros, filas e protocolos operacionais;
2. materializa os próximos candidatos da fila sem incorporá-los;
3. atualiza e checa os corpora ativos;
4. grava manifesto/histórico do ciclo;
5. **somente em refresh global completo sem falhas**, executa os instrumentos
   `production + default_cycle`;
6. em refresh parcial ou com falha, grava manifesto explícito de análise
   `skipped`, evitando recalcular um indicador global com mistura de datas.

Isso corrige a ordem anterior, em que derivados analíticos podiam ser recalculados
antes do refresh dos corpora.

## 5. Promoção de ferramenta

Uma nova ferramenta só entra em produção depois de existir, no Git:

- propósito e unidade de análise;
- versão do algoritmo/regra;
- protocolo ou método de validação;
- resultado de eficácia adequado à tarefa;
- documentação de falsos positivos, falsos negativos ou outros modos de falha;
- escopo permitido de inferência;
- inferências proibidas;
- testes de contrato;
- definição das saídas;
- entrada no registro com `lifecycle=production`;
- CI verde no mesmo commit/PR.

**Testes de software não substituem validação de eficácia.** Para transformação
determinística, eficácia pode ser demonstrada como conformidade com regras explícitas
e casos de borda. Para classificadores ou busca/ranking, exige referência humana ou
outro desenho empírico apropriado.

## 6. Continuidade paralela

A partir desta arquitetura, o planejamento padrão é:

- sempre manter ao menos um item da fila de corpus em engenharia/sondagem;
- desenvolver ferramentas experimentais em branches/protocolos próprios;
- não esperar uma ferramenta experimental para incorporar o próximo corpus;
- não usar uma ferramenta experimental para gerar coluna/indicador público;
- promover ferramentas individualmente após validação e documentação.

Esse desenho preserva o crescimento científico do observatório sem congelar a
engenharia e evita que experimentos ainda incertos contaminem os produtos públicos.
