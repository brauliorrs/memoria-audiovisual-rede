"""Migra a aba de indicadores para o modelo semântico canônico.

A transformação é idempotente e recusa estruturas desconhecidas para evitar
edições parciais no módulo Streamlit.
"""

from __future__ import annotations

import argparse
from pathlib import Path


TARGET = Path("src/memoria_audiovisual/ui/scientific_infrastructure.py")

IMPORT_ANCHOR = """from memoria_audiovisual.scientific_infrastructure import (\n    LoadedArtifact,\n    ScientificInfrastructureLoader,\n    build_default_registry,\n)\n"""
IMPORT_REPLACEMENT = IMPORT_ANCHOR + """from memoria_audiovisual.ui.indicator_presentation import (\n    build_indicator_presentations,\n    registry_summary,\n)\n"""

OLD_START = "def _render_indicator_catalog("
OLD_END = "\n\ndef _render_methodology("

NEW_FUNCTION = '''def _render_indicator_registry(\n    registry_payload: dict[str, Any],\n    methodologies_by_id: dict[str, dict[str, Any]],\n) -> None:\n    st.subheader("Indicadores científicos")\n    st.caption(\n        "O registro apresenta o que a plataforma mede. Conceito, método e "\n        "resultado permanecem separados e versionados."\n    )\n    indicators = [\n        item\n        for item in registry_payload.get("indicators", [])\n        if isinstance(item, dict)\n    ]\n    if not indicators:\n        st.warning("O registro científico de indicadores não pôde ser carregado.")\n        return\n\n    summary = registry_summary(registry_payload)\n    metric_columns = st.columns(4)\n    metric_columns[0].metric("Indicadores registrados", summary["indicator_count"])\n    metric_columns[1].metric("Dimensões analíticas", summary["dimension_count"])\n    metric_columns[2].metric("Versão do registro", summary["version"])\n    metric_columns[3].metric("Situação", summary["status"])\n    st.caption(\n        f"Idioma: {summary['language']} · versão metodológica declarada: "\n        f"{summary['methodology_registry_version']}"\n    )\n\n    presentations = build_indicator_presentations(indicators, methodologies_by_id)\n    for indicator in presentations:\n        label = f"{indicator.title} · v{indicator.version}"\n        with st.expander(label, expanded=False):\n            header = st.columns(4)\n            header[0].metric("Situação", indicator.status)\n            header[1].metric("Dimensão", indicator.dimension)\n            header[2].metric("Unidade", indicator.unit)\n            header[3].metric("Intervalo esperado", indicator.expected_range)\n\n            st.markdown(f"**Identificador:** `{indicator.indicator_id}`")\n            st.markdown(f"**Pergunta científica:** {indicator.scientific_question}")\n            st.markdown(f"**Fundamentação científica:** {indicator.scientific_rationale}")\n            st.markdown(f"**Justificativa de seleção:** {indicator.selection_rationale}")\n            st.markdown(f"**Tipo de resultado:** `{indicator.result_type}`")\n            st.markdown(f"**Interpretação:** {indicator.interpretation}")\n            st.markdown(\n                f"**O que não mede:** {_format_list(indicator.does_not_measure)}"\n            )\n            st.markdown(\n                "**Relação com outros indicadores:** "\n                f"{indicator.relationship_to_other_indicators}"\n            )\n            st.markdown(\n                "**Requisitos de evidência:** "\n                f"{_format_list(indicator.evidence_requirements)}"\n            )\n            st.markdown(\n                f"**Dependências:** {_format_list(indicator.dependencies)}"\n            )\n            st.info(f"Regra de corpus: {indicator.corpus_rule}")\n\n            methodology_status = (\n                "Metodologia disponível"\n                if indicator.methodology_available\n                else "Metodologia pendente no registro metodológico"\n            )\n            st.markdown(f"**Vínculo metodológico:** {methodology_status}")\n            st.markdown(f"**ID metodológico:** `{indicator.methodology_id}`")\n            st.caption(f"Referência: {indicator.methodology_reference}")\n            if indicator.formula:\n                st.markdown("**Fórmula registrada**")\n                st.code(indicator.formula, language=None)\n'''


def transform(source: str) -> str:
    if "def _render_indicator_registry(" in source:
        return source
    if IMPORT_ANCHOR not in source:
        raise ValueError("Bloco de importação esperado não localizado")
    if OLD_START not in source or OLD_END not in source:
        raise ValueError("Bloco legado de indicadores não localizado")

    source = source.replace(IMPORT_ANCHOR, IMPORT_REPLACEMENT, 1)
    start = source.index(OLD_START)
    end = source.index(OLD_END, start)
    source = source[:start] + NEW_FUNCTION + source[end:]
    source = source.replace(
        "_render_indicator_catalog(indicators, methodologies_by_id)",
        "_render_indicator_registry(catalog_payload, methodologies_by_id)",
        1,
    )
    if "Versão do catálogo\", \"1.0.0" in source:
        raise ValueError("Versão fixa do catálogo permaneceu na interface")
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = TARGET.read_text(encoding="utf-8")
    transformed = transform(source)
    if args.check:
        if transformed != source:
            raise SystemExit("interface ainda precisa da migração semântica")
        print("interface semântica dos indicadores está atualizada")
        return 0
    if transformed == source:
        print("interface já está atualizada")
        return 0
    TARGET.write_text(transformed, encoding="utf-8")
    print("interface migrada para o modelo semântico")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
