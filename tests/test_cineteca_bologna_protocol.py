import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.cineteca_bologna_protocol import (
    CINETECA_BOLOGNA_PROTOCOL_FILENAME,
    build_cineteca_bologna_non_incorporated_register,
    build_cineteca_bologna_protocol_probe,
    write_cineteca_bologna_protocol_probe,
)
from memoria_audiovisual.europe_closure import (
    CINETECA_BOLOGNA_NON_INCORPORATION_CATEGORY,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
)


def fake_fetcher(probe):
    if probe.probe == "archives_overview":
        text = "Archivio Film si compone di oltre 90.000 elementi. Consultazione su richiesta."
    elif probe.probe == "audiovisual_archive":
        text = "Archivio audiovisivi. Catalogo Film. Catalogo Registi."
    elif probe.probe == "catalog_ajax_page_1":
        text = (
            '{"items":"<article><a href=\\"/archivi/archivio/archivio-audiovisivi/catalogo-film/film/?film=1\\">'
            '<p><span>Titolo italiano:</span>Test</p></a></article>",'
            '"navigation":{"current_page":1,"total_pages":3290}}'
        )
    elif probe.probe == "catalog_detail_sample":
        text = "Film Catalogo Film Test Copia 1 Durata 90 Formato DVD"
    elif probe.probe == "wp_rest_types":
        text = '{"code":"rest_not_logged_in","data":{"status":401}}'
        return {
            "http_status": 401,
            "final_url": probe.url,
            "content_type": "application/json",
            "content_length": "",
            "text": text,
            "error": "",
        }
    elif probe.probe == "youtube_channel":
        text = "YouTube CinetecaBologna"
    else:
        text = "Cineteca di Bologna"
    return {
        "http_status": 200,
        "final_url": probe.url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class CinetecaBolognaProtocolTests(unittest.TestCase):
    def test_build_protocol_validates_catalog_but_not_active_ingestion(self):
        protocol_df = build_cineteca_bologna_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-17T00:00:00Z",
        )

        conclusions = protocol_df["protocol_conclusion"].tolist()
        ajax_observed = protocol_df.loc[
            protocol_df["probe"].eq("catalog_ajax_page_1"),
            "observed_value",
        ].iloc[0]
        self.assertEqual(len(protocol_df), 8)
        self.assertIn("acervo_filmico_confirmado_com_consulta_por_pedido", conclusions)
        self.assertIn("arquivo_audiovisual_confirma_catalogo_publico", conclusions)
        self.assertIn("catalogo_ajax_publico_extenso_validado_sem_bulk_export", conclusions)
        self.assertIn("ficha_publica_de_metadados_sem_player_detectado", conclusions)
        self.assertIn("wp_rest_nao_publico_para_coleta_eficiente", conclusions)
        self.assertIn("links_detalhe=1", ajax_observed)

    def test_build_non_incorporated_register_explains_pending_total_ingestion(self):
        protocol_df = build_cineteca_bologna_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-17T00:00:00Z",
        )
        excluded_df = build_cineteca_bologna_non_incorporated_register(protocol_df)

        row = excluded_df.iloc[0]
        self.assertEqual(row["unit_code"], "fiaf-cineteca-bologna")
        self.assertEqual(row["access_category"], CINETECA_BOLOGNA_NON_INCORPORATION_CATEGORY)
        self.assertIn("não incluída", row["public_status"])
        self.assertIn("3.290 páginas", row["negative_reason"])
        self.assertIn("A negativa é operacional", row["methodological_explanation"])
        self.assertFalse(bool(row["blocks_expansion"]))

    def test_write_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archivegrid", "unit_label": "ArchiveGrid"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_cineteca_bologna_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / CINETECA_BOLOGNA_PROTOCOL_FILENAME).exists())
            self.assertIn("fiaf-cineteca-bologna", excluded_df["unit_code"].tolist())
            self.assertIn("archivegrid", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
