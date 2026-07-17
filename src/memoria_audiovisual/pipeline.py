import pandas as pd

from .analysis import filter_in_scope_video_links_df
from .aapb import collect_aapb_dataset
from .aapb_exports import build_aapb_analysis_extra_sheets
from .aapb_exports import write_aapb_analysis_outputs
from .aamod import collect_aamod_dataset
from .aamod_exports import build_aamod_analysis_extra_sheets
from .aamod_exports import write_aamod_analysis_outputs
from .anf import collect_anf_dataset
from .anf_exports import build_anf_analysis_extra_sheets
from .anf_exports import write_anf_analysis_outputs
from .ape import collect_ape_dataset
from .ape_exports import build_ape_analysis_extra_sheets
from .ape_exports import write_ape_analysis_outputs
from .aqshf import collect_aqshf_dataset
from .aqshf_exports import build_aqshf_analysis_extra_sheets
from .aqshf_exports import write_aqshf_analysis_outputs
from .asim import collect_asim_dataset
from .asim_exports import build_asim_analysis_extra_sheets
from .asim_exports import write_asim_analysis_outputs
from .arsenal import collect_arsenal_dataset
from .arsenal_exports import build_arsenal_analysis_extra_sheets
from .arsenal_exports import write_arsenal_analysis_outputs
from .archipop import collect_archipop_dataset
from .archipop_exports import build_archipop_analysis_extra_sheets
from .archipop_exports import write_archipop_analysis_outputs
from .autrefois import collect_autrefois_dataset
from .autrefois_exports import build_autrefois_analysis_extra_sheets
from .autrefois_exports import write_autrefois_analysis_outputs
from .bbc import collect_bbc_dataset
from .bbc_exports import build_bbc_analysis_extra_sheets
from .bbc_exports import write_bbc_analysis_outputs
from .bfi import collect_bfi_dataset
from .bfi_exports import build_bfi_analysis_extra_sheets
from .bfi_exports import write_bfi_analysis_outputs
from .barch import collect_barch_dataset
from .barch_exports import build_barch_analysis_extra_sheets
from .barch_exports import write_barch_analysis_outputs
from .bnfa import collect_bnfa_dataset
from .bnfa_exports import build_bnfa_analysis_extra_sheets
from .bnfa_exports import write_bnfa_analysis_outputs
from .bnt import collect_bnt_dataset
from .bnt_exports import build_bnt_analysis_extra_sheets
from .bnt_exports import write_bnt_analysis_outputs
from .ccma import collect_ccma_dataset
from .ccma_exports import build_ccma_analysis_extra_sheets
from .ccma_exports import write_ccma_analysis_outputs
from .czech_television import collect_czech_television_dataset
from .czech_television_exports import build_czech_television_analysis_extra_sheets
from .czech_television_exports import write_czech_television_analysis_outputs
from .dff import collect_dff_dataset
from .dff_exports import build_dff_analysis_extra_sheets
from .dff_exports import write_dff_analysis_outputs
from .dhm import collect_dhm_dataset
from .dhm_exports import build_dhm_analysis_extra_sheets
from .dhm_exports import write_dhm_analysis_outputs
from .ecpad import collect_ecpad_dataset
from .ecpad_exports import build_ecpad_analysis_extra_sheets
from .ecpad_exports import write_ecpad_analysis_outputs
from .eafa import collect_eafa_dataset
from .eafa_exports import build_eafa_analysis_extra_sheets
from .eafa_exports import write_eafa_analysis_outputs
from .ert import collect_ert_dataset
from .ert_exports import build_ert_analysis_extra_sheets
from .ert_exports import write_ert_analysis_outputs
from .eye import collect_eye_dataset
from .eye_exports import build_eye_analysis_extra_sheets
from .eye_exports import write_eye_analysis_outputs
from .estonian_film_archive import collect_estonian_film_archive_dataset
from .estonian_film_archive_exports import build_estonian_film_archive_analysis_extra_sheets
from .estonian_film_archive_exports import write_estonian_film_archive_analysis_outputs
from .filmarchiv_austria import collect_filmarchiv_austria_dataset
from .filmarchiv_austria_exports import build_filmarchiv_austria_analysis_extra_sheets
from .filmarchiv_austria_exports import write_filmarchiv_austria_analysis_outputs
from .filmmuseum_dusseldorf import collect_filmmuseum_dusseldorf_dataset
from .filmmuseum_dusseldorf_exports import build_filmmuseum_dusseldorf_analysis_extra_sheets
from .filmmuseum_dusseldorf_exports import write_filmmuseum_dusseldorf_analysis_outputs
from .filmoteca_catalunya import collect_filmoteca_catalunya_dataset
from .filmoteca_catalunya_exports import build_filmoteca_catalunya_analysis_extra_sheets
from .filmoteca_catalunya_exports import write_filmoteca_catalunya_analysis_outputs
from .filmoteca_espanola import collect_filmoteca_espanola_dataset
from .filmoteca_espanola_exports import build_filmoteca_espanola_analysis_extra_sheets
from .filmoteca_espanola_exports import write_filmoteca_espanola_analysis_outputs
from .filmoteca_valenciana import collect_filmoteca_valenciana_dataset
from .filmoteca_valenciana_exports import build_filmoteca_valenciana_analysis_extra_sheets
from .filmoteca_valenciana_exports import write_filmoteca_valenciana_analysis_outputs
from .deutsche_kinemathek import collect_deutsche_kinemathek_dataset
from .deutsche_kinemathek_exports import build_deutsche_kinemathek_analysis_extra_sheets
from .deutsche_kinemathek_exports import write_deutsche_kinemathek_analysis_outputs
from .dr import collect_dr_dataset
from .dr_exports import build_dr_analysis_extra_sheets
from .dr_exports import write_dr_analysis_outputs
from .ciclic import collect_ciclic_dataset
from .ciclic_exports import build_ciclic_analysis_extra_sheets
from .ciclic_exports import write_ciclic_analysis_outputs
from .cineam import collect_cineam_dataset
from .cineam_exports import build_cineam_analysis_extra_sheets
from .cineam_exports import write_cineam_analysis_outputs
from .cinememoire import collect_cinememoire_dataset
from .cinememoire_exports import build_cinememoire_analysis_extra_sheets
from .cinememoire_exports import write_cinememoire_analysis_outputs
from .cinearchives import collect_cinearchives_dataset
from .cinearchives_exports import build_cinearchives_analysis_extra_sheets
from .cinearchives_exports import write_cinearchives_analysis_outputs
from .cdna import collect_cdna_dataset
from .cdna_exports import build_cdna_analysis_extra_sheets
from .cdna_exports import write_cdna_analysis_outputs
from .cinematheque_bretagne import collect_cinematheque_bretagne_dataset
from .cinematheque_bretagne_exports import build_cinematheque_bretagne_analysis_extra_sheets
from .cinematheque_bretagne_exports import write_cinematheque_bretagne_analysis_outputs
from .cinematheque_francaise import collect_cinematheque_francaise_dataset
from .cinematheque_francaise_exports import build_cinematheque_francaise_analysis_extra_sheets
from .cinematheque_francaise_exports import write_cinematheque_francaise_analysis_outputs
from .cinematek import collect_cinematek_dataset
from .cinematek_exports import build_cinematek_analysis_extra_sheets
from .cinematek_exports import write_cinematek_analysis_outputs
from .cinematheque_suisse import collect_cinematheque_suisse_dataset
from .cinematheque_suisse_exports import build_cinematheque_suisse_analysis_extra_sheets
from .cinematheque_suisse_exports import write_cinematheque_suisse_analysis_outputs
from .cpsa import collect_cpsa_dataset
from .cpsa_exports import build_cpsa_analysis_extra_sheets
from .cpsa_exports import write_cpsa_analysis_outputs
from .saint_etienne import collect_saint_etienne_dataset
from .saint_etienne_exports import build_saint_etienne_analysis_extra_sheets
from .saint_etienne_exports import write_saint_etienne_analysis_outputs
from .cinemateca_portuguesa import collect_cinemateca_portuguesa_dataset
from .cinemateca_portuguesa_exports import build_cinemateca_portuguesa_analysis_extra_sheets
from .cinemateca_portuguesa_exports import write_cinemateca_portuguesa_analysis_outputs
from .filmoteca_vasca import collect_filmoteca_vasca_dataset
from .filmoteca_vasca_exports import build_filmoteca_vasca_analysis_extra_sheets
from .filmoteca_vasca_exports import write_filmoteca_vasca_analysis_outputs
from .cnc_aff import collect_cnc_aff_dataset
from .cnc_aff_exports import build_cnc_aff_analysis_extra_sheets
from .cnc_aff_exports import write_cnc_aff_analysis_outputs
from .cna import collect_cna_dataset
from .cna_exports import build_cna_analysis_extra_sheets
from .cna_exports import write_cna_analysis_outputs
from .crnogorska_kinoteka import collect_crnogorska_kinoteka_dataset
from .crnogorska_kinoteka_exports import build_crnogorska_kinoteka_analysis_extra_sheets
from .crnogorska_kinoteka_exports import write_crnogorska_kinoteka_analysis_outputs
from .luce import collect_luce_dataset
from .luce_exports import build_luce_analysis_extra_sheets
from .luce_exports import write_luce_analysis_outputs
from .config import (
    AAPB_FAQ_URL,
    AAMOD_HOME_URL,
    ANF_EVENTBOOK_URL,
    AQSHF_MOTION_PICTURES_URL,
    APE_CONTENT_PDF_URL,
    ASIM_EFG_SEARCH_URL,
    ARSENAL_FILM_DATABASE_BROWSE_URL,
    ARCHIPOP_FILMS_URL,
    AUTREFOIS_VIDEOS_API_URL,
    BARCH_EFG_COLLECTION_URL,
    BBC_ARCHIVE_TOPIC_URL,
    BFI_REPLAY_SEARCH_URL,
    BNFA_EFG_COLLECTION_URL,
    BNT_ARCHIVE_AZ_URL,
    CCMA_SEARCH_API_URL,
    CZECH_TELEVISION_IVYSILANI_URL,
    DFF_FILMPORTAL_VIDEOS_URL,
    DHM_MARSHALL_PLAN_URL,
    EAFA_HOME_URL,
    ECPAD_ONLINE_ARCHIVES_URL,
    ERT_ARCHIVE_HOME_URL,
    EYE_FILM_FRAGMENT_LIST_URL,
    ARKAADER_FILM_SHELF_URL,
    FILMARCHIV_AUSTRIA_ON_URL,
    DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL,
    FILMOTECA_CATALUNYA_PLATFO_URL,
    FILMOTECA_ESPANOLA_PLATFO_URL,
    FILMOTECA_VALENCIANA_RESTORATIONS_URL,
    DEUTSCHE_KINEMATHEK_STREAMING_URL,
    DR_GENSYN_URL,
    CICLIC_FILMS_ARCHIVES_URL,
    CINEAM_FILMS_URL,
    CINEMEMOIRE_SEARCH_URL,
    CINEARCHIVES_CATALOG_URL,
    CDNA_FILMS_URL,
    CINEMATHEQUE_BRETAGNE_FILMS_URL,
    CINEMATHEQUE_FRANCAISE_HENRI_URL,
    CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
    CINEMATEK_BE_FILM_URL,
    CPSA_FILMS_URL,
    CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
    SAINT_ETIENNE_COLLECTIONS_URL,
    CINEMATECA_PT_VIDEO_LIST_URL,
    FILMOTECA_VASCA_MULTIMEDIA_URL,
    CNCAFF_EFG_SEARCH_URL,
    CNA_SEARCH_PROFILE_URL,
    EUSCREEN_COLLECTIONS_URL,
    EUROPEAN_FILM_GATEWAY_HOME_URL,
    EUROPEANA_HOME_URL,
    IAM_MEDIAS_API_URL,
    INA_INSTITUTION_URL,
    LUCE_CATALOG_FILMS_URL,
    OUTPUT_DIR,
    PARES_HOME_URL,
    PPA_HOME_URL,
    SFA_HOME_URL,
)
from .efg import collect_european_film_gateway_dataset
from .efg_exports import (
    build_european_film_gateway_analysis_extra_sheets,
    write_european_film_gateway_analysis_outputs,
)
from .excel_export import save_basic_excel_report
from .europeana import collect_europeana_dataset
from .europeana_exports import build_europeana_analysis_extra_sheets
from .europeana_exports import write_europeana_analysis_outputs
from .euscreen import collect_euscreen_dataset
from .euscreen_exports import build_euscreen_analysis_extra_sheets
from .euscreen_exports import write_euscreen_analysis_outputs
from .iam import collect_iam_dataset
from .iam_exports import build_iam_analysis_extra_sheets
from .iam_exports import write_iam_analysis_outputs
from .ina import collect_ina_dataset
from .ina_exports import build_ina_analysis_extra_sheets
from .ina_exports import write_ina_analysis_outputs
from .output_files import (
    AAPB_OUTPUT_FILES,
    AAMOD_OUTPUT_FILES,
    ANF_OUTPUT_FILES,
    AQSHF_OUTPUT_FILES,
    APE_OUTPUT_FILES,
    ASIM_OUTPUT_FILES,
    ARSENAL_OUTPUT_FILES,
    ARCHIPOP_OUTPUT_FILES,
    AUTREFOIS_OUTPUT_FILES,
    BARCH_OUTPUT_FILES,
    BBC_OUTPUT_FILES,
    BFI_OUTPUT_FILES,
    BNFA_OUTPUT_FILES,
    BNT_OUTPUT_FILES,
    CCMA_OUTPUT_FILES,
    CZECH_TELEVISION_OUTPUT_FILES,
    DFF_OUTPUT_FILES,
    DHM_OUTPUT_FILES,
    EAFA_OUTPUT_FILES,
    ECPAD_OUTPUT_FILES,
    ERT_OUTPUT_FILES,
    EYE_OUTPUT_FILES,
    ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES,
    FILMARCHIV_AUSTRIA_OUTPUT_FILES,
    FILMMUSEUM_DUSSELDORF_OUTPUT_FILES,
    FILMOTECA_CATALUNYA_OUTPUT_FILES,
    FILMOTECA_ESPANOLA_OUTPUT_FILES,
    FILMOTECA_VALENCIANA_OUTPUT_FILES,
    DEUTSCHE_KINEMATHEK_OUTPUT_FILES,
    DR_OUTPUT_FILES,
    CICLIC_OUTPUT_FILES,
    CINEAM_OUTPUT_FILES,
    CINEMEMOIRE_OUTPUT_FILES,
    CINEARCHIVES_OUTPUT_FILES,
    CDNA_OUTPUT_FILES,
    CINEMATHEQUE_BRETAGNE_OUTPUT_FILES,
    CINEMATHEQUE_FRANCAISE_OUTPUT_FILES,
    CINEMATHEQUE_SUISSE_OUTPUT_FILES,
    CINEMATEK_OUTPUT_FILES,
    CRNOGORSKA_KINOTEKA_OUTPUT_FILES,
    CPSA_OUTPUT_FILES,
    SAINT_ETIENNE_OUTPUT_FILES,
    CINEMATECA_PT_OUTPUT_FILES,
    FILMOTECA_VASCA_OUTPUT_FILES,
    CNCAFF_OUTPUT_FILES,
    CNA_OUTPUT_FILES,
    EUSCREEN_OUTPUT_FILES,
    EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
    EUROPEANA_OUTPUT_FILES,
    IAM_OUTPUT_FILES,
    INA_OUTPUT_FILES,
    LUCE_OUTPUT_FILES,
    PARES_OUTPUT_FILES,
    PPA_OUTPUT_FILES,
    SFA_OUTPUT_FILES,
)
from .pares import collect_pares_dataset
from .pares_exports import build_pares_analysis_extra_sheets
from .pares_exports import write_pares_analysis_outputs
from .ppa import collect_ppa_dataset
from .ppa_exports import build_ppa_analysis_extra_sheets
from .ppa_exports import write_ppa_analysis_outputs
from .reporting import build_report_payload, save_csv, save_json_report, save_txt_report
from .sfa import collect_sfa_dataset
from .sfa_exports import build_sfa_analysis_extra_sheets
from .sfa_exports import write_sfa_analysis_outputs
from .snapshot_metadata import (
    build_aapb_snapshot_metadata,
    build_aamod_snapshot_metadata,
    build_anf_snapshot_metadata,
    build_ape_snapshot_metadata,
    build_aqshf_snapshot_metadata,
    build_asim_snapshot_metadata,
    build_arsenal_snapshot_metadata,
    build_archipop_snapshot_metadata,
    build_autrefois_snapshot_metadata,
    build_barch_snapshot_metadata,
    build_bbc_snapshot_metadata,
    build_bfi_snapshot_metadata,
    build_bnfa_snapshot_metadata,
    build_bnt_snapshot_metadata,
    build_ccma_snapshot_metadata,
    build_czech_television_snapshot_metadata,
    build_dff_snapshot_metadata,
    build_dhm_snapshot_metadata,
    build_eafa_snapshot_metadata,
    build_ecpad_snapshot_metadata,
    build_ert_snapshot_metadata,
    build_eye_snapshot_metadata,
    build_estonian_film_archive_snapshot_metadata,
    build_filmarchiv_austria_snapshot_metadata,
    build_filmmuseum_dusseldorf_snapshot_metadata,
    build_filmoteca_catalunya_snapshot_metadata,
    build_filmoteca_espanola_snapshot_metadata,
    build_filmoteca_valenciana_snapshot_metadata,
    build_deutsche_kinemathek_snapshot_metadata,
    build_dr_snapshot_metadata,
    build_ciclic_snapshot_metadata,
    build_cineam_snapshot_metadata,
    build_cinememoire_snapshot_metadata,
    build_cinearchives_snapshot_metadata,
    build_cdna_snapshot_metadata,
    build_cinematheque_bretagne_snapshot_metadata,
    build_cinematheque_francaise_snapshot_metadata,
    build_cinematheque_suisse_snapshot_metadata,
    build_cinematek_snapshot_metadata,
    build_crnogorska_kinoteka_snapshot_metadata,
    build_cpsa_snapshot_metadata,
    build_saint_etienne_snapshot_metadata,
    build_cinemateca_portuguesa_snapshot_metadata,
    build_filmoteca_vasca_snapshot_metadata,
    build_cnc_aff_snapshot_metadata,
    build_cna_snapshot_metadata,
    build_luce_snapshot_metadata,
    build_euscreen_snapshot_metadata,
    build_european_film_gateway_snapshot_metadata,
    build_europeana_snapshot_metadata,
    build_iam_snapshot_metadata,
    build_ina_snapshot_metadata,
    build_pares_snapshot_metadata,
    build_ppa_snapshot_metadata,
    build_sfa_snapshot_metadata,
    save_snapshot_metadata_payload,
)
from .timeline import write_timeline_outputs


APE_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "ape_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_ape",
]

APE_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ape_detail_url",
    "content_available_in_ape",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

APE_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ape_detail_url",
    "content_available_in_ape",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

APE_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ape_detail_url",
    "content_available_in_ape",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

ARCHIPOP_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archipop_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

ARCHIPOP_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "archipop_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

ARCHIPOP_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "archipop_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

ARCHIPOP_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "archipop_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

AAMOD_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "aamod_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
AAMOD_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "aamod_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
AAMOD_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "aamod_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
AAMOD_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "aamod_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
SFA_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "sfa_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
SFA_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "sfa_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
SFA_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "sfa_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
SFA_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "sfa_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
ANF_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "anf_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
ANF_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "anf_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
ANF_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "anf_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
ANF_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "anf_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
AQSHF_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "aqshf_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
AQSHF_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "aqshf_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
AQSHF_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "aqshf_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
AQSHF_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "aqshf_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
IAM_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "iam_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
IAM_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "iam_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
IAM_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "iam_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
IAM_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "iam_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
AUTREFOIS_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "autrefois_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
AUTREFOIS_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "autrefois_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
AUTREFOIS_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "autrefois_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
AUTREFOIS_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "autrefois_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
BBC_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "bbc_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
BBC_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "bbc_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
BBC_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "bbc_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
BBC_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "bbc_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
BFI_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "bfi_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
BFI_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "bfi_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
BFI_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "bfi_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
BFI_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "bfi_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
BARCH_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "barch_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
BARCH_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "barch_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
BARCH_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "barch_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
BARCH_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "barch_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
BNFA_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "bnfa_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
BNFA_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "bnfa_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
BNFA_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "bnfa_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
BNFA_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "bnfa_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
BNT_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "bnt_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
BNT_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "bnt_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
BNT_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "bnt_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
BNT_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "bnt_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CCMA_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "ccma_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
CCMA_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "ccma_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
CCMA_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "ccma_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
CCMA_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "ccma_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CZECH_TELEVISION_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "czech_tv_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CZECH_TELEVISION_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "czech_tv_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CZECH_TELEVISION_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "czech_tv_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CZECH_TELEVISION_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "czech_tv_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
DFF_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "dff_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
DFF_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "dff_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
DFF_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "dff_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
DFF_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "dff_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
DHM_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "dhm_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
DHM_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "dhm_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
DHM_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "dhm_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
DHM_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "dhm_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
EAFA_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "eafa_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
EAFA_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "eafa_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
EAFA_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "eafa_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
EAFA_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "eafa_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
ECPAD_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "ecpad_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
ECPAD_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "ecpad_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
ECPAD_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "ecpad_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
ECPAD_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "ecpad_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
ERT_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "ert_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
ERT_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "ert_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
ERT_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "ert_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
ERT_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "ert_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
DEUTSCHE_KINEMATHEK_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "deutsche_kinemathek_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
DEUTSCHE_KINEMATHEK_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "deutsche_kinemathek_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
DEUTSCHE_KINEMATHEK_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "deutsche_kinemathek_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
DEUTSCHE_KINEMATHEK_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "deutsche_kinemathek_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
DR_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "dr_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
DR_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "dr_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
DR_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "dr_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
DR_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "dr_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CICLIC_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "ciclic_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
CICLIC_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "ciclic_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
CICLIC_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "ciclic_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
CICLIC_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "ciclic_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CINEAM_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "cineam_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
CINEAM_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "cineam_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
CINEAM_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "cineam_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
CINEAM_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "cineam_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CINEMEMOIRE_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "cinememoire_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CINEMEMOIRE_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "cinememoire_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CINEMEMOIRE_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "cinememoire_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CINEMEMOIRE_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "cinememoire_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
CINEARCHIVES_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "cinearchives_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CINEARCHIVES_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "cinearchives_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CINEARCHIVES_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "cinearchives_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CINEARCHIVES_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "cinearchives_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
CINEMATHEQUE_BRETAGNE_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_bretagne_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CINEMATHEQUE_BRETAGNE_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_bretagne_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CINEMATHEQUE_BRETAGNE_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_bretagne_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CINEMATHEQUE_BRETAGNE_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_bretagne_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
CINEMATHEQUE_FRANCAISE_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_francaise_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CINEMATHEQUE_FRANCAISE_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_francaise_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CINEMATHEQUE_FRANCAISE_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_francaise_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CINEMATHEQUE_FRANCAISE_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_francaise_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
CINEMATEK_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "cinematek_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CINEMATEK_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "cinematek_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CINEMATEK_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "cinematek_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CINEMATEK_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "cinematek_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
EYE_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "eye_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
EYE_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "eye_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
EYE_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "eye_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
EYE_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "eye_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
ESTONIAN_FILM_ARCHIVE_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "estonian_film_archive_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
ESTONIAN_FILM_ARCHIVE_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "estonian_film_archive_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
ESTONIAN_FILM_ARCHIVE_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "estonian_film_archive_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
ESTONIAN_FILM_ARCHIVE_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "estonian_film_archive_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
FILMARCHIV_AUSTRIA_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "filmarchiv_austria_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
FILMARCHIV_AUSTRIA_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "filmarchiv_austria_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
FILMARCHIV_AUSTRIA_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "filmarchiv_austria_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
FILMARCHIV_AUSTRIA_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "filmarchiv_austria_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
FILMMUSEUM_DUSSELDORF_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "filmmuseum_dusseldorf_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
FILMMUSEUM_DUSSELDORF_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "filmmuseum_dusseldorf_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
FILMMUSEUM_DUSSELDORF_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "filmmuseum_dusseldorf_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
FILMMUSEUM_DUSSELDORF_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "filmmuseum_dusseldorf_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
FILMOTECA_CATALUNYA_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_catalunya_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
FILMOTECA_CATALUNYA_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_catalunya_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
FILMOTECA_CATALUNYA_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_catalunya_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
FILMOTECA_CATALUNYA_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_catalunya_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
FILMOTECA_ESPANOLA_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_espanola_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
FILMOTECA_ESPANOLA_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_espanola_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
FILMOTECA_ESPANOLA_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_espanola_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
FILMOTECA_ESPANOLA_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_espanola_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
FILMOTECA_VALENCIANA_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_valenciana_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
FILMOTECA_VALENCIANA_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_valenciana_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
FILMOTECA_VALENCIANA_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_valenciana_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
FILMOTECA_VALENCIANA_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_valenciana_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
CINEMATHEQUE_SUISSE_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_suisse_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CINEMATHEQUE_SUISSE_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_suisse_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CINEMATHEQUE_SUISSE_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_suisse_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CINEMATHEQUE_SUISSE_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "cinematheque_suisse_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
CPSA_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "cpsa_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
CPSA_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "cpsa_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
CPSA_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "cpsa_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
CPSA_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "cpsa_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
SAINT_ETIENNE_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "saint_etienne_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
SAINT_ETIENNE_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "saint_etienne_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
SAINT_ETIENNE_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "saint_etienne_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
SAINT_ETIENNE_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "saint_etienne_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
CDNA_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "cdna_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
CDNA_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "cdna_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
CDNA_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "cdna_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
CDNA_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "cdna_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CINEMATECA_PT_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "cinemateca_portuguesa_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CINEMATECA_PT_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "cinemateca_portuguesa_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CINEMATECA_PT_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "cinemateca_portuguesa_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CINEMATECA_PT_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "cinemateca_portuguesa_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
FILMOTECA_VASCA_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_vasca_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
FILMOTECA_VASCA_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_vasca_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
FILMOTECA_VASCA_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_vasca_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
FILMOTECA_VASCA_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "filmoteca_vasca_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
LUCE_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "luce_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
LUCE_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "luce_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
LUCE_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "luce_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
LUCE_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "luce_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CNCAFF_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "cnc_aff_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
CNCAFF_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "cnc_aff_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
CNCAFF_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "cnc_aff_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
CNCAFF_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "cnc_aff_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CNA_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "cna_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
CNA_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "cna_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
CNA_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "cna_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
CNA_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "cna_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
ASIM_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "asim_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
ASIM_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "asim_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
ASIM_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "asim_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
ASIM_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "asim_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]
CRNOGORSKA_KINOTEKA_INSTITUTION_FIELDS = [
    field.replace("archipop_detail_url", "crnogorska_kinoteka_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS
]
CRNOGORSKA_KINOTEKA_SUMMARY_FIELDS = [
    field.replace("archipop_detail_url", "crnogorska_kinoteka_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS
]
CRNOGORSKA_KINOTEKA_VIDEO_LINK_FIELDS = [
    field.replace("archipop_detail_url", "crnogorska_kinoteka_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS
]
CRNOGORSKA_KINOTEKA_INTERNAL_PAGE_FIELDS = [
    field.replace("archipop_detail_url", "crnogorska_kinoteka_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS
]
ARSENAL_INSTITUTION_FIELDS = [field.replace("archipop_detail_url", "arsenal_detail_url") for field in ARCHIPOP_INSTITUTION_FIELDS]
ARSENAL_SUMMARY_FIELDS = [field.replace("archipop_detail_url", "arsenal_detail_url") for field in ARCHIPOP_SUMMARY_FIELDS]
ARSENAL_VIDEO_LINK_FIELDS = [field.replace("archipop_detail_url", "arsenal_detail_url") for field in ARCHIPOP_VIDEO_LINK_FIELDS]
ARSENAL_INTERNAL_PAGE_FIELDS = [field.replace("archipop_detail_url", "arsenal_detail_url") for field in ARCHIPOP_INTERNAL_PAGE_FIELDS]

INA_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "ina_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

INA_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ina_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

INA_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ina_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

INA_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ina_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

EUSCREEN_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "euscreen_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

EUSCREEN_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "euscreen_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

EUSCREEN_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "euscreen_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

EUSCREEN_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "euscreen_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

EUROPEAN_FILM_GATEWAY_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "efg_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

EUROPEAN_FILM_GATEWAY_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "efg_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

EUROPEAN_FILM_GATEWAY_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "efg_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

EUROPEAN_FILM_GATEWAY_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "efg_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

EUROPEANA_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "europeana_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

EUROPEANA_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "europeana_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

EUROPEANA_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "europeana_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

EUROPEANA_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "europeana_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

PARES_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "pares_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

PARES_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "pares_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

PARES_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "pares_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

PARES_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "pares_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

PPA_INSTITUTION_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_INSTITUTION_FIELDS]
PPA_SUMMARY_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_SUMMARY_FIELDS]
PPA_VIDEO_LINK_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_VIDEO_LINK_FIELDS]
PPA_INTERNAL_PAGE_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_INTERNAL_PAGE_FIELDS]
AAPB_INSTITUTION_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_INSTITUTION_FIELDS]
AAPB_SUMMARY_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_SUMMARY_FIELDS]
AAPB_VIDEO_LINK_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_VIDEO_LINK_FIELDS]
AAPB_INTERNAL_PAGE_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_INTERNAL_PAGE_FIELDS]


def ensure_fields(rows, fieldnames):
    normalized = []
    for row in rows:
        normalized.append({field: row.get(field, "") for field in fieldnames})
    return normalized


def sync_summary_video_counts(rows_summary, links_df):
    if not rows_summary:
        return rows_summary
    counts = {}
    if links_df is not None and not links_df.empty and "slug" in links_df.columns:
        counts = links_df.groupby("slug").size().to_dict()
    synced_rows = []
    for row in rows_summary:
        synced_row = dict(row)
        if "video_links_found_total" in synced_row:
            synced_row["video_links_found_total"] = int(counts.get(synced_row.get("slug"), 0))
        synced_rows.append(synced_row)
    return synced_rows


def _run_corpus_pipeline(
    *,
    source_label,
    source_url,
    collect_dataset,
    institution_fields,
    summary_fields,
    video_link_fields,
    internal_page_fields,
    output_files,
    analysis_output_writer,
    analysis_extra_sheets_builder,
    snapshot_builder,
    report_title,
    institutions_sheet_title,
    generated_by,
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== ETAPA 1: Coletando instituições do {source_label} ===")
    institutions, rows_summary, rows_video_links, rows_internal_pages = collect_dataset()
    links_df = filter_in_scope_video_links_df(pd.DataFrame(rows_video_links))
    rows_video_links = links_df.to_dict(orient="records")
    rows_summary = sync_summary_video_counts(rows_summary, links_df)
    payload = build_report_payload(
        source_url,
        len(institutions),
        rows_summary,
        rows_video_links,
    )
    summary_df = pd.DataFrame(rows_summary)
    analysis_frames = analysis_output_writer(
        OUTPUT_DIR,
        summary_df,
        links_df,
    )

    save_csv(
        OUTPUT_DIR / output_files["institutions"],
        ensure_fields(institutions, institution_fields),
        institution_fields,
    )
    save_csv(
        OUTPUT_DIR / output_files["summary"],
        ensure_fields(rows_summary, summary_fields),
        summary_fields,
    )
    save_csv(
        OUTPUT_DIR / output_files["video_links"],
        ensure_fields(rows_video_links, video_link_fields),
        video_link_fields,
    )
    save_csv(
        OUTPUT_DIR / output_files["internal_pages"],
        ensure_fields(rows_internal_pages, internal_page_fields),
        internal_page_fields,
    )
    save_json_report(OUTPUT_DIR / output_files["report_json"], payload)
    save_txt_report(
        OUTPUT_DIR / output_files["report_txt"],
        payload,
        rows_summary,
        report_title=report_title,
    )
    save_basic_excel_report(
        OUTPUT_DIR / output_files["report_xlsx"],
        payload,
        rows_summary,
        rows_video_links,
        rows_internal_pages,
        extra_sheets=[
            {
                "title": institutions_sheet_title,
                "rows": ensure_fields(institutions, institution_fields),
                "fieldnames": institution_fields,
            },
            *analysis_extra_sheets_builder(analysis_frames),
        ],
    )
    snapshot_payload = snapshot_builder(
        OUTPUT_DIR,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )
    write_timeline_outputs(
        OUTPUT_DIR,
        dataset=snapshot_payload["dataset"],
        output_files=output_files,
        snapshot_metadata=snapshot_payload,
        summary_df=summary_df,
        analysis_frames=analysis_frames,
    )
    save_snapshot_metadata_payload(
        OUTPUT_DIR,
        output_files=output_files,
        payload=snapshot_payload,
    )

    print("\nArquivos gerados:")
    for filename in output_files.values():
        print(f" - {OUTPUT_DIR / filename}")


def run_pipeline():
    _run_corpus_pipeline(
        source_label="Archives Portal Europe",
        source_url=APE_CONTENT_PDF_URL,
        collect_dataset=collect_ape_dataset,
        institution_fields=APE_INSTITUTION_FIELDS,
        summary_fields=APE_SUMMARY_FIELDS,
        video_link_fields=APE_VIDEO_LINK_FIELDS,
        internal_page_fields=APE_INTERNAL_PAGE_FIELDS,
        output_files=APE_OUTPUT_FILES,
        analysis_output_writer=write_ape_analysis_outputs,
        analysis_extra_sheets_builder=build_ape_analysis_extra_sheets,
        snapshot_builder=build_ape_snapshot_metadata,
        report_title="RELATORIO - ARCHIVES PORTAL EUROPE",
        institutions_sheet_title="APE Institutions",
        generated_by="scripts/run_pipeline.py",
    )


def run_ina_pipeline():
    _run_corpus_pipeline(
        source_label="Institut national de l'audiovisuel (INA)",
        source_url=INA_INSTITUTION_URL,
        collect_dataset=collect_ina_dataset,
        institution_fields=INA_INSTITUTION_FIELDS,
        summary_fields=INA_SUMMARY_FIELDS,
        video_link_fields=INA_VIDEO_LINK_FIELDS,
        internal_page_fields=INA_INTERNAL_PAGE_FIELDS,
        output_files=INA_OUTPUT_FILES,
        analysis_output_writer=write_ina_analysis_outputs,
        analysis_extra_sheets_builder=build_ina_analysis_extra_sheets,
        snapshot_builder=build_ina_snapshot_metadata,
        report_title="RELATORIO - INA",
        institutions_sheet_title="INA Institutions",
        generated_by="scripts/run_ina_pipeline.py",
    )


def run_archipop_pipeline():
    _run_corpus_pipeline(
        source_label="ARCHIPOP",
        source_url=ARCHIPOP_FILMS_URL,
        collect_dataset=collect_archipop_dataset,
        institution_fields=ARCHIPOP_INSTITUTION_FIELDS,
        summary_fields=ARCHIPOP_SUMMARY_FIELDS,
        video_link_fields=ARCHIPOP_VIDEO_LINK_FIELDS,
        internal_page_fields=ARCHIPOP_INTERNAL_PAGE_FIELDS,
        output_files=ARCHIPOP_OUTPUT_FILES,
        analysis_output_writer=write_archipop_analysis_outputs,
        analysis_extra_sheets_builder=build_archipop_analysis_extra_sheets,
        snapshot_builder=build_archipop_snapshot_metadata,
        report_title="RELATORIO - ARCHIPOP",
        institutions_sheet_title="ARCHIPOP Institutions",
        generated_by="scripts/run_archipop_pipeline.py",
    )


def run_aamod_pipeline():
    _run_corpus_pipeline(
        source_label="AAMOD",
        source_url=AAMOD_HOME_URL,
        collect_dataset=collect_aamod_dataset,
        institution_fields=AAMOD_INSTITUTION_FIELDS,
        summary_fields=AAMOD_SUMMARY_FIELDS,
        video_link_fields=AAMOD_VIDEO_LINK_FIELDS,
        internal_page_fields=AAMOD_INTERNAL_PAGE_FIELDS,
        output_files=AAMOD_OUTPUT_FILES,
        analysis_output_writer=write_aamod_analysis_outputs,
        analysis_extra_sheets_builder=build_aamod_analysis_extra_sheets,
        snapshot_builder=build_aamod_snapshot_metadata,
        report_title="RELATORIO - AAMOD",
        institutions_sheet_title="AAMOD Institutions",
        generated_by="scripts/run_aamod_pipeline.py",
    )


def run_sfa_pipeline():
    _run_corpus_pipeline(
        source_label="Slovenski filmski arhiv",
        source_url=SFA_HOME_URL,
        collect_dataset=collect_sfa_dataset,
        institution_fields=SFA_INSTITUTION_FIELDS,
        summary_fields=SFA_SUMMARY_FIELDS,
        video_link_fields=SFA_VIDEO_LINK_FIELDS,
        internal_page_fields=SFA_INTERNAL_PAGE_FIELDS,
        output_files=SFA_OUTPUT_FILES,
        analysis_output_writer=write_sfa_analysis_outputs,
        analysis_extra_sheets_builder=build_sfa_analysis_extra_sheets,
        snapshot_builder=build_sfa_snapshot_metadata,
        report_title="RELATORIO - SFA",
        institutions_sheet_title="SFA Institutions",
        generated_by="scripts/run_sfa_pipeline.py",
    )


def run_anf_pipeline():
    _run_corpus_pipeline(
        source_label="Arhiva Nationala de Filme - Cinemateca Romana",
        source_url=ANF_EVENTBOOK_URL,
        collect_dataset=collect_anf_dataset,
        institution_fields=ANF_INSTITUTION_FIELDS,
        summary_fields=ANF_SUMMARY_FIELDS,
        video_link_fields=ANF_VIDEO_LINK_FIELDS,
        internal_page_fields=ANF_INTERNAL_PAGE_FIELDS,
        output_files=ANF_OUTPUT_FILES,
        analysis_output_writer=write_anf_analysis_outputs,
        analysis_extra_sheets_builder=build_anf_analysis_extra_sheets,
        snapshot_builder=build_anf_snapshot_metadata,
        report_title="RELATORIO - ANF CINEMATECA ROMANA",
        institutions_sheet_title="ANF Institutions",
        generated_by="scripts/run_anf_pipeline.py",
    )


def run_aqshf_pipeline():
    _run_corpus_pipeline(
        source_label="Arkivi Qendror Shtetëror i Filmit / The Albanian National Film Archive",
        source_url=AQSHF_MOTION_PICTURES_URL,
        collect_dataset=collect_aqshf_dataset,
        institution_fields=AQSHF_INSTITUTION_FIELDS,
        summary_fields=AQSHF_SUMMARY_FIELDS,
        video_link_fields=AQSHF_VIDEO_LINK_FIELDS,
        internal_page_fields=AQSHF_INTERNAL_PAGE_FIELDS,
        output_files=AQSHF_OUTPUT_FILES,
        analysis_output_writer=write_aqshf_analysis_outputs,
        analysis_extra_sheets_builder=build_aqshf_analysis_extra_sheets,
        snapshot_builder=build_aqshf_snapshot_metadata,
        report_title="RELATORIO - AQSHF",
        institutions_sheet_title="AQSHF Institutions",
        generated_by="scripts/run_aqshf_pipeline.py",
    )


def run_iam_pipeline():
    _run_corpus_pipeline(
        source_label="Institut audiovisuel de Monaco",
        source_url=IAM_MEDIAS_API_URL,
        collect_dataset=collect_iam_dataset,
        institution_fields=IAM_INSTITUTION_FIELDS,
        summary_fields=IAM_SUMMARY_FIELDS,
        video_link_fields=IAM_VIDEO_LINK_FIELDS,
        internal_page_fields=IAM_INTERNAL_PAGE_FIELDS,
        output_files=IAM_OUTPUT_FILES,
        analysis_output_writer=write_iam_analysis_outputs,
        analysis_extra_sheets_builder=build_iam_analysis_extra_sheets,
        snapshot_builder=build_iam_snapshot_metadata,
        report_title="RELATORIO - INSTITUT AUDIOVISUEL DE MONACO",
        institutions_sheet_title="IAM Institutions",
        generated_by="scripts/run_iam_pipeline.py",
    )


def run_autrefois_pipeline():
    _run_corpus_pipeline(
        source_label="Fondation Autrefois Genève",
        source_url=AUTREFOIS_VIDEOS_API_URL,
        collect_dataset=collect_autrefois_dataset,
        institution_fields=AUTREFOIS_INSTITUTION_FIELDS,
        summary_fields=AUTREFOIS_SUMMARY_FIELDS,
        video_link_fields=AUTREFOIS_VIDEO_LINK_FIELDS,
        internal_page_fields=AUTREFOIS_INTERNAL_PAGE_FIELDS,
        output_files=AUTREFOIS_OUTPUT_FILES,
        analysis_output_writer=write_autrefois_analysis_outputs,
        analysis_extra_sheets_builder=build_autrefois_analysis_extra_sheets,
        snapshot_builder=build_autrefois_snapshot_metadata,
        report_title="RELATORIO - FONDATION AUTREFOIS GENEVE",
        institutions_sheet_title="Autrefois Institutions",
        generated_by="scripts/run_autrefois_pipeline.py",
    )


def run_bbc_pipeline():
    _run_corpus_pipeline(
        source_label="BBC Archive",
        source_url=BBC_ARCHIVE_TOPIC_URL,
        collect_dataset=collect_bbc_dataset,
        institution_fields=BBC_INSTITUTION_FIELDS,
        summary_fields=BBC_SUMMARY_FIELDS,
        video_link_fields=BBC_VIDEO_LINK_FIELDS,
        internal_page_fields=BBC_INTERNAL_PAGE_FIELDS,
        output_files=BBC_OUTPUT_FILES,
        analysis_output_writer=write_bbc_analysis_outputs,
        analysis_extra_sheets_builder=build_bbc_analysis_extra_sheets,
        snapshot_builder=build_bbc_snapshot_metadata,
        report_title="RELATORIO - BBC ARCHIVE",
        institutions_sheet_title="BBC Archive Institutions",
        generated_by="scripts/run_bbc_pipeline.py",
    )


def run_bfi_pipeline():
    _run_corpus_pipeline(
        source_label="BFI National Archive",
        source_url=BFI_REPLAY_SEARCH_URL,
        collect_dataset=collect_bfi_dataset,
        institution_fields=BFI_INSTITUTION_FIELDS,
        summary_fields=BFI_SUMMARY_FIELDS,
        video_link_fields=BFI_VIDEO_LINK_FIELDS,
        internal_page_fields=BFI_INTERNAL_PAGE_FIELDS,
        output_files=BFI_OUTPUT_FILES,
        analysis_output_writer=write_bfi_analysis_outputs,
        analysis_extra_sheets_builder=build_bfi_analysis_extra_sheets,
        snapshot_builder=build_bfi_snapshot_metadata,
        report_title="RELATORIO - BFI NATIONAL ARCHIVE",
        institutions_sheet_title="BFI Institutions",
        generated_by="scripts/run_bfi_pipeline.py",
    )


def run_barch_pipeline():
    _run_corpus_pipeline(
        source_label="Bundesarchiv",
        source_url=BARCH_EFG_COLLECTION_URL,
        collect_dataset=collect_barch_dataset,
        institution_fields=BARCH_INSTITUTION_FIELDS,
        summary_fields=BARCH_SUMMARY_FIELDS,
        video_link_fields=BARCH_VIDEO_LINK_FIELDS,
        internal_page_fields=BARCH_INTERNAL_PAGE_FIELDS,
        output_files=BARCH_OUTPUT_FILES,
        analysis_output_writer=write_barch_analysis_outputs,
        analysis_extra_sheets_builder=build_barch_analysis_extra_sheets,
        snapshot_builder=build_barch_snapshot_metadata,
        report_title="RELATORIO - BUNDESARCHIV",
        institutions_sheet_title="Bundesarchiv Institutions",
        generated_by="scripts/run_barch_pipeline.py",
    )


def run_bnt_pipeline():
    _run_corpus_pipeline(
        source_label="Bulgarian National Television",
        source_url=BNT_ARCHIVE_AZ_URL,
        collect_dataset=collect_bnt_dataset,
        institution_fields=BNT_INSTITUTION_FIELDS,
        summary_fields=BNT_SUMMARY_FIELDS,
        video_link_fields=BNT_VIDEO_LINK_FIELDS,
        internal_page_fields=BNT_INTERNAL_PAGE_FIELDS,
        output_files=BNT_OUTPUT_FILES,
        analysis_output_writer=write_bnt_analysis_outputs,
        analysis_extra_sheets_builder=build_bnt_analysis_extra_sheets,
        snapshot_builder=build_bnt_snapshot_metadata,
        report_title="RELATORIO - BULGARIAN NATIONAL TELEVISION",
        institutions_sheet_title="BNT Institutions",
        generated_by="scripts/run_bnt_pipeline.py",
    )


def run_ciclic_pipeline():
    _run_corpus_pipeline(
        source_label="CICLIC - Centre-Val-de-Loire",
        source_url=CICLIC_FILMS_ARCHIVES_URL,
        collect_dataset=collect_ciclic_dataset,
        institution_fields=CICLIC_INSTITUTION_FIELDS,
        summary_fields=CICLIC_SUMMARY_FIELDS,
        video_link_fields=CICLIC_VIDEO_LINK_FIELDS,
        internal_page_fields=CICLIC_INTERNAL_PAGE_FIELDS,
        output_files=CICLIC_OUTPUT_FILES,
        analysis_output_writer=write_ciclic_analysis_outputs,
        analysis_extra_sheets_builder=build_ciclic_analysis_extra_sheets,
        snapshot_builder=build_ciclic_snapshot_metadata,
        report_title="RELATORIO - CICLIC CENTRE-VAL-DE-LOIRE",
        institutions_sheet_title="CICLIC Institutions",
        generated_by="scripts/run_ciclic_pipeline.py",
    )


def run_cineam_pipeline():
    _run_corpus_pipeline(
        source_label="CINÉAM",
        source_url=CINEAM_FILMS_URL,
        collect_dataset=collect_cineam_dataset,
        institution_fields=CINEAM_INSTITUTION_FIELDS,
        summary_fields=CINEAM_SUMMARY_FIELDS,
        video_link_fields=CINEAM_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEAM_INTERNAL_PAGE_FIELDS,
        output_files=CINEAM_OUTPUT_FILES,
        analysis_output_writer=write_cineam_analysis_outputs,
        analysis_extra_sheets_builder=build_cineam_analysis_extra_sheets,
        snapshot_builder=build_cineam_snapshot_metadata,
        report_title="RELATORIO - CINEAM",
        institutions_sheet_title="CINÉAM Institutions",
        generated_by="scripts/run_cineam_pipeline.py",
    )


def run_cinememoire_pipeline():
    _run_corpus_pipeline(
        source_label="Cinémémoire",
        source_url=CINEMEMOIRE_SEARCH_URL,
        collect_dataset=collect_cinememoire_dataset,
        institution_fields=CINEMEMOIRE_INSTITUTION_FIELDS,
        summary_fields=CINEMEMOIRE_SUMMARY_FIELDS,
        video_link_fields=CINEMEMOIRE_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEMEMOIRE_INTERNAL_PAGE_FIELDS,
        output_files=CINEMEMOIRE_OUTPUT_FILES,
        analysis_output_writer=write_cinememoire_analysis_outputs,
        analysis_extra_sheets_builder=build_cinememoire_analysis_extra_sheets,
        snapshot_builder=build_cinememoire_snapshot_metadata,
        report_title="RELATORIO - CINEMEMOIRE",
        institutions_sheet_title="Cinémémoire",
        generated_by="scripts/run_cinememoire_pipeline.py",
    )


def run_ccma_pipeline():
    _run_corpus_pipeline(
        source_label="CCMA/3Cat",
        source_url=CCMA_SEARCH_API_URL,
        collect_dataset=collect_ccma_dataset,
        institution_fields=CCMA_INSTITUTION_FIELDS,
        summary_fields=CCMA_SUMMARY_FIELDS,
        video_link_fields=CCMA_VIDEO_LINK_FIELDS,
        internal_page_fields=CCMA_INTERNAL_PAGE_FIELDS,
        output_files=CCMA_OUTPUT_FILES,
        analysis_output_writer=write_ccma_analysis_outputs,
        analysis_extra_sheets_builder=build_ccma_analysis_extra_sheets,
        snapshot_builder=build_ccma_snapshot_metadata,
        report_title="RELATORIO - CCMA/3CAT",
        institutions_sheet_title="CCMA 3Cat",
        generated_by="scripts/run_ccma_pipeline.py",
    )


def run_czech_television_pipeline():
    _run_corpus_pipeline(
        source_label="Czech Television / iVysílání",
        source_url=CZECH_TELEVISION_IVYSILANI_URL,
        collect_dataset=collect_czech_television_dataset,
        institution_fields=CZECH_TELEVISION_INSTITUTION_FIELDS,
        summary_fields=CZECH_TELEVISION_SUMMARY_FIELDS,
        video_link_fields=CZECH_TELEVISION_VIDEO_LINK_FIELDS,
        internal_page_fields=CZECH_TELEVISION_INTERNAL_PAGE_FIELDS,
        output_files=CZECH_TELEVISION_OUTPUT_FILES,
        analysis_output_writer=write_czech_television_analysis_outputs,
        analysis_extra_sheets_builder=build_czech_television_analysis_extra_sheets,
        snapshot_builder=build_czech_television_snapshot_metadata,
        report_title="RELATORIO - CZECH TELEVISION",
        institutions_sheet_title="Czech Television",
        generated_by="scripts/run_czech_television_pipeline.py",
    )


def run_dff_pipeline():
    _run_corpus_pipeline(
        source_label="DFF / filmportal.de",
        source_url=DFF_FILMPORTAL_VIDEOS_URL,
        collect_dataset=collect_dff_dataset,
        institution_fields=DFF_INSTITUTION_FIELDS,
        summary_fields=DFF_SUMMARY_FIELDS,
        video_link_fields=DFF_VIDEO_LINK_FIELDS,
        internal_page_fields=DFF_INTERNAL_PAGE_FIELDS,
        output_files=DFF_OUTPUT_FILES,
        analysis_output_writer=write_dff_analysis_outputs,
        analysis_extra_sheets_builder=build_dff_analysis_extra_sheets,
        snapshot_builder=build_dff_snapshot_metadata,
        report_title="RELATORIO - DFF FILMPORTAL",
        institutions_sheet_title="DFF filmportal.de",
        generated_by="scripts/run_dff_pipeline.py",
    )


def run_dhm_pipeline():
    _run_corpus_pipeline(
        source_label="DHM / Zeughauskino",
        source_url=DHM_MARSHALL_PLAN_URL,
        collect_dataset=collect_dhm_dataset,
        institution_fields=DHM_INSTITUTION_FIELDS,
        summary_fields=DHM_SUMMARY_FIELDS,
        video_link_fields=DHM_VIDEO_LINK_FIELDS,
        internal_page_fields=DHM_INTERNAL_PAGE_FIELDS,
        output_files=DHM_OUTPUT_FILES,
        analysis_output_writer=write_dhm_analysis_outputs,
        analysis_extra_sheets_builder=build_dhm_analysis_extra_sheets,
        snapshot_builder=build_dhm_snapshot_metadata,
        report_title="RELATORIO - DHM ZEUGHAUSKINO",
        institutions_sheet_title="DHM Zeughauskino",
        generated_by="scripts/run_dhm_pipeline.py",
    )


def run_ecpad_pipeline():
    _run_corpus_pipeline(
        source_label="ECPAD Archives",
        source_url=ECPAD_ONLINE_ARCHIVES_URL,
        collect_dataset=collect_ecpad_dataset,
        institution_fields=ECPAD_INSTITUTION_FIELDS,
        summary_fields=ECPAD_SUMMARY_FIELDS,
        video_link_fields=ECPAD_VIDEO_LINK_FIELDS,
        internal_page_fields=ECPAD_INTERNAL_PAGE_FIELDS,
        output_files=ECPAD_OUTPUT_FILES,
        analysis_output_writer=write_ecpad_analysis_outputs,
        analysis_extra_sheets_builder=build_ecpad_analysis_extra_sheets,
        snapshot_builder=build_ecpad_snapshot_metadata,
        report_title="RELATORIO - ECPAD ARCHIVES",
        institutions_sheet_title="ECPAD Archives",
        generated_by="scripts/run_ecpad_pipeline.py",
    )


def run_eafa_pipeline():
    _run_corpus_pipeline(
        source_label="East Anglian Film Archive",
        source_url=EAFA_HOME_URL,
        collect_dataset=collect_eafa_dataset,
        institution_fields=EAFA_INSTITUTION_FIELDS,
        summary_fields=EAFA_SUMMARY_FIELDS,
        video_link_fields=EAFA_VIDEO_LINK_FIELDS,
        internal_page_fields=EAFA_INTERNAL_PAGE_FIELDS,
        output_files=EAFA_OUTPUT_FILES,
        analysis_output_writer=write_eafa_analysis_outputs,
        analysis_extra_sheets_builder=build_eafa_analysis_extra_sheets,
        snapshot_builder=build_eafa_snapshot_metadata,
        report_title="RELATORIO - EAST ANGLIAN FILM ARCHIVE",
        institutions_sheet_title="EAFA",
        generated_by="scripts/run_eafa_pipeline.py",
    )


def run_ert_pipeline():
    _run_corpus_pipeline(
        source_label="ERT Archive",
        source_url=ERT_ARCHIVE_HOME_URL,
        collect_dataset=collect_ert_dataset,
        institution_fields=ERT_INSTITUTION_FIELDS,
        summary_fields=ERT_SUMMARY_FIELDS,
        video_link_fields=ERT_VIDEO_LINK_FIELDS,
        internal_page_fields=ERT_INTERNAL_PAGE_FIELDS,
        output_files=ERT_OUTPUT_FILES,
        analysis_output_writer=write_ert_analysis_outputs,
        analysis_extra_sheets_builder=build_ert_analysis_extra_sheets,
        snapshot_builder=build_ert_snapshot_metadata,
        report_title="RELATORIO - ERT ARCHIVE",
        institutions_sheet_title="ERT Archive",
        generated_by="scripts/run_ert_pipeline.py",
    )


def run_deutsche_kinemathek_pipeline():
    _run_corpus_pipeline(
        source_label="Deutsche Kinemathek / Selects",
        source_url=DEUTSCHE_KINEMATHEK_STREAMING_URL,
        collect_dataset=collect_deutsche_kinemathek_dataset,
        institution_fields=DEUTSCHE_KINEMATHEK_INSTITUTION_FIELDS,
        summary_fields=DEUTSCHE_KINEMATHEK_SUMMARY_FIELDS,
        video_link_fields=DEUTSCHE_KINEMATHEK_VIDEO_LINK_FIELDS,
        internal_page_fields=DEUTSCHE_KINEMATHEK_INTERNAL_PAGE_FIELDS,
        output_files=DEUTSCHE_KINEMATHEK_OUTPUT_FILES,
        analysis_output_writer=write_deutsche_kinemathek_analysis_outputs,
        analysis_extra_sheets_builder=build_deutsche_kinemathek_analysis_extra_sheets,
        snapshot_builder=build_deutsche_kinemathek_snapshot_metadata,
        report_title="RELATORIO - DEUTSCHE KINEMATHEK SELECTS",
        institutions_sheet_title="Deutsche Kinemathek",
        generated_by="scripts/run_deutsche_kinemathek_pipeline.py",
    )


def run_dr_pipeline():
    _run_corpus_pipeline(
        source_label="DR / DRTV-Gensyn",
        source_url=DR_GENSYN_URL,
        collect_dataset=collect_dr_dataset,
        institution_fields=DR_INSTITUTION_FIELDS,
        summary_fields=DR_SUMMARY_FIELDS,
        video_link_fields=DR_VIDEO_LINK_FIELDS,
        internal_page_fields=DR_INTERNAL_PAGE_FIELDS,
        output_files=DR_OUTPUT_FILES,
        analysis_output_writer=write_dr_analysis_outputs,
        analysis_extra_sheets_builder=build_dr_analysis_extra_sheets,
        snapshot_builder=build_dr_snapshot_metadata,
        report_title="RELATORIO - DR DRTV-GENSYN",
        institutions_sheet_title="DR DRTV-Gensyn",
        generated_by="scripts/run_dr_pipeline.py",
    )


def run_cinearchives_pipeline():
    _run_corpus_pipeline(
        source_label="Ciné-Archives",
        source_url=CINEARCHIVES_CATALOG_URL,
        collect_dataset=collect_cinearchives_dataset,
        institution_fields=CINEARCHIVES_INSTITUTION_FIELDS,
        summary_fields=CINEARCHIVES_SUMMARY_FIELDS,
        video_link_fields=CINEARCHIVES_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEARCHIVES_INTERNAL_PAGE_FIELDS,
        output_files=CINEARCHIVES_OUTPUT_FILES,
        analysis_output_writer=write_cinearchives_analysis_outputs,
        analysis_extra_sheets_builder=build_cinearchives_analysis_extra_sheets,
        snapshot_builder=build_cinearchives_snapshot_metadata,
        report_title="RELATORIO - CINE-ARCHIVES",
        institutions_sheet_title="Ciné-Archives",
        generated_by="scripts/run_cinearchives_pipeline.py",
    )


def run_cinematheque_bretagne_pipeline():
    _run_corpus_pipeline(
        source_label="Cinémathèque de Bretagne",
        source_url=CINEMATHEQUE_BRETAGNE_FILMS_URL,
        collect_dataset=collect_cinematheque_bretagne_dataset,
        institution_fields=CINEMATHEQUE_BRETAGNE_INSTITUTION_FIELDS,
        summary_fields=CINEMATHEQUE_BRETAGNE_SUMMARY_FIELDS,
        video_link_fields=CINEMATHEQUE_BRETAGNE_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEMATHEQUE_BRETAGNE_INTERNAL_PAGE_FIELDS,
        output_files=CINEMATHEQUE_BRETAGNE_OUTPUT_FILES,
        analysis_output_writer=write_cinematheque_bretagne_analysis_outputs,
        analysis_extra_sheets_builder=build_cinematheque_bretagne_analysis_extra_sheets,
        snapshot_builder=build_cinematheque_bretagne_snapshot_metadata,
        report_title="RELATORIO - CINEMATHEQUE DE BRETAGNE",
        institutions_sheet_title="Cinémathèque de Bretagne",
        generated_by="scripts/run_cinematheque_bretagne_pipeline.py",
    )


def run_cinematheque_francaise_pipeline():
    _run_corpus_pipeline(
        source_label="Cinémathèque française / HENRI",
        source_url=CINEMATHEQUE_FRANCAISE_HENRI_URL,
        collect_dataset=collect_cinematheque_francaise_dataset,
        institution_fields=CINEMATHEQUE_FRANCAISE_INSTITUTION_FIELDS,
        summary_fields=CINEMATHEQUE_FRANCAISE_SUMMARY_FIELDS,
        video_link_fields=CINEMATHEQUE_FRANCAISE_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEMATHEQUE_FRANCAISE_INTERNAL_PAGE_FIELDS,
        output_files=CINEMATHEQUE_FRANCAISE_OUTPUT_FILES,
        analysis_output_writer=write_cinematheque_francaise_analysis_outputs,
        analysis_extra_sheets_builder=build_cinematheque_francaise_analysis_extra_sheets,
        snapshot_builder=build_cinematheque_francaise_snapshot_metadata,
        report_title="RELATORIO - CINEMATHEQUE FRANCAISE",
        institutions_sheet_title="Cinémathèque française",
        generated_by="scripts/run_cinematheque_francaise_pipeline.py",
    )


def run_cinematek_pipeline():
    _run_corpus_pipeline(
        source_label="CINEMATEK",
        source_url=CINEMATEK_BE_FILM_URL,
        collect_dataset=collect_cinematek_dataset,
        institution_fields=CINEMATEK_INSTITUTION_FIELDS,
        summary_fields=CINEMATEK_SUMMARY_FIELDS,
        video_link_fields=CINEMATEK_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEMATEK_INTERNAL_PAGE_FIELDS,
        output_files=CINEMATEK_OUTPUT_FILES,
        analysis_output_writer=write_cinematek_analysis_outputs,
        analysis_extra_sheets_builder=build_cinematek_analysis_extra_sheets,
        snapshot_builder=build_cinematek_snapshot_metadata,
        report_title="RELATORIO - CINEMATEK",
        institutions_sheet_title="CINEMATEK",
        generated_by="scripts/run_cinematek_pipeline.py",
    )


def run_eye_pipeline():
    _run_corpus_pipeline(
        source_label="Eye Filmmuseum",
        source_url=EYE_FILM_FRAGMENT_LIST_URL,
        collect_dataset=collect_eye_dataset,
        institution_fields=EYE_INSTITUTION_FIELDS,
        summary_fields=EYE_SUMMARY_FIELDS,
        video_link_fields=EYE_VIDEO_LINK_FIELDS,
        internal_page_fields=EYE_INTERNAL_PAGE_FIELDS,
        output_files=EYE_OUTPUT_FILES,
        analysis_output_writer=write_eye_analysis_outputs,
        analysis_extra_sheets_builder=build_eye_analysis_extra_sheets,
        snapshot_builder=build_eye_snapshot_metadata,
        report_title="RELATORIO - EYE FILMMUSEUM",
        institutions_sheet_title="Eye Filmmuseum",
        generated_by="scripts/run_eye_pipeline.py",
    )


def run_estonian_film_archive_pipeline():
    _run_corpus_pipeline(
        source_label="Film Archive of the National Archives of Estonia / Arkaader",
        source_url=ARKAADER_FILM_SHELF_URL,
        collect_dataset=collect_estonian_film_archive_dataset,
        institution_fields=ESTONIAN_FILM_ARCHIVE_INSTITUTION_FIELDS,
        summary_fields=ESTONIAN_FILM_ARCHIVE_SUMMARY_FIELDS,
        video_link_fields=ESTONIAN_FILM_ARCHIVE_VIDEO_LINK_FIELDS,
        internal_page_fields=ESTONIAN_FILM_ARCHIVE_INTERNAL_PAGE_FIELDS,
        output_files=ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES,
        analysis_output_writer=write_estonian_film_archive_analysis_outputs,
        analysis_extra_sheets_builder=build_estonian_film_archive_analysis_extra_sheets,
        snapshot_builder=build_estonian_film_archive_snapshot_metadata,
        report_title="RELATORIO - ESTONIAN FILM ARCHIVE / ARKAADER",
        institutions_sheet_title="Estonian Film Archive",
        generated_by="scripts/run_estonian_film_archive_pipeline.py",
    )


def run_filmarchiv_austria_pipeline():
    _run_corpus_pipeline(
        source_label="Filmarchiv Austria / Filmarchiv ON",
        source_url=FILMARCHIV_AUSTRIA_ON_URL,
        collect_dataset=collect_filmarchiv_austria_dataset,
        institution_fields=FILMARCHIV_AUSTRIA_INSTITUTION_FIELDS,
        summary_fields=FILMARCHIV_AUSTRIA_SUMMARY_FIELDS,
        video_link_fields=FILMARCHIV_AUSTRIA_VIDEO_LINK_FIELDS,
        internal_page_fields=FILMARCHIV_AUSTRIA_INTERNAL_PAGE_FIELDS,
        output_files=FILMARCHIV_AUSTRIA_OUTPUT_FILES,
        analysis_output_writer=write_filmarchiv_austria_analysis_outputs,
        analysis_extra_sheets_builder=build_filmarchiv_austria_analysis_extra_sheets,
        snapshot_builder=build_filmarchiv_austria_snapshot_metadata,
        report_title="RELATORIO - FILMARCHIV AUSTRIA / FILMARCHIV ON",
        institutions_sheet_title="Filmarchiv Austria",
        generated_by="scripts/run_filmarchiv_austria_pipeline.py",
    )


def run_filmmuseum_dusseldorf_pipeline():
    _run_corpus_pipeline(
        source_label="Filmmuseum Düsseldorf / d:kult online",
        source_url=DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL,
        collect_dataset=collect_filmmuseum_dusseldorf_dataset,
        institution_fields=FILMMUSEUM_DUSSELDORF_INSTITUTION_FIELDS,
        summary_fields=FILMMUSEUM_DUSSELDORF_SUMMARY_FIELDS,
        video_link_fields=FILMMUSEUM_DUSSELDORF_VIDEO_LINK_FIELDS,
        internal_page_fields=FILMMUSEUM_DUSSELDORF_INTERNAL_PAGE_FIELDS,
        output_files=FILMMUSEUM_DUSSELDORF_OUTPUT_FILES,
        analysis_output_writer=write_filmmuseum_dusseldorf_analysis_outputs,
        analysis_extra_sheets_builder=build_filmmuseum_dusseldorf_analysis_extra_sheets,
        snapshot_builder=build_filmmuseum_dusseldorf_snapshot_metadata,
        report_title="RELATORIO - FILMMUSEUM DUSSELDORF / D:KULT ONLINE",
        institutions_sheet_title="Filmmuseum Düsseldorf",
        generated_by="scripts/run_filmmuseum_dusseldorf_pipeline.py",
    )


def run_filmoteca_catalunya_pipeline():
    _run_corpus_pipeline(
        source_label="Filmoteca de Catalunya / PLATFO FILMO",
        source_url=FILMOTECA_CATALUNYA_PLATFO_URL,
        collect_dataset=collect_filmoteca_catalunya_dataset,
        institution_fields=FILMOTECA_CATALUNYA_INSTITUTION_FIELDS,
        summary_fields=FILMOTECA_CATALUNYA_SUMMARY_FIELDS,
        video_link_fields=FILMOTECA_CATALUNYA_VIDEO_LINK_FIELDS,
        internal_page_fields=FILMOTECA_CATALUNYA_INTERNAL_PAGE_FIELDS,
        output_files=FILMOTECA_CATALUNYA_OUTPUT_FILES,
        analysis_output_writer=write_filmoteca_catalunya_analysis_outputs,
        analysis_extra_sheets_builder=build_filmoteca_catalunya_analysis_extra_sheets,
        snapshot_builder=build_filmoteca_catalunya_snapshot_metadata,
        report_title="RELATORIO - FILMOTECA DE CATALUNYA / PLATFO FILMO",
        institutions_sheet_title="Filmoteca de Catalunya",
        generated_by="scripts/run_filmoteca_catalunya_pipeline.py",
    )


def run_filmoteca_espanola_pipeline():
    _run_corpus_pipeline(
        source_label="Filmoteca Española / PLATFO FILMO",
        source_url=FILMOTECA_ESPANOLA_PLATFO_URL,
        collect_dataset=collect_filmoteca_espanola_dataset,
        institution_fields=FILMOTECA_ESPANOLA_INSTITUTION_FIELDS,
        summary_fields=FILMOTECA_ESPANOLA_SUMMARY_FIELDS,
        video_link_fields=FILMOTECA_ESPANOLA_VIDEO_LINK_FIELDS,
        internal_page_fields=FILMOTECA_ESPANOLA_INTERNAL_PAGE_FIELDS,
        output_files=FILMOTECA_ESPANOLA_OUTPUT_FILES,
        analysis_output_writer=write_filmoteca_espanola_analysis_outputs,
        analysis_extra_sheets_builder=build_filmoteca_espanola_analysis_extra_sheets,
        snapshot_builder=build_filmoteca_espanola_snapshot_metadata,
        report_title="RELATORIO - FILMOTECA ESPAÑOLA / PLATFO FILMO",
        institutions_sheet_title="Filmoteca Española",
        generated_by="scripts/run_filmoteca_espanola_pipeline.py",
    )


def run_filmoteca_valenciana_pipeline():
    _run_corpus_pipeline(
        source_label="Filmoteca Valenciana / Restauraciones",
        source_url=FILMOTECA_VALENCIANA_RESTORATIONS_URL,
        collect_dataset=collect_filmoteca_valenciana_dataset,
        institution_fields=FILMOTECA_VALENCIANA_INSTITUTION_FIELDS,
        summary_fields=FILMOTECA_VALENCIANA_SUMMARY_FIELDS,
        video_link_fields=FILMOTECA_VALENCIANA_VIDEO_LINK_FIELDS,
        internal_page_fields=FILMOTECA_VALENCIANA_INTERNAL_PAGE_FIELDS,
        output_files=FILMOTECA_VALENCIANA_OUTPUT_FILES,
        analysis_output_writer=write_filmoteca_valenciana_analysis_outputs,
        analysis_extra_sheets_builder=build_filmoteca_valenciana_analysis_extra_sheets,
        snapshot_builder=build_filmoteca_valenciana_snapshot_metadata,
        report_title="RELATORIO - FILMOTECA VALENCIANA / RESTAURACIONES",
        institutions_sheet_title="Filmoteca Valenciana",
        generated_by="scripts/run_filmoteca_valenciana_pipeline.py",
    )


def run_cinematheque_suisse_pipeline():
    _run_corpus_pipeline(
        source_label="Cinémathèque suisse",
        source_url=CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
        collect_dataset=collect_cinematheque_suisse_dataset,
        institution_fields=CINEMATHEQUE_SUISSE_INSTITUTION_FIELDS,
        summary_fields=CINEMATHEQUE_SUISSE_SUMMARY_FIELDS,
        video_link_fields=CINEMATHEQUE_SUISSE_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEMATHEQUE_SUISSE_INTERNAL_PAGE_FIELDS,
        output_files=CINEMATHEQUE_SUISSE_OUTPUT_FILES,
        analysis_output_writer=write_cinematheque_suisse_analysis_outputs,
        analysis_extra_sheets_builder=build_cinematheque_suisse_analysis_extra_sheets,
        snapshot_builder=build_cinematheque_suisse_snapshot_metadata,
        report_title="RELATORIO - CINEMATHEQUE SUISSE",
        institutions_sheet_title="Cinémathèque suisse",
        generated_by="scripts/run_cinematheque_suisse_pipeline.py",
    )


def run_cpsa_pipeline():
    _run_corpus_pipeline(
        source_label="Cinémathèque des Pays de Savoie et de l'Ain",
        source_url=CPSA_FILMS_URL,
        collect_dataset=collect_cpsa_dataset,
        institution_fields=CPSA_INSTITUTION_FIELDS,
        summary_fields=CPSA_SUMMARY_FIELDS,
        video_link_fields=CPSA_VIDEO_LINK_FIELDS,
        internal_page_fields=CPSA_INTERNAL_PAGE_FIELDS,
        output_files=CPSA_OUTPUT_FILES,
        analysis_output_writer=write_cpsa_analysis_outputs,
        analysis_extra_sheets_builder=build_cpsa_analysis_extra_sheets,
        snapshot_builder=build_cpsa_snapshot_metadata,
        report_title="RELATORIO - CPSA",
        institutions_sheet_title="CPSA",
        generated_by="scripts/run_cpsa_pipeline.py",
    )


def run_saint_etienne_pipeline():
    _run_corpus_pipeline(
        source_label="Cinémathèque de Saint-Étienne",
        source_url=SAINT_ETIENNE_COLLECTIONS_URL,
        collect_dataset=collect_saint_etienne_dataset,
        institution_fields=SAINT_ETIENNE_INSTITUTION_FIELDS,
        summary_fields=SAINT_ETIENNE_SUMMARY_FIELDS,
        video_link_fields=SAINT_ETIENNE_VIDEO_LINK_FIELDS,
        internal_page_fields=SAINT_ETIENNE_INTERNAL_PAGE_FIELDS,
        output_files=SAINT_ETIENNE_OUTPUT_FILES,
        analysis_output_writer=write_saint_etienne_analysis_outputs,
        analysis_extra_sheets_builder=build_saint_etienne_analysis_extra_sheets,
        snapshot_builder=build_saint_etienne_snapshot_metadata,
        report_title="RELATORIO - CINEMATHEQUE DE SAINT-ETIENNE",
        institutions_sheet_title="Cinémathèque de Saint-Étienne",
        generated_by="scripts/run_saint_etienne_pipeline.py",
    )


def run_cdna_pipeline():
    _run_corpus_pipeline(
        source_label="Cinémathèque de Nouvelle-Aquitaine",
        source_url=CDNA_FILMS_URL,
        collect_dataset=collect_cdna_dataset,
        institution_fields=CDNA_INSTITUTION_FIELDS,
        summary_fields=CDNA_SUMMARY_FIELDS,
        video_link_fields=CDNA_VIDEO_LINK_FIELDS,
        internal_page_fields=CDNA_INTERNAL_PAGE_FIELDS,
        output_files=CDNA_OUTPUT_FILES,
        analysis_output_writer=write_cdna_analysis_outputs,
        analysis_extra_sheets_builder=build_cdna_analysis_extra_sheets,
        snapshot_builder=build_cdna_snapshot_metadata,
        report_title="RELATORIO - CINEMATHEQUE DE NOUVELLE-AQUITAINE",
        institutions_sheet_title="CdNA",
        generated_by="scripts/run_cdna_pipeline.py",
    )


def run_luce_pipeline():
    _run_corpus_pipeline(
        source_label="Cinecittà - Archivio Luce",
        source_url=LUCE_CATALOG_FILMS_URL,
        collect_dataset=collect_luce_dataset,
        institution_fields=LUCE_INSTITUTION_FIELDS,
        summary_fields=LUCE_SUMMARY_FIELDS,
        video_link_fields=LUCE_VIDEO_LINK_FIELDS,
        internal_page_fields=LUCE_INTERNAL_PAGE_FIELDS,
        output_files=LUCE_OUTPUT_FILES,
        analysis_output_writer=write_luce_analysis_outputs,
        analysis_extra_sheets_builder=build_luce_analysis_extra_sheets,
        snapshot_builder=build_luce_snapshot_metadata,
        report_title="RELATORIO - CINECITTA ARCHIVIO LUCE",
        institutions_sheet_title="Archivio Luce Institutions",
        generated_by="scripts/run_luce_pipeline.py",
    )


def run_cinemateca_portuguesa_pipeline():
    _run_corpus_pipeline(
        source_label="Cinemateca Portuguesa - Museu do Cinema",
        source_url=CINEMATECA_PT_VIDEO_LIST_URL,
        collect_dataset=collect_cinemateca_portuguesa_dataset,
        institution_fields=CINEMATECA_PT_INSTITUTION_FIELDS,
        summary_fields=CINEMATECA_PT_SUMMARY_FIELDS,
        video_link_fields=CINEMATECA_PT_VIDEO_LINK_FIELDS,
        internal_page_fields=CINEMATECA_PT_INTERNAL_PAGE_FIELDS,
        output_files=CINEMATECA_PT_OUTPUT_FILES,
        analysis_output_writer=write_cinemateca_portuguesa_analysis_outputs,
        analysis_extra_sheets_builder=build_cinemateca_portuguesa_analysis_extra_sheets,
        snapshot_builder=build_cinemateca_portuguesa_snapshot_metadata,
        report_title="RELATORIO - CINEMATECA PORTUGUESA",
        institutions_sheet_title="Cinemateca Portuguesa",
        generated_by="scripts/run_cinemateca_portuguesa_pipeline.py",
    )


def run_filmoteca_vasca_pipeline():
    _run_corpus_pipeline(
        source_label="Filmoteca Vasca",
        source_url=FILMOTECA_VASCA_MULTIMEDIA_URL,
        collect_dataset=collect_filmoteca_vasca_dataset,
        institution_fields=FILMOTECA_VASCA_INSTITUTION_FIELDS,
        summary_fields=FILMOTECA_VASCA_SUMMARY_FIELDS,
        video_link_fields=FILMOTECA_VASCA_VIDEO_LINK_FIELDS,
        internal_page_fields=FILMOTECA_VASCA_INTERNAL_PAGE_FIELDS,
        output_files=FILMOTECA_VASCA_OUTPUT_FILES,
        analysis_output_writer=write_filmoteca_vasca_analysis_outputs,
        analysis_extra_sheets_builder=build_filmoteca_vasca_analysis_extra_sheets,
        snapshot_builder=build_filmoteca_vasca_snapshot_metadata,
        report_title="RELATORIO - FILMOTECA VASCA",
        institutions_sheet_title="Filmoteca Vasca",
        generated_by="scripts/run_filmoteca_vasca_pipeline.py",
    )


def run_cna_pipeline():
    _run_corpus_pipeline(
        source_label="Centre national de l'audiovisuel (CNA)",
        source_url=CNA_SEARCH_PROFILE_URL,
        collect_dataset=collect_cna_dataset,
        institution_fields=CNA_INSTITUTION_FIELDS,
        summary_fields=CNA_SUMMARY_FIELDS,
        video_link_fields=CNA_VIDEO_LINK_FIELDS,
        internal_page_fields=CNA_INTERNAL_PAGE_FIELDS,
        output_files=CNA_OUTPUT_FILES,
        analysis_output_writer=write_cna_analysis_outputs,
        analysis_extra_sheets_builder=build_cna_analysis_extra_sheets,
        snapshot_builder=build_cna_snapshot_metadata,
        report_title="RELATORIO - CNA LUXEMBOURG",
        institutions_sheet_title="CNA Luxembourg Institutions",
        generated_by="scripts/run_cna_pipeline.py",
    )


def run_cnc_aff_pipeline():
    _run_corpus_pipeline(
        source_label="CNC - Archives françaises du film",
        source_url=CNCAFF_EFG_SEARCH_URL,
        collect_dataset=collect_cnc_aff_dataset,
        institution_fields=CNCAFF_INSTITUTION_FIELDS,
        summary_fields=CNCAFF_SUMMARY_FIELDS,
        video_link_fields=CNCAFF_VIDEO_LINK_FIELDS,
        internal_page_fields=CNCAFF_INTERNAL_PAGE_FIELDS,
        output_files=CNCAFF_OUTPUT_FILES,
        analysis_output_writer=write_cnc_aff_analysis_outputs,
        analysis_extra_sheets_builder=build_cnc_aff_analysis_extra_sheets,
        snapshot_builder=build_cnc_aff_snapshot_metadata,
        report_title="RELATORIO - CNC ARCHIVES FRANCAISES DU FILM",
        institutions_sheet_title="CNC AFF Institutions",
        generated_by="scripts/run_cnc_aff_pipeline.py",
    )


def run_bnfa_pipeline():
    _run_corpus_pipeline(
        source_label="Bulgarian National Film Archive",
        source_url=BNFA_EFG_COLLECTION_URL,
        collect_dataset=collect_bnfa_dataset,
        institution_fields=BNFA_INSTITUTION_FIELDS,
        summary_fields=BNFA_SUMMARY_FIELDS,
        video_link_fields=BNFA_VIDEO_LINK_FIELDS,
        internal_page_fields=BNFA_INTERNAL_PAGE_FIELDS,
        output_files=BNFA_OUTPUT_FILES,
        analysis_output_writer=write_bnfa_analysis_outputs,
        analysis_extra_sheets_builder=build_bnfa_analysis_extra_sheets,
        snapshot_builder=build_bnfa_snapshot_metadata,
        report_title="RELATORIO - BULGARIAN NATIONAL FILM ARCHIVE",
        institutions_sheet_title="BNFA Institutions",
        generated_by="scripts/run_bnfa_pipeline.py",
    )


def run_asim_pipeline():
    _run_corpus_pipeline(
        source_label="Arxiu del So i de la Imatge de Mallorca",
        source_url=ASIM_EFG_SEARCH_URL,
        collect_dataset=collect_asim_dataset,
        institution_fields=ASIM_INSTITUTION_FIELDS,
        summary_fields=ASIM_SUMMARY_FIELDS,
        video_link_fields=ASIM_VIDEO_LINK_FIELDS,
        internal_page_fields=ASIM_INTERNAL_PAGE_FIELDS,
        output_files=ASIM_OUTPUT_FILES,
        analysis_output_writer=write_asim_analysis_outputs,
        analysis_extra_sheets_builder=build_asim_analysis_extra_sheets,
        snapshot_builder=build_asim_snapshot_metadata,
        report_title="RELATORIO - ASIM MALLORCA",
        institutions_sheet_title="ASIM Institutions",
        generated_by="scripts/run_asim_pipeline.py",
    )


def run_crnogorska_kinoteka_pipeline():
    _run_corpus_pipeline(
        source_label="Crnogorska Kinoteka",
        source_url=CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
        collect_dataset=collect_crnogorska_kinoteka_dataset,
        institution_fields=CRNOGORSKA_KINOTEKA_INSTITUTION_FIELDS,
        summary_fields=CRNOGORSKA_KINOTEKA_SUMMARY_FIELDS,
        video_link_fields=CRNOGORSKA_KINOTEKA_VIDEO_LINK_FIELDS,
        internal_page_fields=CRNOGORSKA_KINOTEKA_INTERNAL_PAGE_FIELDS,
        output_files=CRNOGORSKA_KINOTEKA_OUTPUT_FILES,
        analysis_output_writer=write_crnogorska_kinoteka_analysis_outputs,
        analysis_extra_sheets_builder=build_crnogorska_kinoteka_analysis_extra_sheets,
        snapshot_builder=build_crnogorska_kinoteka_snapshot_metadata,
        report_title="RELATORIO - CRNOGORSKA KINOTEKA",
        institutions_sheet_title="Crnogorska Kinoteka",
        generated_by="scripts/run_crnogorska_kinoteka_pipeline.py",
    )


def run_arsenal_pipeline():
    _run_corpus_pipeline(
        source_label="Arsenal Filminstitut",
        source_url=ARSENAL_FILM_DATABASE_BROWSE_URL,
        collect_dataset=collect_arsenal_dataset,
        institution_fields=ARSENAL_INSTITUTION_FIELDS,
        summary_fields=ARSENAL_SUMMARY_FIELDS,
        video_link_fields=ARSENAL_VIDEO_LINK_FIELDS,
        internal_page_fields=ARSENAL_INTERNAL_PAGE_FIELDS,
        output_files=ARSENAL_OUTPUT_FILES,
        analysis_output_writer=write_arsenal_analysis_outputs,
        analysis_extra_sheets_builder=build_arsenal_analysis_extra_sheets,
        snapshot_builder=build_arsenal_snapshot_metadata,
        report_title="RELATORIO - ARSENAL FILMINSTITUT",
        institutions_sheet_title="Arsenal Institutions",
        generated_by="scripts/run_arsenal_pipeline.py",
    )


def run_euscreen_pipeline():
    _run_corpus_pipeline(
        source_label="EUscreen",
        source_url=EUSCREEN_COLLECTIONS_URL,
        collect_dataset=collect_euscreen_dataset,
        institution_fields=EUSCREEN_INSTITUTION_FIELDS,
        summary_fields=EUSCREEN_SUMMARY_FIELDS,
        video_link_fields=EUSCREEN_VIDEO_LINK_FIELDS,
        internal_page_fields=EUSCREEN_INTERNAL_PAGE_FIELDS,
        output_files=EUSCREEN_OUTPUT_FILES,
        analysis_output_writer=write_euscreen_analysis_outputs,
        analysis_extra_sheets_builder=build_euscreen_analysis_extra_sheets,
        snapshot_builder=build_euscreen_snapshot_metadata,
        report_title="RELATORIO - EUSCREEN",
        institutions_sheet_title="EUscreen Institutions",
        generated_by="scripts/run_euscreen_pipeline.py",
    )


def run_european_film_gateway_pipeline():
    _run_corpus_pipeline(
        source_label="European Film Gateway",
        source_url=EUROPEAN_FILM_GATEWAY_HOME_URL,
        collect_dataset=collect_european_film_gateway_dataset,
        institution_fields=EUROPEAN_FILM_GATEWAY_INSTITUTION_FIELDS,
        summary_fields=EUROPEAN_FILM_GATEWAY_SUMMARY_FIELDS,
        video_link_fields=EUROPEAN_FILM_GATEWAY_VIDEO_LINK_FIELDS,
        internal_page_fields=EUROPEAN_FILM_GATEWAY_INTERNAL_PAGE_FIELDS,
        output_files=EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
        analysis_output_writer=write_european_film_gateway_analysis_outputs,
        analysis_extra_sheets_builder=build_european_film_gateway_analysis_extra_sheets,
        snapshot_builder=build_european_film_gateway_snapshot_metadata,
        report_title="RELATORIO - EUROPEAN FILM GATEWAY",
        institutions_sheet_title="EFG Institutions",
        generated_by="scripts/run_european_film_gateway_pipeline.py",
    )


def run_europeana_pipeline():
    _run_corpus_pipeline(
        source_label="Europeana",
        source_url=EUROPEANA_HOME_URL,
        collect_dataset=collect_europeana_dataset,
        institution_fields=EUROPEANA_INSTITUTION_FIELDS,
        summary_fields=EUROPEANA_SUMMARY_FIELDS,
        video_link_fields=EUROPEANA_VIDEO_LINK_FIELDS,
        internal_page_fields=EUROPEANA_INTERNAL_PAGE_FIELDS,
        output_files=EUROPEANA_OUTPUT_FILES,
        analysis_output_writer=write_europeana_analysis_outputs,
        analysis_extra_sheets_builder=build_europeana_analysis_extra_sheets,
        snapshot_builder=build_europeana_snapshot_metadata,
        report_title="RELATORIO - EUROPEANA",
        institutions_sheet_title="Europeana Institutions",
        generated_by="scripts/run_europeana_pipeline.py",
    )


def run_pares_pipeline():
    _run_corpus_pipeline(
        source_label="PARES",
        source_url=PARES_HOME_URL,
        collect_dataset=collect_pares_dataset,
        institution_fields=PARES_INSTITUTION_FIELDS,
        summary_fields=PARES_SUMMARY_FIELDS,
        video_link_fields=PARES_VIDEO_LINK_FIELDS,
        internal_page_fields=PARES_INTERNAL_PAGE_FIELDS,
        output_files=PARES_OUTPUT_FILES,
        analysis_output_writer=write_pares_analysis_outputs,
        analysis_extra_sheets_builder=build_pares_analysis_extra_sheets,
        snapshot_builder=build_pares_snapshot_metadata,
        report_title="RELATORIO - PARES",
        institutions_sheet_title="PARES Institutions",
        generated_by="scripts/run_pares_pipeline.py",
    )


def run_ppa_pipeline():
    _run_corpus_pipeline(
        source_label="Portal Português de Arquivos",
        source_url=PPA_HOME_URL,
        collect_dataset=collect_ppa_dataset,
        institution_fields=PPA_INSTITUTION_FIELDS,
        summary_fields=PPA_SUMMARY_FIELDS,
        video_link_fields=PPA_VIDEO_LINK_FIELDS,
        internal_page_fields=PPA_INTERNAL_PAGE_FIELDS,
        output_files=PPA_OUTPUT_FILES,
        analysis_output_writer=write_ppa_analysis_outputs,
        analysis_extra_sheets_builder=build_ppa_analysis_extra_sheets,
        snapshot_builder=build_ppa_snapshot_metadata,
        report_title="RELATORIO - PORTAL PORTUGUES DE ARQUIVOS",
        institutions_sheet_title="PPA Institutions",
        generated_by="scripts/run_ppa_pipeline.py",
    )


def run_aapb_pipeline():
    _run_corpus_pipeline(
        source_label="American Archive of Public Broadcasting",
        source_url=AAPB_FAQ_URL,
        collect_dataset=collect_aapb_dataset,
        institution_fields=AAPB_INSTITUTION_FIELDS,
        summary_fields=AAPB_SUMMARY_FIELDS,
        video_link_fields=AAPB_VIDEO_LINK_FIELDS,
        internal_page_fields=AAPB_INTERNAL_PAGE_FIELDS,
        output_files=AAPB_OUTPUT_FILES,
        analysis_output_writer=write_aapb_analysis_outputs,
        analysis_extra_sheets_builder=build_aapb_analysis_extra_sheets,
        snapshot_builder=build_aapb_snapshot_metadata,
        report_title="RELATORIO - AMERICAN ARCHIVE OF PUBLIC BROADCASTING",
        institutions_sheet_title="AAPB Institutions",
        generated_by="scripts/run_aapb_pipeline.py",
    )


__all__ = [
    "run_aapb_pipeline",
    "run_aamod_pipeline",
    "run_anf_pipeline",
    "run_aqshf_pipeline",
    "run_asim_pipeline",
    "run_arsenal_pipeline",
    "run_archipop_pipeline",
    "run_autrefois_pipeline",
    "run_barch_pipeline",
    "run_bbc_pipeline",
    "run_bfi_pipeline",
    "run_bnfa_pipeline",
    "run_bnt_pipeline",
    "run_ccma_pipeline",
    "run_czech_television_pipeline",
    "run_dff_pipeline",
    "run_dhm_pipeline",
    "run_eafa_pipeline",
    "run_ecpad_pipeline",
    "run_ert_pipeline",
    "run_eye_pipeline",
    "run_estonian_film_archive_pipeline",
    "run_filmarchiv_austria_pipeline",
    "run_filmmuseum_dusseldorf_pipeline",
    "run_filmoteca_catalunya_pipeline",
    "run_filmoteca_espanola_pipeline",
    "run_filmoteca_valenciana_pipeline",
    "run_deutsche_kinemathek_pipeline",
    "run_dr_pipeline",
    "run_ciclic_pipeline",
    "run_cineam_pipeline",
    "run_cinearchives_pipeline",
    "run_cdna_pipeline",
    "run_cinematheque_bretagne_pipeline",
    "run_cinematheque_francaise_pipeline",
    "run_cinematheque_suisse_pipeline",
    "run_cinematek_pipeline",
    "run_cinememoire_pipeline",
    "run_crnogorska_kinoteka_pipeline",
    "run_cpsa_pipeline",
    "run_saint_etienne_pipeline",
    "run_cinemateca_portuguesa_pipeline",
    "run_filmoteca_vasca_pipeline",
    "run_cnc_aff_pipeline",
    "run_cna_pipeline",
    "run_luce_pipeline",
    "run_pipeline",
    "run_sfa_pipeline",
    "run_ina_pipeline",
    "run_euscreen_pipeline",
    "run_european_film_gateway_pipeline",
    "run_europeana_pipeline",
    "run_iam_pipeline",
    "run_pares_pipeline",
    "run_ppa_pipeline",
]
