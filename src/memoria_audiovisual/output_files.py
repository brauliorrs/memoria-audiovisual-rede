from .config import (
    AAPB_OUTPUT_PREFIX,
    AAMOD_OUTPUT_PREFIX,
    ANF_OUTPUT_PREFIX,
    AQSHF_OUTPUT_PREFIX,
    APE_OUTPUT_PREFIX,
    ASIM_OUTPUT_PREFIX,
    ARSENAL_OUTPUT_PREFIX,
    ARCHIPOP_OUTPUT_PREFIX,
    AUTREFOIS_OUTPUT_PREFIX,
    BARCH_OUTPUT_PREFIX,
    BBC_OUTPUT_PREFIX,
    BFI_OUTPUT_PREFIX,
    BNFA_OUTPUT_PREFIX,
    BNT_OUTPUT_PREFIX,
    CCMA_OUTPUT_PREFIX,
    CZECH_TELEVISION_OUTPUT_PREFIX,
    DFF_OUTPUT_PREFIX,
    DHM_OUTPUT_PREFIX,
    EAFA_OUTPUT_PREFIX,
    ECPAD_OUTPUT_PREFIX,
    ERT_OUTPUT_PREFIX,
    EYE_OUTPUT_PREFIX,
    ESTONIAN_FILM_ARCHIVE_OUTPUT_PREFIX,
    FILMARCHIV_AUSTRIA_OUTPUT_PREFIX,
    FILMMUSEUM_DUSSELDORF_OUTPUT_PREFIX,
    FILMOTECA_CATALUNYA_OUTPUT_PREFIX,
    FILMOTECA_ESPANOLA_OUTPUT_PREFIX,
    FILMOTECA_VALENCIANA_OUTPUT_PREFIX,
    DEUTSCHE_KINEMATHEK_OUTPUT_PREFIX,
    DR_OUTPUT_PREFIX,
    CICLIC_OUTPUT_PREFIX,
    CINEARCHIVES_OUTPUT_PREFIX,
    CINEAM_OUTPUT_PREFIX,
    CINEMEMOIRE_OUTPUT_PREFIX,
    CDNA_OUTPUT_PREFIX,
    CINEMATHEQUE_BRETAGNE_OUTPUT_PREFIX,
    CINEMATHEQUE_FRANCAISE_OUTPUT_PREFIX,
    CINEMATHEQUE_SUISSE_OUTPUT_PREFIX,
    CINEMATEK_OUTPUT_PREFIX,
    FILMOTECA_VASCA_OUTPUT_PREFIX,
    CRNOGORSKA_KINOTEKA_OUTPUT_PREFIX,
    CPSA_OUTPUT_PREFIX,
    SAINT_ETIENNE_OUTPUT_PREFIX,
    CINEMATECA_PT_OUTPUT_PREFIX,
    CNCAFF_OUTPUT_PREFIX,
    CNA_OUTPUT_PREFIX,
    EUSCREEN_OUTPUT_PREFIX,
    EUROPEAN_FILM_GATEWAY_OUTPUT_PREFIX,
    EUROPEANA_OUTPUT_PREFIX,
    IAM_OUTPUT_PREFIX,
    INA_OUTPUT_PREFIX,
    LUCE_OUTPUT_PREFIX,
    PARES_OUTPUT_PREFIX,
    PPA_OUTPUT_PREFIX,
    SFA_OUTPUT_PREFIX,
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
ANF_OUTPUT_FILES = build_output_files(ANF_OUTPUT_PREFIX)
AQSHF_OUTPUT_FILES = build_output_files(AQSHF_OUTPUT_PREFIX)
IAM_OUTPUT_FILES = build_output_files(IAM_OUTPUT_PREFIX)
LUCE_OUTPUT_FILES = build_output_files(LUCE_OUTPUT_PREFIX)
ASIM_OUTPUT_FILES = build_output_files(ASIM_OUTPUT_PREFIX)
ARSENAL_OUTPUT_FILES = build_output_files(ARSENAL_OUTPUT_PREFIX)
AUTREFOIS_OUTPUT_FILES = build_output_files(AUTREFOIS_OUTPUT_PREFIX)
BARCH_OUTPUT_FILES = build_output_files(BARCH_OUTPUT_PREFIX)
BBC_OUTPUT_FILES = build_output_files(BBC_OUTPUT_PREFIX)
BFI_OUTPUT_FILES = build_output_files(BFI_OUTPUT_PREFIX)
BNFA_OUTPUT_FILES = build_output_files(BNFA_OUTPUT_PREFIX)
BNT_OUTPUT_FILES = build_output_files(BNT_OUTPUT_PREFIX)
CCMA_OUTPUT_FILES = build_output_files(CCMA_OUTPUT_PREFIX)
CZECH_TELEVISION_OUTPUT_FILES = build_output_files(CZECH_TELEVISION_OUTPUT_PREFIX)
DFF_OUTPUT_FILES = build_output_files(DFF_OUTPUT_PREFIX)
DHM_OUTPUT_FILES = build_output_files(DHM_OUTPUT_PREFIX)
EAFA_OUTPUT_FILES = build_output_files(EAFA_OUTPUT_PREFIX)
ECPAD_OUTPUT_FILES = build_output_files(ECPAD_OUTPUT_PREFIX)
ERT_OUTPUT_FILES = build_output_files(ERT_OUTPUT_PREFIX)
EYE_OUTPUT_FILES = build_output_files(EYE_OUTPUT_PREFIX)
ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES = build_output_files(ESTONIAN_FILM_ARCHIVE_OUTPUT_PREFIX)
FILMARCHIV_AUSTRIA_OUTPUT_FILES = build_output_files(FILMARCHIV_AUSTRIA_OUTPUT_PREFIX)
FILMMUSEUM_DUSSELDORF_OUTPUT_FILES = build_output_files(FILMMUSEUM_DUSSELDORF_OUTPUT_PREFIX)
FILMOTECA_CATALUNYA_OUTPUT_FILES = build_output_files(FILMOTECA_CATALUNYA_OUTPUT_PREFIX)
FILMOTECA_ESPANOLA_OUTPUT_FILES = build_output_files(FILMOTECA_ESPANOLA_OUTPUT_PREFIX)
FILMOTECA_VALENCIANA_OUTPUT_FILES = build_output_files(FILMOTECA_VALENCIANA_OUTPUT_PREFIX)
DEUTSCHE_KINEMATHEK_OUTPUT_FILES = build_output_files(DEUTSCHE_KINEMATHEK_OUTPUT_PREFIX)
DR_OUTPUT_FILES = build_output_files(DR_OUTPUT_PREFIX)
CICLIC_OUTPUT_FILES = build_output_files(CICLIC_OUTPUT_PREFIX)
CINEARCHIVES_OUTPUT_FILES = build_output_files(CINEARCHIVES_OUTPUT_PREFIX)
CINEAM_OUTPUT_FILES = build_output_files(CINEAM_OUTPUT_PREFIX)
CINEMEMOIRE_OUTPUT_FILES = build_output_files(CINEMEMOIRE_OUTPUT_PREFIX)
CDNA_OUTPUT_FILES = build_output_files(CDNA_OUTPUT_PREFIX)
CINEMATHEQUE_BRETAGNE_OUTPUT_FILES = build_output_files(CINEMATHEQUE_BRETAGNE_OUTPUT_PREFIX)
CINEMATHEQUE_FRANCAISE_OUTPUT_FILES = build_output_files(CINEMATHEQUE_FRANCAISE_OUTPUT_PREFIX)
CINEMATEK_OUTPUT_FILES = build_output_files(CINEMATEK_OUTPUT_PREFIX)
CINEMATHEQUE_SUISSE_OUTPUT_FILES = build_output_files(CINEMATHEQUE_SUISSE_OUTPUT_PREFIX)
FILMOTECA_VASCA_OUTPUT_FILES = build_output_files(FILMOTECA_VASCA_OUTPUT_PREFIX)
CRNOGORSKA_KINOTEKA_OUTPUT_FILES = build_output_files(CRNOGORSKA_KINOTEKA_OUTPUT_PREFIX)
CPSA_OUTPUT_FILES = build_output_files(CPSA_OUTPUT_PREFIX)
SAINT_ETIENNE_OUTPUT_FILES = build_output_files(SAINT_ETIENNE_OUTPUT_PREFIX)
CINEMATECA_PT_OUTPUT_FILES = build_output_files(CINEMATECA_PT_OUTPUT_PREFIX)
CNCAFF_OUTPUT_FILES = build_output_files(CNCAFF_OUTPUT_PREFIX)
CNA_OUTPUT_FILES = build_output_files(CNA_OUTPUT_PREFIX)
SFA_OUTPUT_FILES = build_output_files(SFA_OUTPUT_PREFIX)
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


def list_anf_output_filenames():
    return list_output_filenames(ANF_OUTPUT_FILES)


def list_aqshf_output_filenames():
    return list_output_filenames(AQSHF_OUTPUT_FILES)


def list_iam_output_filenames():
    return list_output_filenames(IAM_OUTPUT_FILES)


def list_luce_output_filenames():
    return list_output_filenames(LUCE_OUTPUT_FILES)


def list_asim_output_filenames():
    return list_output_filenames(ASIM_OUTPUT_FILES)


def list_arsenal_output_filenames():
    return list_output_filenames(ARSENAL_OUTPUT_FILES)


def list_autrefois_output_filenames():
    return list_output_filenames(AUTREFOIS_OUTPUT_FILES)


def list_barch_output_filenames():
    return list_output_filenames(BARCH_OUTPUT_FILES)


def list_bbc_output_filenames():
    return list_output_filenames(BBC_OUTPUT_FILES)


def list_bfi_output_filenames():
    return list_output_filenames(BFI_OUTPUT_FILES)


def list_bnfa_output_filenames():
    return list_output_filenames(BNFA_OUTPUT_FILES)


def list_bnt_output_filenames():
    return list_output_filenames(BNT_OUTPUT_FILES)


def list_ccma_output_filenames():
    return list_output_filenames(CCMA_OUTPUT_FILES)


def list_czech_television_output_filenames():
    return list_output_filenames(CZECH_TELEVISION_OUTPUT_FILES)


def list_dff_output_filenames():
    return list_output_filenames(DFF_OUTPUT_FILES)


def list_dhm_output_filenames():
    return list_output_filenames(DHM_OUTPUT_FILES)


def list_eafa_output_filenames():
    return list_output_filenames(EAFA_OUTPUT_FILES)


def list_ecpad_output_filenames():
    return list_output_filenames(ECPAD_OUTPUT_FILES)


def list_ert_output_filenames():
    return list_output_filenames(ERT_OUTPUT_FILES)


def list_eye_output_filenames():
    return list_output_filenames(EYE_OUTPUT_FILES)


def list_estonian_film_archive_output_filenames():
    return list_output_filenames(ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES)


def list_filmarchiv_austria_output_filenames():
    return list_output_filenames(FILMARCHIV_AUSTRIA_OUTPUT_FILES)


def list_filmmuseum_dusseldorf_output_filenames():
    return list_output_filenames(FILMMUSEUM_DUSSELDORF_OUTPUT_FILES)


def list_filmoteca_catalunya_output_filenames():
    return list_output_filenames(FILMOTECA_CATALUNYA_OUTPUT_FILES)


def list_filmoteca_espanola_output_filenames():
    return list_output_filenames(FILMOTECA_ESPANOLA_OUTPUT_FILES)


def list_filmoteca_valenciana_output_filenames():
    return list_output_filenames(FILMOTECA_VALENCIANA_OUTPUT_FILES)


def list_deutsche_kinemathek_output_filenames():
    return list_output_filenames(DEUTSCHE_KINEMATHEK_OUTPUT_FILES)


def list_dr_output_filenames():
    return list_output_filenames(DR_OUTPUT_FILES)


def list_ciclic_output_filenames():
    return list_output_filenames(CICLIC_OUTPUT_FILES)


def list_cinearchives_output_filenames():
    return list_output_filenames(CINEARCHIVES_OUTPUT_FILES)


def list_cineam_output_filenames():
    return list_output_filenames(CINEAM_OUTPUT_FILES)


def list_cinememoire_output_filenames():
    return list_output_filenames(CINEMEMOIRE_OUTPUT_FILES)


def list_cinematheque_bretagne_output_filenames():
    return list_output_filenames(CINEMATHEQUE_BRETAGNE_OUTPUT_FILES)


def list_cinematheque_francaise_output_filenames():
    return list_output_filenames(CINEMATHEQUE_FRANCAISE_OUTPUT_FILES)


def list_cinematek_output_filenames():
    return list_output_filenames(CINEMATEK_OUTPUT_FILES)


def list_cinematheque_suisse_output_filenames():
    return list_output_filenames(CINEMATHEQUE_SUISSE_OUTPUT_FILES)


def list_filmoteca_vasca_output_filenames():
    return list_output_filenames(FILMOTECA_VASCA_OUTPUT_FILES)


def list_crnogorska_kinoteka_output_filenames():
    return list_output_filenames(CRNOGORSKA_KINOTEKA_OUTPUT_FILES)


def list_cpsa_output_filenames():
    return list_output_filenames(CPSA_OUTPUT_FILES)


def list_saint_etienne_output_filenames():
    return list_output_filenames(SAINT_ETIENNE_OUTPUT_FILES)


def list_cdna_output_filenames():
    return list_output_filenames(CDNA_OUTPUT_FILES)


def list_cinemateca_portuguesa_output_filenames():
    return list_output_filenames(CINEMATECA_PT_OUTPUT_FILES)


def list_cnc_aff_output_filenames():
    return list_output_filenames(CNCAFF_OUTPUT_FILES)


def list_cna_output_filenames():
    return list_output_filenames(CNA_OUTPUT_FILES)


def list_sfa_output_filenames():
    return list_output_filenames(SFA_OUTPUT_FILES)


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
    "ANF_OUTPUT_FILES",
    "AQSHF_OUTPUT_FILES",
    "APE_OUTPUT_FILES",
    "ASIM_OUTPUT_FILES",
    "ARSENAL_OUTPUT_FILES",
    "ARCHIPOP_OUTPUT_FILES",
    "AUTREFOIS_OUTPUT_FILES",
    "BARCH_OUTPUT_FILES",
    "BBC_OUTPUT_FILES",
    "BFI_OUTPUT_FILES",
    "BNFA_OUTPUT_FILES",
    "BNT_OUTPUT_FILES",
    "CCMA_OUTPUT_FILES",
    "CZECH_TELEVISION_OUTPUT_FILES",
    "DFF_OUTPUT_FILES",
    "DHM_OUTPUT_FILES",
    "EAFA_OUTPUT_FILES",
    "ECPAD_OUTPUT_FILES",
    "ERT_OUTPUT_FILES",
    "EYE_OUTPUT_FILES",
    "ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES",
    "FILMARCHIV_AUSTRIA_OUTPUT_FILES",
    "FILMMUSEUM_DUSSELDORF_OUTPUT_FILES",
    "FILMOTECA_CATALUNYA_OUTPUT_FILES",
    "FILMOTECA_ESPANOLA_OUTPUT_FILES",
    "FILMOTECA_VALENCIANA_OUTPUT_FILES",
    "DEUTSCHE_KINEMATHEK_OUTPUT_FILES",
    "DR_OUTPUT_FILES",
    "CICLIC_OUTPUT_FILES",
    "CDNA_OUTPUT_FILES",
    "CINEARCHIVES_OUTPUT_FILES",
    "CINEAM_OUTPUT_FILES",
    "CINEMEMOIRE_OUTPUT_FILES",
    "CINEMATHEQUE_BRETAGNE_OUTPUT_FILES",
    "CINEMATHEQUE_FRANCAISE_OUTPUT_FILES",
    "CINEMATHEQUE_SUISSE_OUTPUT_FILES",
    "CINEMATEK_OUTPUT_FILES",
    "FILMOTECA_VASCA_OUTPUT_FILES",
    "CRNOGORSKA_KINOTEKA_OUTPUT_FILES",
    "CPSA_OUTPUT_FILES",
    "SAINT_ETIENNE_OUTPUT_FILES",
    "CINEMATECA_PT_OUTPUT_FILES",
    "CNCAFF_OUTPUT_FILES",
    "CNA_OUTPUT_FILES",
    "EUSCREEN_OUTPUT_FILES",
    "EUROPEAN_FILM_GATEWAY_OUTPUT_FILES",
    "EUROPEANA_OUTPUT_FILES",
    "IAM_OUTPUT_FILES",
    "INA_OUTPUT_FILES",
    "LUCE_OUTPUT_FILES",
    "PARES_OUTPUT_FILES",
    "PPA_OUTPUT_FILES",
    "SFA_OUTPUT_FILES",
    "build_output_files",
    "list_aapb_output_filenames",
    "list_aamod_output_filenames",
    "list_anf_output_filenames",
    "list_aqshf_output_filenames",
    "list_ape_output_filenames",
    "list_iam_output_filenames",
    "list_luce_output_filenames",
    "list_asim_output_filenames",
    "list_arsenal_output_filenames",
    "list_autrefois_output_filenames",
    "list_barch_output_filenames",
    "list_bbc_output_filenames",
    "list_bfi_output_filenames",
    "list_bnfa_output_filenames",
    "list_bnt_output_filenames",
    "list_ccma_output_filenames",
    "list_czech_television_output_filenames",
    "list_dff_output_filenames",
    "list_dhm_output_filenames",
    "list_eafa_output_filenames",
    "list_ecpad_output_filenames",
    "list_ert_output_filenames",
    "list_eye_output_filenames",
    "list_estonian_film_archive_output_filenames",
    "list_filmarchiv_austria_output_filenames",
    "list_filmmuseum_dusseldorf_output_filenames",
    "list_filmoteca_catalunya_output_filenames",
    "list_filmoteca_espanola_output_filenames",
    "list_filmoteca_valenciana_output_filenames",
    "list_deutsche_kinemathek_output_filenames",
    "list_dr_output_filenames",
    "list_ciclic_output_filenames",
    "list_cdna_output_filenames",
    "list_cinearchives_output_filenames",
    "list_cineam_output_filenames",
    "list_cinememoire_output_filenames",
    "list_cinematheque_bretagne_output_filenames",
    "list_cinematheque_francaise_output_filenames",
    "list_cinematheque_suisse_output_filenames",
    "list_cinematek_output_filenames",
    "list_filmoteca_vasca_output_filenames",
    "list_crnogorska_kinoteka_output_filenames",
    "list_cpsa_output_filenames",
    "list_saint_etienne_output_filenames",
    "list_cinemateca_portuguesa_output_filenames",
    "list_cnc_aff_output_filenames",
    "list_cna_output_filenames",
    "list_archipop_output_filenames",
    "list_euscreen_output_filenames",
    "list_european_film_gateway_output_filenames",
    "list_europeana_output_filenames",
    "list_ina_output_filenames",
    "list_pares_output_filenames",
    "list_ppa_output_filenames",
    "list_sfa_output_filenames",
    "list_output_filenames",
]
