import unittest

from memoria_audiovisual.dashboard_data import DASHBOARD_SOURCE_KEYS
from memoria_audiovisual.output_files import (
    AAPB_OUTPUT_FILES,
    AAMOD_OUTPUT_FILES,
    ANF_OUTPUT_FILES,
    APE_OUTPUT_FILES,
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
    DEUTSCHE_KINEMATHEK_OUTPUT_FILES,
    DR_OUTPUT_FILES,
    CICLIC_OUTPUT_FILES,
    CINEAM_OUTPUT_FILES,
    CINEARCHIVES_OUTPUT_FILES,
    CINEMEMOIRE_OUTPUT_FILES,
    CINEMATHEQUE_BRETAGNE_OUTPUT_FILES,
    CRNOGORSKA_KINOTEKA_OUTPUT_FILES,
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
    list_aapb_output_filenames,
    list_aamod_output_filenames,
    list_anf_output_filenames,
    list_ape_output_filenames,
    list_archipop_output_filenames,
    list_autrefois_output_filenames,
    list_barch_output_filenames,
    list_bbc_output_filenames,
    list_bfi_output_filenames,
    list_bnfa_output_filenames,
    list_bnt_output_filenames,
    list_ccma_output_filenames,
    list_czech_television_output_filenames,
    list_dff_output_filenames,
    list_dhm_output_filenames,
    list_eafa_output_filenames,
    list_ecpad_output_filenames,
    list_ert_output_filenames,
    list_eye_output_filenames,
    list_estonian_film_archive_output_filenames,
    list_filmarchiv_austria_output_filenames,
    list_filmmuseum_dusseldorf_output_filenames,
    list_deutsche_kinemathek_output_filenames,
    list_dr_output_filenames,
    list_ciclic_output_filenames,
    list_cineam_output_filenames,
    list_cinearchives_output_filenames,
    list_cinememoire_output_filenames,
    list_cinematheque_bretagne_output_filenames,
    list_crnogorska_kinoteka_output_filenames,
    list_cinemateca_portuguesa_output_filenames,
    list_filmoteca_vasca_output_filenames,
    list_cnc_aff_output_filenames,
    list_cna_output_filenames,
    list_euscreen_output_filenames,
    list_european_film_gateway_output_filenames,
    list_europeana_output_filenames,
    list_iam_output_filenames,
    list_ina_output_filenames,
    list_luce_output_filenames,
    list_pares_output_filenames,
    list_ppa_output_filenames,
    list_sfa_output_filenames,
)


class OutputContractsTests(unittest.TestCase):
    def test_dashboard_source_keys_exist_in_output_manifest(self):
        for key in DASHBOARD_SOURCE_KEYS:
            self.assertIn(key, APE_OUTPUT_FILES)
            self.assertIn(key, AAPB_OUTPUT_FILES)
            self.assertIn(key, AAMOD_OUTPUT_FILES)
            self.assertIn(key, ANF_OUTPUT_FILES)
            self.assertIn(key, ARCHIPOP_OUTPUT_FILES)
            self.assertIn(key, SFA_OUTPUT_FILES)
            self.assertIn(key, EUROPEAN_FILM_GATEWAY_OUTPUT_FILES)
            self.assertIn(key, EUROPEANA_OUTPUT_FILES)
            self.assertIn(key, IAM_OUTPUT_FILES)
            self.assertIn(key, AUTREFOIS_OUTPUT_FILES)
            self.assertIn(key, BARCH_OUTPUT_FILES)
            self.assertIn(key, BBC_OUTPUT_FILES)
            self.assertIn(key, BFI_OUTPUT_FILES)
            self.assertIn(key, BNFA_OUTPUT_FILES)
            self.assertIn(key, BNT_OUTPUT_FILES)
            self.assertIn(key, CCMA_OUTPUT_FILES)
            self.assertIn(key, CZECH_TELEVISION_OUTPUT_FILES)
            self.assertIn(key, DFF_OUTPUT_FILES)
            self.assertIn(key, DHM_OUTPUT_FILES)
            self.assertIn(key, EAFA_OUTPUT_FILES)
            self.assertIn(key, ECPAD_OUTPUT_FILES)
            self.assertIn(key, ERT_OUTPUT_FILES)
            self.assertIn(key, EYE_OUTPUT_FILES)
            self.assertIn(key, ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES)
            self.assertIn(key, FILMARCHIV_AUSTRIA_OUTPUT_FILES)
            self.assertIn(key, FILMMUSEUM_DUSSELDORF_OUTPUT_FILES)
            self.assertIn(key, DEUTSCHE_KINEMATHEK_OUTPUT_FILES)
            self.assertIn(key, DR_OUTPUT_FILES)
            self.assertIn(key, CICLIC_OUTPUT_FILES)
            self.assertIn(key, CINEAM_OUTPUT_FILES)
            self.assertIn(key, CINEMEMOIRE_OUTPUT_FILES)
            self.assertIn(key, CINEARCHIVES_OUTPUT_FILES)
            self.assertIn(key, CINEMATHEQUE_BRETAGNE_OUTPUT_FILES)
            self.assertIn(key, CRNOGORSKA_KINOTEKA_OUTPUT_FILES)
            self.assertIn(key, CNCAFF_OUTPUT_FILES)
            self.assertIn(key, CNA_OUTPUT_FILES)
            self.assertIn(key, LUCE_OUTPUT_FILES)
            self.assertIn(key, CINEMATECA_PT_OUTPUT_FILES)
            self.assertIn(key, FILMOTECA_VASCA_OUTPUT_FILES)

    def test_output_manifest_values_are_unique(self):
        filenames = list_ape_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_aapb_output_manifest_values_are_unique(self):
        filenames = list_aapb_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_archipop_output_manifest_values_are_unique(self):
        filenames = list_archipop_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_aamod_output_manifest_values_are_unique(self):
        filenames = list_aamod_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_sfa_output_manifest_values_are_unique(self):
        filenames = list_sfa_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_anf_output_manifest_values_are_unique(self):
        filenames = list_anf_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, APE_OUTPUT_FILES)

    def test_aapb_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, AAPB_OUTPUT_FILES)

    def test_archipop_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, ARCHIPOP_OUTPUT_FILES)

    def test_aamod_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, AAMOD_OUTPUT_FILES)

    def test_sfa_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, SFA_OUTPUT_FILES)

    def test_anf_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, ANF_OUTPUT_FILES)

    def test_ina_output_manifest_values_are_unique(self):
        filenames = list_ina_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_ina_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, INA_OUTPUT_FILES)

    def test_euscreen_output_manifest_values_are_unique(self):
        filenames = list_euscreen_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_euscreen_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EUSCREEN_OUTPUT_FILES)

    def test_pares_output_manifest_values_are_unique(self):
        filenames = list_pares_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_ppa_output_manifest_values_are_unique(self):
        filenames = list_ppa_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_european_film_gateway_output_manifest_values_are_unique(self):
        filenames = list_european_film_gateway_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_europeana_output_manifest_values_are_unique(self):
        filenames = list_europeana_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_iam_output_manifest_values_are_unique(self):
        filenames = list_iam_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_autrefois_output_manifest_values_are_unique(self):
        filenames = list_autrefois_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_barch_output_manifest_values_are_unique(self):
        filenames = list_barch_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_bbc_output_manifest_values_are_unique(self):
        filenames = list_bbc_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_bfi_output_manifest_values_are_unique(self):
        filenames = list_bfi_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_bnfa_output_manifest_values_are_unique(self):
        filenames = list_bnfa_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_bnt_output_manifest_values_are_unique(self):
        filenames = list_bnt_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_ccma_output_manifest_values_are_unique(self):
        filenames = list_ccma_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_czech_television_output_manifest_values_are_unique(self):
        filenames = list_czech_television_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_dff_output_manifest_values_are_unique(self):
        filenames = list_dff_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_dhm_output_manifest_values_are_unique(self):
        filenames = list_dhm_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_eafa_output_manifest_values_are_unique(self):
        filenames = list_eafa_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_ecpad_output_manifest_values_are_unique(self):
        filenames = list_ecpad_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_ert_output_manifest_values_are_unique(self):
        filenames = list_ert_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_deutsche_kinemathek_output_manifest_values_are_unique(self):
        filenames = list_deutsche_kinemathek_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_ciclic_output_manifest_values_are_unique(self):
        filenames = list_ciclic_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_cineam_output_manifest_values_are_unique(self):
        filenames = list_cineam_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_cinememoire_output_manifest_values_are_unique(self):
        filenames = list_cinememoire_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_cinearchives_output_manifest_values_are_unique(self):
        filenames = list_cinearchives_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_cinematheque_bretagne_output_manifest_values_are_unique(self):
        filenames = list_cinematheque_bretagne_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_crnogorska_kinoteka_output_manifest_values_are_unique(self):
        filenames = list_crnogorska_kinoteka_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_crnogorska_kinoteka_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CRNOGORSKA_KINOTEKA_OUTPUT_FILES)

    def test_cna_output_manifest_values_are_unique(self):
        filenames = list_cna_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_cnc_aff_output_manifest_values_are_unique(self):
        filenames = list_cnc_aff_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_luce_output_manifest_values_are_unique(self):
        filenames = list_luce_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_cinemateca_portuguesa_output_manifest_values_are_unique(self):
        filenames = list_cinemateca_portuguesa_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_filmoteca_vasca_output_manifest_values_are_unique(self):
        filenames = list_filmoteca_vasca_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_eye_output_manifest_values_are_unique(self):
        filenames = list_eye_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_estonian_film_archive_output_manifest_values_are_unique(self):
        filenames = list_estonian_film_archive_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_filmarchiv_austria_output_manifest_values_are_unique(self):
        filenames = list_filmarchiv_austria_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_filmmuseum_dusseldorf_output_manifest_values_are_unique(self):
        filenames = list_filmmuseum_dusseldorf_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_pares_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, PARES_OUTPUT_FILES)

    def test_ppa_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, PPA_OUTPUT_FILES)

    def test_european_film_gateway_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EUROPEAN_FILM_GATEWAY_OUTPUT_FILES)

    def test_europeana_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EUROPEANA_OUTPUT_FILES)

    def test_iam_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, IAM_OUTPUT_FILES)

    def test_autrefois_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, AUTREFOIS_OUTPUT_FILES)

    def test_bbc_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, BBC_OUTPUT_FILES)

    def test_barch_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, BARCH_OUTPUT_FILES)

    def test_bfi_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, BFI_OUTPUT_FILES)

    def test_bnfa_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, BNFA_OUTPUT_FILES)

    def test_bnt_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, BNT_OUTPUT_FILES)

    def test_ccma_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CCMA_OUTPUT_FILES)

    def test_czech_television_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CZECH_TELEVISION_OUTPUT_FILES)

    def test_dff_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, DFF_OUTPUT_FILES)

    def test_dhm_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, DHM_OUTPUT_FILES)

    def test_eafa_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EAFA_OUTPUT_FILES)

    def test_deutsche_kinemathek_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, DEUTSCHE_KINEMATHEK_OUTPUT_FILES)

    def test_ert_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, ERT_OUTPUT_FILES)

    def test_ciclic_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CICLIC_OUTPUT_FILES)

    def test_cineam_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CINEAM_OUTPUT_FILES)

    def test_cinememoire_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CINEMEMOIRE_OUTPUT_FILES)

    def test_cinearchives_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CINEARCHIVES_OUTPUT_FILES)

    def test_cinematheque_bretagne_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CINEMATHEQUE_BRETAGNE_OUTPUT_FILES)

    def test_cna_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CNA_OUTPUT_FILES)

    def test_cnc_aff_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CNCAFF_OUTPUT_FILES)

    def test_luce_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, LUCE_OUTPUT_FILES)

    def test_cinemateca_portuguesa_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, CINEMATECA_PT_OUTPUT_FILES)

    def test_filmoteca_vasca_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, FILMOTECA_VASCA_OUTPUT_FILES)

    def test_eye_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EYE_OUTPUT_FILES)

    def test_estonian_film_archive_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES)

    def test_filmarchiv_austria_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, FILMARCHIV_AUSTRIA_OUTPUT_FILES)

    def test_filmmuseum_dusseldorf_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, FILMMUSEUM_DUSSELDORF_OUTPUT_FILES)


if __name__ == "__main__":
    unittest.main()
