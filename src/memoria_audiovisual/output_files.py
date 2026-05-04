from .config import APE_OUTPUT_PREFIX


def _csv(name):
    return f"{APE_OUTPUT_PREFIX}_{name}.csv"


def _json(name):
    return f"{APE_OUTPUT_PREFIX}_{name}.json"


def _txt(name):
    return f"{APE_OUTPUT_PREFIX}_{name}.txt"


def _xlsx(name):
    return f"{APE_OUTPUT_PREFIX}_{name}.xlsx"


APE_OUTPUT_FILES = {
    "institutions": _csv("instituicoes"),
    "summary": _csv("resumo_instituicoes"),
    "video_links": _csv("links_video"),
    "internal_pages": _csv("paginas_internas"),
    "analytic_summary": _csv("resumo_instituicoes_analitico"),
    "analytic_video_catalog": _csv("catalogo_videos_analitico"),
    "availability_summary": _csv("resumo_disponibilidade"),
    "availability_reasons": _csv("subcategorias_disponibilidade"),
    "visibility_summary": _csv("resumo_visibilidade"),
    "theme_summary": _csv("resumo_temas"),
    "theme_country": _csv("tema_pais"),
    "archive_type_summary": _csv("resumo_tipos_arquivo"),
    "theme_platform": _csv("tema_plataforma"),
    "theme_archive_type": _csv("tema_tipo_arquivo"),
    "visibility_archive_type": _csv("visibilidade_tipo_arquivo"),
    "snapshot_metadata": _json("snapshot_metadata"),
    "report_json": _json("relatorio"),
    "report_txt": _txt("relatorio"),
    "report_xlsx": _xlsx("relatorio"),
}


def list_ape_output_filenames():
    return list(APE_OUTPUT_FILES.values())


__all__ = ["APE_OUTPUT_FILES", "list_ape_output_filenames"]
