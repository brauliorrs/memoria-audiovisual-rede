#!/usr/bin/env python3
"""Ajuste único do backlog e do protocolo para separar os objetos de IA."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKLOG_PATH = ROOT / "docs" / "project" / "BACKLOG.md"
PROTOCOL_PATH = ROOT / "docs" / "digital-infrastructure-alignment" / "ai_systems_protocol.md"


def patch_backlog() -> None:
    text = BACKLOG_PATH.read_text(encoding="utf-8")

    old_heading = "## P2A — indicador experimental de IA para detecção de acervo e presença de vídeo"
    new_heading = "## P2A — indicadores experimentais relacionados à inteligência artificial"
    if old_heading not in text:
        raise SystemExit("P2A heading not found")
    text = text.replace(old_heading, new_heading, 1)

    marker = "`docs/digital-infrastructure-alignment/ai_systems_protocol.md`\n\nO componente não deverá ser implementado como uma única classificação genérica."
    insertion = """`docs/digital-infrastructure-alignment/ai_systems_protocol.md`

### Separação obrigatória dos objetos de IA

A plataforma deverá manter três dimensões científicas independentes:

1. **uso institucional de ferramentas de IA pelo arquivo ou agregador** — verifica se a instituição declara ou documenta uso de IA, quais ferramentas, modelos ou fornecedores utiliza, para quais funções e em qual estágio de implantação;
2. **uso de IA pela própria plataforma para detectar acervo audiovisual e presença pública de vídeo** — mecanismo de apoio à triagem do observatório, sem atribuir esse uso à instituição observada;
3. **detecção de vídeos gerados, sintetizados ou materialmente modificados por IA** — classificação aplicada ao item audiovisual, à versão ou ao segmento, e não à instituição como um todo.

Essas dimensões não podem compartilhar automaticamente o mesmo indicador, denominador ou conclusão. Um arquivo pode utilizar IA em transcrição ou restauração e não custodiar vídeos gerados por IA. Também pode custodiar vídeos sintéticos sem utilizar IA em seus próprios processos. A IA empregada pelo observatório nunca deverá ser atribuída ao arquivo analisado.

### P2A.1 — presença institucional de ferramentas de IA e identificação das ferramentas

A plataforma deverá verificar separadamente:

- se existe evidência pública de uso institucional de IA ou aprendizado de máquina;
- quais ferramentas, sistemas, modelos, fornecedores ou componentes são mencionados;
- quais funções são desempenhadas, como transcrição, OCR, tradução, reconhecimento de imagem, descrição automática, enriquecimento de metadados, extração de entidades, busca, recomendação, detecção de direitos, restauração, colorização, geração de conteúdo ou moderação;
- se o uso está anunciado, em pesquisa, em piloto, operacional ou descontinuado;
- se há supervisão humana, documentação, transparência e mecanismo de contestação.

A presença de uma biblioteca, CDN, componente genérico ou linguagem promocional não constitui prova de uso institucional de IA. Nome, fornecedor, versão, função, estágio, fonte pública e data da evidência deverão ser preservados. Quando a ferramenta não puder ser identificada, o campo permanecerá desconhecido.

Estados mínimos:

- `verified_institutional_ai_use`;
- `detected_pending_review`;
- `declared_without_technical_detail`;
- `ambiguous`;
- `not_identified_on_assessed_surfaces`;
- `not_assessable`;
- `error`;
- `discontinued`;
- `withdrawn_or_corrected`.

`not_identified_on_assessed_surfaces` não significa que a instituição não utiliza IA. Significa apenas que o procedimento declarado não encontrou evidência pública suficiente.

### P2A.2 — IA da plataforma para detectar acervo e presença pública de vídeo

O componente não deverá ser implementado como uma única classificação genérica."""
    if marker not in text:
        raise SystemExit("P2A insertion marker not found")
    text = text.replace(marker, insertion, 1)

    products_marker = "### Produtos a implementar\n\n1. definir dois contratos independentes de classificação;"
    synthetic_section = """### P2A.3 — detecção de vídeos gerados ou modificados por IA

Este eixo deverá analisar a origem e o processo de produção do conteúdo audiovisual observado, independentemente do uso institucional de IA.

As classes deverão permanecer separadas:

- `declared_fully_ai_generated_video` — vídeo declarado como integralmente gerado ou sintetizado por IA;
- `declared_partially_ai_generated_video` — partes visuais ou sonoras foram geradas por IA;
- `declared_ai_assisted_production` — IA auxiliou roteiro, edição, composição ou outro estágio sem caracterizar necessariamente geração do vídeo;
- `ai_restored_or_enhanced_video` — restauração, interpolação, redução de ruído, colorização ou aumento de resolução;
- `synthetic_voice_or_audio` — voz, fala, música ou efeitos sonoros sintéticos;
- `synthetic_image_or_avatar` — imagens, personagens, avatares ou cenas sintéticas;
- `suspected_ai_generated_pending_review` — sinal técnico ou visual ainda não confirmado;
- `no_public_evidence_of_ai_generation`;
- `not_assessable`;
- `error`;
- `withdrawn_or_corrected`.

Restauração, colorização, transcrição, recomendação ou enriquecimento de metadados não deverão ser classificados automaticamente como “vídeo feito por IA”. O indicador deverá distinguir geração integral, geração parcial, assistência de produção, modificação material e uso de IA apenas em processos auxiliares.

A classificação deverá priorizar:

1. declaração explícita do produtor, arquivo, catálogo ou detentor responsável;
2. metadados de proveniência, credenciais de conteúdo ou documentação técnica verificável;
3. ficha catalográfica, créditos, notas de produção ou documentação de aquisição;
4. marca d’água, identificador ou informação técnica associada ao conteúdo;
5. análise forense ou detector automatizado validado;
6. avaliação humana especializada.

Nenhum detector probabilístico poderá, isoladamente, produzir a afirmação pública de que um vídeo foi gerado por IA. A confiança do modelo será evidência de triagem, não prova de autoria ou processo de produção.

A unidade de análise poderá ser o item completo, uma versão, um segmento temporal, uma faixa de áudio, um quadro ou um elemento sintético incorporado. A presença de um elemento sintético não autoriza classificar automaticamente todo o vídeo como integralmente gerado por IA.

### Produtos a implementar

1. definir três contratos independentes: uso institucional de IA, IA de triagem do observatório e detecção de vídeo sintético;"""
    if products_marker not in text:
        raise SystemExit("P2A products marker not found")
    text = text.replace(products_marker, synthetic_section, 1)

    text = text.replace(
        "2. criar conjunto de treinamento e avaliação com proveniência e licença compatíveis;",
        "2. criar vocabulário controlado de ferramentas, funções e estágios institucionais;\n3. criar vocabulário controlado de geração, assistência, restauração e modificação audiovisual;\n4. criar conjuntos de treinamento e avaliação independentes, com proveniência e licença compatíveis;",
        1,
    )
    for old, new in [
        ("3. implementar baseline determinístico para comparação;", "5. implementar baseline determinístico e documental para comparação;"),
        ("4. testar classificador textual multilíngue;", "6. testar classificador textual multilíngue;"),
        ("5. testar detecção estrutural de players, embeds e formatos de vídeo;", "7. testar detecção estrutural de players, embeds e formatos de vídeo;"),
        ("6. avaliar, em etapa separada, se análise visual de miniaturas agrega valor mensurável;", "8. avaliar detectores de conteúdo sintético e, em etapa separada, se análise visual agrega valor mensurável;"),
        ("7. criar fila de revisão humana e interface de confirmação;", "9. criar fila de revisão humana e interface de confirmação;"),
        ("8. persistir evidências, confiança, versão do modelo e decisão final;", "10. persistir evidências, confiança, versão do modelo e decisão final;"),
        ("9. produzir relatório de desempenho por idioma, continente e tipo de instituição;", "11. produzir relatórios separados por tarefa, idioma, continente e tipo de instituição;"),
        ("10. executar estudo de sensibilidade de limiares;", "12. executar estudo de sensibilidade de limiares;"),
        ("11. integrar o resultado validado aos snapshots sem sobrescrever observações históricas;", "13. integrar os resultados validados aos snapshots sem sobrescrever observações históricas;"),
        ("12. criar visualização que separe previsão automática, evidência verificada e resultado não avaliável;", "14. criar visualizações que não misturem adoção institucional, triagem automatizada e vídeo sintético;"),
        ("13. documentar a metodologia no livro científico antes da ativação pública;", "15. documentar as três metodologias no livro científico antes da ativação pública;"),
        ("14. manter o indicador desativado no catálogo analítico até o cumprimento dos critérios de validação.", "16. manter os indicadores desativados no catálogo analítico até o cumprimento dos critérios específicos de validação."),
    ]:
        if old not in text:
            raise SystemExit(f"Expected product item not found: {old}")
        text = text.replace(old, new, 1)

    old_conclusion = "O indicador somente poderá ser considerado implantado quando as duas tarefas forem avaliadas separadamente em amostra multilíngue e geograficamente diversa, alcançarem desempenho mínimo previamente definido, preservarem evidência reproduzível, tiverem revisão humana operacional e estiverem registradas com metodologia e versões próprias. Até esse ponto, qualquer resultado será tratado como experimento de apoio à triagem, não como medida científica publicada."
    new_conclusion = """A implantação somente será considerada concluída quando a plataforma conseguir responder separadamente:

1. se há evidência pública de que o arquivo utiliza ferramentas de IA, quais são e para quais funções;
2. se a IA do observatório identificou evidência de acervo audiovisual ou presença pública de vídeo, com revisão humana;
3. se um item, versão ou segmento audiovisual possui evidência verificável de geração ou modificação por IA, distinguindo geração integral, geração parcial, assistência e restauração.

As três tarefas deverão possuir amostras de validação, métricas, metodologias e versões próprias. Até esse ponto, os resultados permanecerão experimentais e não poderão fundamentar afirmações públicas conclusivas sobre uma instituição ou um vídeo."""
    if old_conclusion not in text:
        raise SystemExit("P2A conclusion not found")
    text = text.replace(old_conclusion, new_conclusion, 1)

    old_order = "5. Desenvolver e validar experimentalmente a detecção por IA de acervo e presença de vídeo"
    new_order = "5. Desenvolver e validar separadamente: uso institucional de IA, IA de triagem do observatório e detecção de vídeos gerados ou modificados por IA"
    if old_order not in text:
        raise SystemExit("Executive order item not found")
    text = text.replace(old_order, new_order, 1)

    BACKLOG_PATH.write_text(text, encoding="utf-8")


def patch_protocol() -> None:
    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    marker = "## Unidade de observação\n"
    addition = """## Separação obrigatória dos objetos de IA

O projeto distingue três objetos que não podem compartilhar automaticamente o mesmo indicador ou denominador:

1. **IA utilizada pela instituição** — sistemas e ferramentas empregados pelo arquivo ou agregador e suas funções;
2. **IA utilizada pelo observatório** — modelos empregados para apoiar triagem, detecção de acervo e localização de vídeo público;
3. **conteúdo audiovisual gerado ou modificado por IA** — propriedade observada em um item, versão, segmento, faixa de áudio ou elemento visual.

Uso institucional de IA não prova que a instituição custodie vídeos gerados por IA. Presença de vídeos sintéticos não prova que o arquivo utilize IA em seus processos. IA usada pelo observatório para detectar evidências não deve ser atribuída à instituição observada.

Restauração, colorização, transcrição, recomendação e enriquecimento de metadados devem permanecer separados da geração sintética do conteúdo. Detectores probabilísticos de vídeo sintético servem para triagem e não podem, isoladamente, sustentar afirmação pública conclusiva.

"""
    if addition in text:
        return
    if marker not in text:
        raise SystemExit("Protocol marker not found")
    text = text.replace(marker, addition + marker, 1)
    PROTOCOL_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    patch_backlog()
    patch_protocol()


if __name__ == "__main__":
    main()
