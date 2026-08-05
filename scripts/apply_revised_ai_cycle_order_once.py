#!/usr/bin/env python3
"""Aplica uma única vez a ordem aprovada entre preparação de IA e ciclo integral."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs" / "project" / "BACKLOG.md"
ROADMAP = ROOT / "docs" / "roadmap" / "infrastructure_execution_plan.md"
TECHNICAL = ROOT / "docs" / "digital-infrastructure-alignment" / "implementation_backlog.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Trecho não encontrado em {label}: {old[:100]!r}")
    return text.replace(old, new, 1)


def patch_backlog() -> None:
    text = BACKLOG.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "## P1 — primeiro ciclo operacional completo\n\n**Estado:** próxima prioridade executiva.\n",
        "## P1 — primeiro ciclo operacional completo\n\n**Estado:** execução autorizada após a preparação mínima da camada experimental de IA definida em P2A.\n\nO ciclo integral continua sendo o próximo grande marco empírico. Antes de iniciá-lo, porém, devem estar concluídos os contratos, o armazenamento separado, a execução opcional por feature flag e a amostra inicial de validação das três dimensões de IA. Essa antecipação evita nova coleta das mesmas superfícies sem tornar a IA dependência do baseline oficial.\n",
        "BACKLOG P1 estado",
    )

    text = replace_once(
        text,
        "### Ações\n\n1. executar ciclo integral dos 55 corpora ativos;\n2. manter falhas, ausências e estados não avaliáveis explicitamente registrados;\n3. gerar manifesto do ciclo completo;\n4. atualizar linha do tempo e resultados por corpus;\n5. verificar se todos os corpora ativos possuem snapshot e observation key;\n6. produzir relatório formal de validação operacional;\n7. congelar o primeiro baseline operacional completo.\n\n### Critério de conclusão\n\nTodos os 55 corpora ativos aparecem em um ciclo completo, com resultado, falha ou estado não avaliável auditável.\n",
        "### Ações\n\n1. confirmar que os contratos e campos das três dimensões de IA foram finalizados;\n2. confirmar armazenamento experimental separado e execução opcional por feature flag;\n3. confirmar a amostra inicial de validação antes de iniciar a rodada;\n4. executar o ciclo integral dos 55 corpora ativos;\n5. coletar simultaneamente os sinais experimentais de IA em modo sombra, sem alterar elegibilidade, denominadores ou indicadores oficiais;\n6. manter falhas, ausências e estados não avaliáveis explicitamente registrados;\n7. gerar manifesto do ciclo completo e registrar a configuração da feature flag;\n8. atualizar linha do tempo e resultados por corpus;\n9. verificar se todos os corpora ativos possuem snapshot e observation key;\n10. concluir e congelar o primeiro baseline operacional oficial sem depender da IA;\n11. preservar as evidências experimentais para revisão e recálculo posterior, sem necessidade de nova coleta integral.\n\n### Critério de conclusão\n\nTodos os 55 corpora ativos aparecem em um ciclo completo, com resultado, falha ou estado não avaliável auditável. O baseline oficial é reproduzível mesmo quando a IA está desativada ou falha, enquanto os sinais experimentais ficam preservados em armazenamento separado para validação posterior.\n",
        "BACKLOG P1 ações",
    )

    text = replace_once(
        text,
        "**Estado:** código existente; produtos operacionais incompletos.\n",
        "**Estado:** código existente; produtos operacionais incompletos. A materialização operacional será concluída com o baseline oficial posterior ao ciclo integral.\n",
        "BACKLOG P2 estado",
    )

    text = replace_once(
        text,
        "**Estado:** não implantado; protocolo de evidências de IA existente, metodologia, modelo, validação e integração analítica pendentes.\n",
        "**Estado:** prioridade executiva imediata antes do ciclo integral; implantação científica ainda pendente. O protocolo existe, mas contratos, armazenamento, feature flag, amostra, validação e integração analítica precisam ser implementados por fases.\n",
        "BACKLOG P2A estado",
    )

    marker = "Essas dimensões não podem compartilhar automaticamente o mesmo indicador, denominador ou conclusão. Um arquivo pode utilizar IA em transcrição ou restauração e não custodiar vídeos gerados por IA. Também pode custodiar vídeos sintéticos sem utilizar IA em seus próprios processos. A IA empregada pelo observatório nunca deverá ser atribuída ao arquivo analisado.\n\n"
    insertion = marker + """### Sequência de implantação aprovada

A ordem obrigatória para esta frente é:

1. finalizar os contratos e campos das três dimensões de IA;
2. implementar armazenamento separado e execução opcional por feature flag;
3. definir uma amostra inicial de validação;
4. executar o ciclo completo dos 55 corpora ativos;
5. coletar simultaneamente os sinais experimentais de IA;
6. concluir o baseline oficial sem depender da IA;
7. revisar humanamente a amostra;
8. calcular precisão, revocação, F1, matriz de confusão e erros por idioma;
9. decidir quais componentes de IA podem ser ativados;
10. recalcular somente os indicadores de IA a partir das evidências armazenadas.

A sequência divide a implementação em duas fases:

- **pré-ciclo e ciclo:** contratos, campos, armazenamento, feature flag, amostra e coleta experimental em modo sombra;
- **pós-baseline:** revisão humana, métricas, decisão de ativação e recálculo exclusivo dos indicadores de IA.

### Regras da execução opcional

- a feature flag deverá permanecer desativada por padrão fora das execuções controladas;
- a falha, indisponibilidade ou custo excessivo da IA não poderá interromper o ciclo oficial;
- as três dimensões deverão possuir flags, estados de execução e armazenamento distinguíveis;
- previsões experimentais não entram em numeradores, denominadores, elegibilidade ou publicação oficial;
- toda saída deverá registrar modelo, versão, configuração, prompt ou classificador, custo, duração e erro;
- o snapshot oficial deverá ser reproduzível sem dependência de fornecedor de IA;
- evidências textuais, estruturais e audiovisuais reutilizáveis deverão ser preservadas para permitir recálculo sem nova varredura integral;
- a ativação posterior deverá ocorrer por componente, e não como aprovação genérica de toda a camada de IA.

"""
    text = replace_once(text, marker, insertion, "BACKLOG sequência P2A")

    old_order = """## Ordem executiva atual

```text
Concluído: sincronizar e validar corpus, registro, fila e resumo europeus
1. Executar o ciclo completo dos 55 corpora ativos globais
2. Materializar validação controlada, analytics vivo, ledger e lotes
3. Modelar o corpus geral e os recortes geográficos versionados
4. Operacionalizar sondagem e elegibilidade da fila europeia
5. Desenvolver e validar separadamente: uso institucional de IA, IA de triagem do observatório e detecção de vídeos gerados ou modificados por IA
6. Simular e validar a política dos 20 corpora
7. Fechar a onda europeia
8. Consolidar a América do Norte
9. Preparar a fila da América Latina e Caribe
10. Manter descoberta preparatória de África, Ásia e Oceania
11. Ativar publicação derivada e entrega pública versionada
```
"""
    new_order = """## Ordem executiva atual

```text
Concluído: sincronizar e validar corpus, registro, fila e resumo europeus
1. Finalizar contratos e campos das três dimensões de IA
2. Implementar armazenamento separado e execução opcional por feature flag
3. Definir a amostra inicial de validação
4. Executar o ciclo completo dos 55 corpora ativos globais
5. Coletar simultaneamente os sinais experimentais de IA em modo sombra
6. Concluir o baseline oficial sem depender da IA, materializando analytics, histórico, ledger e lotes
7. Revisar humanamente a amostra de IA
8. Calcular precisão, revocação, F1, matriz de confusão e erros por idioma
9. Decidir quais componentes de IA podem ser ativados
10. Recalcular somente os indicadores de IA a partir das evidências armazenadas
11. Modelar o corpus geral e os recortes geográficos versionados
12. Operacionalizar sondagem e elegibilidade da fila europeia
13. Simular e validar a política dos 20 corpora
14. Fechar a onda europeia
15. Consolidar a América do Norte
16. Preparar a fila da América Latina e Caribe
17. Manter descoberta preparatória de África, Ásia e Oceania
18. Ativar publicação derivada e entrega pública versionada
```
"""
    text = replace_once(text, old_order, new_order, "BACKLOG ordem executiva")

    text = replace_once(
        text,
        "Novas funcionalidades não devem anteceder a execução dos módulos científicos e de governança que já existem. A prioridade é transformar código estrutural em um ciclo operacional completo, auditável e publicável.\n",
        "Novas funcionalidades não devem anteceder a execução dos módulos científicos e de governança que já existem. A única antecipação autorizada é a infraestrutura mínima de IA necessária para coletar sinais experimentais durante o ciclo e evitar nova varredura integral. A ativação científica da IA permanece posterior ao baseline oficial.\n",
        "BACKLOG regra final",
    )

    BACKLOG.write_text(text, encoding="utf-8")


def patch_roadmap() -> None:
    text = ROADMAP.read_text(encoding="utf-8")

    old_stage = """### Etapa 5 — Atualização integral dos corpora atuais

**Estado: próxima prioridade executiva.**

O corpus científico possui 58 entidades, das quais 55 estão ativas globalmente. O último ciclo, concluído em 21 de julho de 2026, foi parcial e processou somente `home-movies-memoryscapes`.

Não existe ciclo completo materializado para os 55 corpora ativos.

### Etapa 6 — Produtos e fila europeus
"""
    new_stage = """### Etapa 5 — Preparação experimental de IA antes do ciclo

**Estado: próxima prioridade executiva.**

Antes do novo ciclo devem ser finalizados:

- contratos e campos das três dimensões de IA;
- armazenamento experimental separado;
- execução opcional por feature flag;
- amostra inicial de validação.

A preparação existe para permitir coleta simultânea sem nova varredura integral. A IA permanece em modo sombra e não interfere em elegibilidade, denominadores, indicadores, falhas ou conclusão do baseline oficial.

### Etapa 6 — Atualização integral dos corpora atuais

**Estado: autorizada após a preparação mínima de IA.**

O corpus científico possui 58 entidades, das quais 55 estão ativas globalmente. O último ciclo, concluído em 21 de julho de 2026, foi parcial e processou somente `home-movies-memoryscapes`.

Não existe ciclo completo materializado para os 55 corpora ativos. A nova rodada coletará sinais experimentais de IA quando a feature flag estiver ativa, mas deverá concluir normalmente com a IA desativada ou indisponível.

### Etapa 7 — Produtos e fila europeus
"""
    text = replace_once(text, old_stage, new_stage, "ROADMAP etapas 5-7")

    old_order = """## Ordem executiva autorizada

1. executar o ciclo completo dos 55 corpora ativos globais;
2. materializar validação controlada, analytics operacional, histórico, ledger e lotes;
3. operacionalizar a sondagem e o gate da fila europeia;
4. criar revisão curatorial sem promoção automática;
5. simular e automatizar a política dos 20 corpora;
6. fechar a onda europeia;
7. consolidar a América do Norte;
8. preparar a fila da América Latina e Caribe.
"""
    new_order = """## Ordem executiva autorizada

1. finalizar contratos e campos das três dimensões de IA;
2. implementar armazenamento separado e execução opcional por feature flag;
3. definir a amostra inicial de validação;
4. executar o ciclo completo dos 55 corpora ativos globais;
5. coletar simultaneamente os sinais experimentais de IA;
6. concluir o baseline oficial sem depender da IA, materializando analytics, histórico, ledger e lotes;
7. revisar humanamente a amostra;
8. calcular precisão, revocação, F1, matriz de confusão e erros por idioma;
9. decidir quais componentes de IA podem ser ativados;
10. recalcular somente os indicadores de IA a partir das evidências armazenadas;
11. operacionalizar a sondagem e o gate da fila europeia;
12. criar revisão curatorial sem promoção automática;
13. simular e automatizar a política dos 20 corpora;
14. fechar a onda europeia;
15. consolidar a América do Norte;
16. preparar a fila da América Latina e Caribe.
"""
    text = replace_once(text, old_order, new_order, "ROADMAP ordem")

    text = replace_once(
        text,
        "- publicar observações sem revisão e ativação formal.\n",
        "- publicar observações sem revisão e ativação formal;\n- usar previsões experimentais de IA em indicadores oficiais antes da validação;\n- permitir que falha ou indisponibilidade da IA bloqueie o ciclo oficial.\n",
        "ROADMAP bloqueios",
    )

    text = replace_once(
        text,
        "## Próxima ação autorizada\n\nPreparar e executar o primeiro ciclo integral dos 55 corpora ativos globais. A operação da fila europeia permanece posterior à materialização desse baseline operacional completo.\n",
        "## Próxima ação autorizada\n\nFinalizar os contratos e campos das três dimensões de IA, implementar armazenamento experimental separado e execução opcional por feature flag e definir a amostra inicial de validação. Somente depois desses três portões será iniciado o ciclo integral dos 55 corpora, com coleta de IA em modo sombra e baseline oficial independente.\n",
        "ROADMAP próxima ação",
    )

    ROADMAP.write_text(text, encoding="utf-8")


def patch_technical() -> None:
    text = TECHNICAL.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "| Corpus operacional | ativo parcialmente | 55 entidades ativas globais | primeiro ciclo completo dos 55 corpora |\n",
        "| Corpus operacional | ativo parcialmente | 55 entidades ativas globais | primeiro ciclo completo após preparação mínima de IA |\n| IA experimental | protocolo documentado | três dimensões separadas e regras de cautela | contratos, armazenamento, feature flag, amostra, coleta sombra e validação |\n",
        "TECH tabela",
    )

    marker = "## T1 — execução integral do organismo\n\n**Estado:** próximo portão técnico.\n"
    insertion = """## T0A — preparação experimental de IA antes do ciclo

**Estado:** próximo portão técnico.

A preparação deverá ser mínima, modular e incapaz de bloquear o pipeline oficial.

1. finalizar contratos e campos das três dimensões de IA;
2. separar uso institucional de IA, IA de triagem do observatório e vídeo gerado ou modificado por IA;
3. implementar armazenamento append-only ou versionado para previsões e evidências;
4. implementar feature flags independentes, desativadas por padrão;
5. registrar modelo, versão, configuração, prompt, custo, duração, erro e proveniência;
6. garantir que falha da IA não altere o status do ciclo oficial;
7. definir amostra inicial multilíngue e geograficamente diversa;
8. preparar recálculo posterior sem nova coleta integral.

## T1 — execução integral do organismo

**Estado:** executa após T0A.
"""
    text = replace_once(text, marker, insertion, "TECH T0A/T1")

    text = replace_once(
        text,
        "1. executar todos os 55 corpora ativos em um ciclo completo;\n2. registrar sucesso, falha e não avaliabilidade sem exclusão silenciosa;\n3. atualizar manifesto, linha do tempo e resultados do ciclo;\n4. verificar snapshots e observation keys por corpus;\n5. congelar o primeiro baseline operacional completo.\n",
        "1. executar todos os 55 corpora ativos em um ciclo completo;\n2. coletar sinais experimentais de IA quando as flags controladas estiverem ativas;\n3. registrar sucesso, falha e não avaliabilidade sem exclusão silenciosa;\n4. registrar separadamente falhas e custos das tarefas de IA;\n5. atualizar manifesto, linha do tempo e resultados do ciclo;\n6. verificar snapshots e observation keys por corpus;\n7. congelar o primeiro baseline operacional completo sem dependência da IA;\n8. preservar evidências para revisão e recálculo posterior.\n",
        "TECH T1 ações",
    )

    marker_t2 = "## T3 — fila europeia\n"
    insert_t2a = """## T2A — validação pós-baseline dos componentes de IA

**Estado:** posterior ao ciclo e ao baseline oficial.

1. revisar humanamente a amostra inicial;
2. calcular precisão, revocação, F1 e matriz de confusão por tarefa;
3. medir falsos positivos e falsos negativos por idioma, continente e tipo de instituição;
4. avaliar estabilidade entre versões, custo, tempo e dependência de fornecedor;
5. decidir separadamente quais componentes podem ser ativados;
6. registrar metodologia e indicador somente após aprovação científica;
7. recalcular apenas os indicadores de IA usando as evidências armazenadas;
8. não repetir a coleta integral salvo insuficiência documentada das evidências.

## T3 — fila europeia
"""
    text = replace_once(text, marker_t2, insert_t2a, "TECH T2A")

    text = replace_once(
        text,
        "## Fora do primeiro ciclo operacional\n\n- inferência automática de contratos;\n- classificação autônoma de riscos por IA;\n",
        "## Fora do primeiro ciclo operacional\n\nA coleta experimental de sinais de IA poderá acompanhar o ciclo. Permanecem fora do primeiro baseline oficial:\n\n- ativação pública dos indicadores de IA;\n- decisões automáticas baseadas em previsões de IA;\n- inferência automática de contratos;\n- classificação autônoma de riscos por IA;\n",
        "TECH fora do ciclo",
    )

    old_gate = """## Próximo portão técnico

```text
Concluído: regenerar e validar os produtos europeus
1. Executar o ciclo completo dos 55 corpora ativos globais
2. Materializar analytics, histórico, ledger e lotes
3. Executar sondagem e elegibilidade europeias
4. Abrir revisão curatorial controlada
```
"""
    new_gate = """## Próximo portão técnico

```text
Concluído: regenerar e validar os produtos europeus
1. Finalizar contratos e campos das três dimensões de IA
2. Implementar armazenamento separado e feature flags
3. Definir a amostra inicial de validação
4. Executar o ciclo completo dos 55 corpora ativos
5. Coletar sinais experimentais de IA em modo sombra
6. Materializar o baseline oficial, analytics, histórico, ledger e lotes sem dependência da IA
7. Revisar a amostra e calcular métricas por idioma
8. Decidir ativações por componente
9. Recalcular somente os indicadores de IA com as evidências armazenadas
10. Executar sondagem e elegibilidade europeias
11. Abrir revisão curatorial controlada
```
"""
    text = replace_once(text, old_gate, new_gate, "TECH próximo portão")

    TECHNICAL.write_text(text, encoding="utf-8")


def main() -> None:
    patch_backlog()
    patch_roadmap()
    patch_technical()
    print("Ordem revisada de IA e ciclo aplicada aos três documentos.")


if __name__ == "__main__":
    main()
