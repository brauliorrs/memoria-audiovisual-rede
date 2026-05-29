from .config import (
    AAPB_OUTPUT_PREFIX,
    AAMOD_OUTPUT_PREFIX,
    APE_OUTPUT_PREFIX,
    ARCHIPOP_OUTPUT_PREFIX,
    EUSCREEN_OUTPUT_PREFIX,
    EUROPEAN_FILM_GATEWAY_OUTPUT_PREFIX,
    EUROPEANA_OUTPUT_PREFIX,
    INA_OUTPUT_PREFIX,
    PARES_OUTPUT_PREFIX,
    PPA_OUTPUT_PREFIX,
)


def _csv(prefix, name):
    return f"{prefix}_{name}.csv"


def _json(prefix, name):
    return f"{prefix}_{name}.json"


def _txt(prefix, name):
    return f"{prefix}_{name}.txt"


def _xlsx(prefix, name):
    return f"{prefix}_{name}.xlsx"


def build_output_files(prefix):
    return {
        "institutions": _csv(prefix, "instituicoes"),
        "summary": _csv(prefix, "resumo_instituicoes"),
        "video_links": _csv(prefix, "links_video"),
        "internal_pages": _csv(prefix, "paginas_internas"),
        "analytic_summary": _csv(prefix, "resumo_instituicoes_analitico"),
        "analytic_video_catalog": _csv(prefix, "catalogo_videos_analitico"),
        "availability_summary": _csv(prefix, "resumo_disponibilidade"),
        "availability_reasons": _csv(prefix, "subcategorias_disponibilidade"),
        "visibility_summary": _csv(prefix, "resumo_visibilidade"),
        "access_surface_summary": _csv(prefix, "resumo_modalidades_acesso"),
        "access_regime_summary": _csv(prefix, "resumo_regimes_acesso"),
        "theme_summary": _csv(prefix, "resumo_temas"),
        "theme_country": _csv(prefix, "tema_pais"),
        "archive_type_summary": _csv(prefix, "resumo_tipos_arquivo"),
        "theme_platform": _csv(prefix, "tema_plataforma"),
        "theme_archive_type": _csv(prefix, "tema_tipo_arquivo"),
        "visibility_archive_type": _csv(prefix, "visibilidade_tipo_arquivo"),
        "timeline_corpus": _csv(prefix, "linha_do_tempo_corpus"),
        "timeline_institutions": _csv(prefix, "linha_do_tempo_instituicoes"),
        "extinction_signals": _csv(prefix, "sinais_possivel_extincao"),
        "snapshot_metadata": _json(prefix, "snapshot_metadata"),
        "report_json": _json(prefix, "relatorio"),
        "report_txt": _txt(prefix, "relatorio"),
        "report_xlsx": _xlsx(prefix, "relatorio"),
    }


def list_output_filenames(output_files):
    return list(output_files.values())


APE_OUTPUT_FILES = build_output_files(APE_OUTPUT_PREFIX)
AAPB_OUTPUT_FILES = build_output_files(AAPB_OUTPUT_PREFIX)
AAMOD_OUTPUT_FILES = build_output_files(AAMOD_OUTPUT_PREFIX)
ARCHIPOP_OUTPUT_FILES = build_output_files(ARCHIPOP_OUTPUT_PREFIX)
INA_OUTPUT_FILES = build_output_files(INA_OUTPUT_PREFIX)
EUSCREEN_OUTPUT_FILES = build_output_files(EUSCREEN_OUTPUT_PREFIX)
EUROPEAN_FILM_GATEWAY_OUTPUT_FILES = build_output_files(EUROPEAN_FILM_GATEWAY_OUTPUT_PREFIX)
EUROPEANA_OUTPUT_FILES = build_output_files(EUROPEANA_OUTPUT_PREFIX)
PARES_OUTPUT_FILES = build_output_files(PARES_OUTPUT_PREFIX)
PPA_OUTPUT_FILES = build_output_files(PPA_OUTPUT_PREFIX)


def list_ape_output_filenames():
    return list_output_filenames(APE_OUTPUT_FILES)


def list_aapb_output_filenames():
    return list_output_filenames(AAPB_OUTPUT_FILES)


def list_aamod_output_filenames():
    return list_output_filenames(AAMOD_OUTPUT_FILES)


def list_archipop_output_filenames():
    return list_output_filenames(ARCHIPOP_OUTPUT_FILES)


def list_ina_output_filenames():
    return list_output_filenames(INA_OUTPUT_FILES)


def list_euscreen_output_filenames():
    return list_output_filenames(EUSCREEN_OUTPUT_FILES)


def list_european_film_gateway_output_filenames():
    return list_output_filenames(EUROPEAN_FILM_GATEWAY_OUTPUT_FILES)


def list_europeana_output_filenames():
    return list_output_filenames(EUROPEANA_OUTPUT_FILES)


def list_pares_output_filenames():
    return list_output_filenames(PARES_OUTPUT_FILES)


def list_ppa_output_filenames():
    return list_output_filenames(PPA_OUTPUT_FILES)


__all__ = [
    "AAPB_OUTPUT_FILES",
    "AAMOD_OUTPUT_FILES",
    "APE_OUTPUT_FILES",
    "ARCHIPOP_OUTPUT_FILES",
    "EUSCREEN_OUTPUT_FILES",
    "EUROPEAN_FILM_GATEWAY_OUTPUT_FILES",
    "EUROPEANA_OUTPUT_FILES",
    "INA_OUTPUT_FILES",
    "PARES_OUTPUT_FILES",
    "PPA_OUTPUT_FILES",
    "build_output_files",
    "list_aapb_output_filenames",
    "list_aamod_output_filenames",
    "list_ape_output_filenames",
    "list_archipop_output_filenames",
    "list_euscreen_output_filenames",
    "list_european_film_gateway_output_filenames",
    "list_europeana_output_filenames",
    "list_ina_output_filenames",
    "list_pares_output_filenames",
    "list_ppa_output_filenames",
    "list_output_filenames",
]
