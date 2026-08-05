# Auditoria da política de integração e expansão continental

**Data de referência:** 5 de agosto de 2026  
**Branch auditada:** `presentation/rpv-1`

## 1. Objetivo

Esta auditoria verifica:

- a política vigente de integração entre código, artefatos científicos e interface pública;
- o estado real das filas de expansão;
- a existência ou ausência de uma sequência continental formal;
- componentes implementados em código que ainda não foram operacionalmente materializados ou conectados à aplicação;
- prioridades que devem anteceder a abertura de uma nova frente continental.

## 2. Política de integração vigente

A arquitetura estabelece separação entre:

1. coleta e sondagem técnica;
2. evidência e proveniência;
3. validação e integridade;
4. decisão curatorial;
5. incorporação no corpus canônico;
6. snapshots e analytics;
7. revisão de publicação;
8. visão pública derivada.

A interface pública deve ser integrada diretamente em `app/streamlit_app.py`. Workflows podem validar, executar, materializar e publicar artefatos, mas não devem funcionar como mecanismo permanente de edição do código-fonte da interface.

Nenhuma fila pode promover automaticamente uma unidade para `CORPORA`. A sondagem técnica, o gate de elegibilidade e a decisão curatorial permanecem etapas separadas.

## 3. Estado canônico do corpus

O manifesto científico de referência registra:

- 58 entidades no corpus de referência;
- versão do manifesto: `1.0.0`;
- estado congelado;
- branch científica: `presentation/rpv-1`.

O inventário derivado atual registra:

- 58 entidades totais;
- 55 entidades ativas globais;
- 3 entidades inativas;
- 7 agregadores;
- 51 arquivos ou instituições.

O recorte europeu dos produtos `observatorio_*_pesquisa_europa.csv` contém 54 corpora ativos. O corpus ativo global adicional é o American Archive of Public Broadcasting — AAPB, incorporado como primeiro corpus norte-americano.

Consequentemente, devem permanecer distintos:

- **corpus de referência:** 58 entidades;
- **corpus operacional ativo global:** 55 entidades;
- **corpus operacional ativo europeu:** 54 entidades;
- **corpus operacional ativo extraeuropeu:** 1 entidade, o AAPB;
- **unidades incorporáveis em fila:** somente candidatas que concluírem o gate e a revisão humana.

## 4. Estado dos ciclos operacionais

O último ciclo registrado foi concluído em **21 de julho de 2026** e teve escopo parcial:

- 55 corpora ativos globais declarados;
- 1 corpus selecionado;
- `home-movies-memoryscapes` processado com sucesso.

A linha do tempo contém apenas ciclos parciais. Não existe ciclo completo materializado para os 55 corpora ativos.

A leitura dos códigos únicos da linha do tempo mostra 36 corpora com alguma execução registrada. Portanto, 19 dos 55 corpora ativos não possuem evidência de participação nessa linha do tempo operacional.

Esse número não significa que os 19 corpora não possuam dados. Significa apenas que o histórico de ciclos não demonstra uma execução controlada deles dentro do mecanismo mensal atual.

## 5. Fila europeia

### 5.1 Fila operacional atual

A fila mais recente é:

`data/output/observatorio_fila_pesquisa_europa.csv`

Características:

- regra: `2026-05-pesquisa-europa-v3`;
- 118 registros;
- 24 campos;
- ranking operacional explícito;
- separação entre fontes de descoberta e candidatos individuais.

Os cinco primeiros registros são fontes de fila:

1. EUscreen Network — membros;
2. European Film Gateway — contributing archives;
3. FIAF — membros europeus;
4. FIAT/IFTA — membros;
5. INEDITS — membros.

Essas fontes não entram diretamente como corpus. Elas geram candidatos individuais verificáveis.

O resumo europeu registra:

- 54 corpora ativos europeus;
- 73 candidatos na fila definitiva um a um:
  - 38 arquivos audiovisuais individuais;
  - 10 instituições audiovisuais europeias;
  - 25 instituições televisivas com acervo audiovisual;
- 30 agregadores nacionais ou regionais em radar;
- 8 agregadores temáticos em radar contextual;
- 5 fontes de fila;
- protocolos de negativa, não incorporação, ingestão pendente e monitoramento.

### 5.2 Fila de fechamento antiga

O arquivo:

`data/output/observatorio_fila_fechamento_europa.csv`

possui apenas 6 registros e usa a regra `2026-05-fechamento-europa-v1`.

Ele deve ser tratado como artefato histórico de fechamento, não como fila operacional vigente.

### 5.3 Validação dos denominadores e produtos

A comparação inicial entre 54 corpora no resumo europeu e 55 no inventário global foi reavaliada contra o código canônico.

O resultado correto é:

```text
55 corpora ativos globais
= 54 corpora ativos europeus
+ 1 corpus ativo norte-americano — AAPB
```

Portanto, não havia divergência nos três produtos europeus.

A ação de regeneração foi executada pelo gerador canônico e não produziu alterações nos CSVs, confirmando que os arquivos materializados já correspondiam ao estado atual do código.

Foi criado `scripts/sync_europe_research_outputs.py`, que:

- regenera os três produtos;
- oferece modo `--check` sem escrita;
- compara semanticamente arquivos materializados e DataFrames esperados;
- valida códigos ativos europeus contra o recorte canônico;
- impede entrada silenciosa de corpora extraeuropeus no denominador europeu;
- verifica duplicidades, versão da regra e continuidade do ranking;
- falha quando o resumo, a fila ou o registro ficam desatualizados.

O workflow `Quality Checks` passou a executar essa validação obrigatoriamente.

## 6. Código implementado sem operacionalização completa

### 6.1 Sondagem e elegibilidade da fila europeia

Código existente:

- `src/memoria_audiovisual/digital_infrastructure/european_queue.py`;
- `src/memoria_audiovisual/digital_infrastructure/queue_probe.py`;
- `scripts/probe_european_queue.py`;
- `scripts/evaluate_european_queue.py`;
- testes de elegibilidade e sondagem.

Estado:

- implementado e testado estruturalmente;
- não existe workflow operacional da fila;
- não existe `observatorio_sondagem_tecnica_fila_europa.json` materializado;
- não existem `observatorio_elegibilidade_fila_europa.json` e `.csv` materializados;
- a interface apresenta a fila bruta, mas não o resultado do gate;
- nenhuma promoção automática é permitida.

### 6.2 Validação controlada e analytics ao vivo

Existe workflow para executar três corpora reais (`europeana`, `ina`, `bfi`) e nove indicadores.

Estado:

- workflow codificado;
- `data/output/controlled_validation_summary.json` não está materializado;
- não há snapshot analítico operacional persistido em `data/output/analytics/<snapshot>`;
- `data/output/analytics/indicator_history.jsonl` não está materializado.

A Infraestrutura Científica atualmente consegue apresentar os resultados congelados do corpus de referência, mas não possui uma série analítica operacional viva.

### 6.3 Governança persistente

Os carregadores e módulos esperam:

- `data/digital_infrastructure/ledger.jsonl`;
- `data/digital_infrastructure/ingestion_batches.jsonl`.

Esses artefatos não estão materializados na branch auditada.

### 6.4 Publicação derivada

Código existente:

- registro de publicação ativa;
- revisão de publicação;
- visão pública derivada;
- projeção de entrega pública;
- manifestos e histórico de ativações.

Estado:

- implementado estruturalmente;
- não conectado ao Streamlit;
- sem workflow operacional de ativação e entrega;
- sem registro público ativo materializado;
- sem API pública somente leitura.

### 6.5 Memória longitudinal

Código de snapshots, comparação, triagem e revisão temporal existe.

Estado:

- ciclos parciais históricos existem;
- não há primeiro ciclo integral dos 55 corpora;
- não há dois snapshots oficiais completos e comparáveis;
- a validação longitudinal oficial permanece pendente.

## 7. Sequência continental

Não havia sequência formal registrada depois da Europa. A documentação apenas determinava:

- Europa como primeiro recorte;
- agregadores antes de instituições individuais;
- expansão internacional posterior.

O AAPB já funciona como primeiro corpus extraeuropeu e estabelece um início de observação da América do Norte. Iberarchivos permanece como fonte de radar ibero-americana, sem catálogo audiovisual comparável para incorporação direta.

### Sequência operacional provisória

A sequência recomendada para ondas de ativação é:

0. consolidação do baseline atual, sem novas incorporações;
1. Europa;
2. América do Norte;
3. América Latina e Caribe;
4. África;
5. Ásia;
6. Oceania.

Fontes mundiais, supranacionais ou transcontinentais devem permanecer em uma fila transversal e não contar automaticamente para o limiar de um continente.

### Justificativa

- a Europa já concentra a infraestrutura e a fila mais desenvolvidas;
- a América do Norte já foi iniciada pelo AAPB;
- América Latina e Caribe possuem aderência linguística e científica à plataforma, além de fonte de radar já documentada;
- a África deve anteceder novas expansões orientadas apenas pela facilidade técnica, reduzindo o risco de perpetuar concentração europeia e norte-americana;
- Ásia e Oceania exigem inventários próprios de agregadores, idiomas, regimes de acesso e fontes institucionais.

A ordem pode ser ajustada após inventário comparável de fontes, mas não deve ser alterada apenas porque uma região oferece coleta tecnicamente mais fácil.

## 8. Regra de operação por continente

A descoberta pode ocorrer em paralelo para todas as regiões. A ativação de uma nova onda continental, porém, depende de:

1. corpus canônico e filas sincronizados;
2. ciclo integral dos corpora ativos concluído;
3. snapshot, cobertura e analytics materializados;
4. ledger e lote de ingestão registrados;
5. fila regional com ranking, evidências e proveniência;
6. sondagem técnica concluída;
7. gate de elegibilidade executado;
8. revisão curatorial humana;
9. ausência de bloqueio de integridade;
10. baseline anterior preservado e publicável.

O limiar de 20 corpora deve considerar somente unidades aprovadas e validadas. Registros em radar, fontes de descoberta, duplicados, não avaliáveis, negativos ou pendentes não contam.

## 9. Ordem recomendada de execução

### P0 — consistência do estado atual

**Concluído nesta rodada.**

- três produtos europeus regenerados;
- ausência de diferença confirmada;
- recortes global e europeu explicitados;
- sincronizador e validação `--check` implementados;
- ranking, códigos, versões e denominadores protegidos no CI;
- fila de fechamento v1 mantida como histórica.

### P1 — ciclo integral e baseline operacional

1. executar um ciclo completo dos 55 corpora ativos;
2. registrar falhas e estados não avaliáveis sem removê-los silenciosamente;
3. materializar cobertura, snapshot analítico, manifesto e nove indicadores;
4. iniciar histórico de indicadores, ledger e lotes de ingestão;
5. produzir relatório formal de validação operacional.

### P2 — operacionalização segura da fila europeia

1. criar workflow manual e reiniciável para sondagem, com `limit`, `resume` e timeout;
2. materializar resultados técnicos;
3. executar o gate de elegibilidade;
4. apresentar contagens e estados na interface;
5. criar fila de revisão humana;
6. incorporar apenas lotes aprovados, sem alteração automática de `CORPORA`.

### P3 — política dos 20 corpora

1. simular o limiar usando a fila europeia real;
2. contar somente candidatos aprovados;
3. definir prazo máximo sem atingir 20;
4. definir regras para fontes transcontinentais;
5. gerar relatório de prontidão por região;
6. integrar o gatilho aos snapshots, analytics e publicação.

### P4 — próxima onda continental

Somente após P0–P3:

1. consolidar a América do Norte;
2. criar inventário e fila da América Latina e Caribe;
3. manter pesquisa preparatória das demais regiões sem ativação prematura.

## 10. Conclusão

A sincronização dos produtos europeus foi concluída e o aparente conflito 54/55 foi resolvido como diferença legítima entre denominador europeu e denominador global.

A plataforma possui mais código científico e de governança do que produtos operacionais materializados. A próxima prioridade correta é executar o primeiro ciclo completo dos 55 corpora ativos e produzir um baseline operacional auditável antes de operacionalizar a fila europeia ou abrir nova expansão continental.
