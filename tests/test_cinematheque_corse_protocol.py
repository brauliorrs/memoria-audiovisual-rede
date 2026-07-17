import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.cinematheque_corse_protocol import (
    CINEMATHEQUE_CORSE_ACCESS_CATEGORY,
    CINEMATHEQUE_CORSE_PROTOCOL_FILENAME,
    build_cinematheque_corse_non_incorporated_register,
    build_cinematheque_corse_protocol_probe,
    write_cinematheque_corse_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


def fake_fetcher(url, method="GET"):
    if "casadilume.corse.fr" in url:
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "content_length": "",
            "text": "",
            "error": "NameResolutionError",
        }
    if "Consulter-les-Collections" in url:
        text = (
            "Cinémathèque de Corse Casa di Lume. La consultation des collections est accessible sur rendez-vous. "
            "Le catalogue en ligne donne accès aux collections Non Film, affiches et photographies, sur "
            "cineressources.net. Fonds du dépôt légal INA et CNC. Accès sur inscription et formulaire de demande "
            "d'accréditation."
        )
    elif "Cine-Ressources" in url:
        text = "Ciné-Ressources présente les collections Non Film, affiches et photographies."
    elif "Le-Patrimoine" in url:
        text = "Cinémathèque de Corse patrimoine archives film conservation restauration cinéma."
    elif "search" in url:
        text = "Recherche avancée du site institutionnel."
    elif "MEDIAS" in url:
        text = "MEDIAS actualités de la Cinémathèque de Corse."
    elif "youtube" in url:
        text = "YouTube channel Casa di Lume consent.youtube vidéos de communication."
    else:
        text = "Cinémathèque de Corse Casa di Lume patrimoine cinéma collections."
    return {
        "http_status": 200,
        "final_url": url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class CinemathequeCorseProtocolTests(unittest.TestCase):
    def test_build_protocol_documents_archive_without_public_video_catalog(self):
        protocol_df = build_cinematheque_corse_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-06-19T00:00:00Z",
        )

        conclusions = protocol_df["protocol_conclusion"].tolist()
        self.assertEqual(len(protocol_df), 8)
        self.assertIn("dominio_antigo_da_fila_indisponivel", conclusions)
        self.assertIn("colecoes_audiovisuais_sem_catalogo_publico_de_video", conclusions)
        self.assertIn("catalogo_online_restrito_a_non_film", conclusions)
        self.assertIn("arquivo_audiovisual_confirmado_sem_rota_publica_de_video", conclusions)

    def test_build_non_incorporated_register_explains_methodological_negative(self):
        protocol_df = build_cinematheque_corse_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-06-19T00:00:00Z",
        )
        excluded_df = build_cinematheque_corse_non_incorporated_register(protocol_df)

        row = excluded_df.iloc[0]
        self.assertEqual(row["unit_code"], "inedits-cinematheque-corse")
        self.assertEqual(row["access_category"], CINEMATHEQUE_CORSE_ACCESS_CATEGORY)
        self.assertIn("não incluído", row["public_status"])
        self.assertIn("Non Film", row["negative_reason"])
        self.assertIn("não nega a existência", row["methodological_explanation"])
        self.assertFalse(bool(row["blocks_expansion"]))

    def test_write_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archivegrid", "unit_label": "ArchiveGrid"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_cinematheque_corse_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / CINEMATHEQUE_CORSE_PROTOCOL_FILENAME).exists())
            self.assertIn("inedits-cinematheque-corse", excluded_df["unit_code"].tolist())
            self.assertIn("archivegrid", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
