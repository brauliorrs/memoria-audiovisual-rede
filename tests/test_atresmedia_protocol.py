import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.atresmedia_protocol import (
    ATRESMEDIA_ACCESS_CATEGORY,
    ATRESMEDIA_PROTOCOL_FILENAME,
    build_atresmedia_non_incorporated_register,
    build_atresmedia_protocol_probe,
    write_atresmedia_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


def fake_fetcher(url, method="GET"):
    if method == "BUNDLE":
        return {
            "http_status": 200,
            "final_url": "https://portalventas.atresmedia.com/main.js",
            "content_type": "application/javascript",
            "content_length": "",
            "text": (
                "Archivo de ATRESMEDIA audiovisual desde noviembre de 1989. "
                "Compra, presupuesto, contrato, licencia, marca de agua y baja resolución. "
                "oidc accessToken isAuthenticated portalventas-identity apiportalventas "
                "'Solicitud/GetFicheros' 'Solicitud/GetSolicitud' 'carrito/getCarritoUsuario'"
            ),
            "error": "",
        }
    if "GetFormulario" in url or "GetFicheros" in url:
        return {
            "http_status": 401,
            "final_url": url,
            "content_type": "",
            "content_length": "",
            "text": "",
            "error": "",
        }
    if "GetVersiones" in url:
        return {
            "http_status": 200,
            "final_url": url,
            "content_type": "application/json",
            "content_length": "",
            "text": '[{"idVersion":"1.0.2"}]',
            "error": "",
        }
    if "fiatifta" in url and "awards" not in url:
        text = "FIAT/IFTA Full Members. ATRESMEDIA. television audiovisual archives."
    elif "awards" in url:
        text = "AI Algorithms for Media Cataloguing in ATRESMEDIA Archive. Video materials in television archives."
    elif "portalventas" in url:
        text = "<html><title>PortalImagenesWeb</title><body><app-root></app-root></body></html>"
    elif "atresplayer" in url:
        text = "Atresplayer plataforma audiovisual de Atresmedia."
    else:
        text = "Atresmedia audiovisual Antena 3 laSexta atresplayer."
    return {
        "http_status": 200,
        "final_url": url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class AtresmediaProtocolTests(unittest.TestCase):
    def test_build_atresmedia_protocol_documents_restricted_commercial_archive(self):
        protocol_df = build_atresmedia_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-06-11T00:00:00Z")

        self.assertEqual(len(protocol_df), 9)
        self.assertIn("membro_fiat_ifta_confirmado", protocol_df["protocol_conclusion"].tolist())
        self.assertIn(
            "arquivo_audiovisual_confirmado_sem_catalogo_publico",
            protocol_df["protocol_conclusion"].tolist(),
        )
        self.assertIn(
            "portal_de_arquivo_com_fluxo_comercial_autenticado",
            protocol_df["protocol_conclusion"].tolist(),
        )
        self.assertEqual(
            int((protocol_df["protocol_conclusion"] == "api_do_portal_requer_autenticacao").sum()),
            2,
        )

    def test_build_atresmedia_non_incorporated_register_explains_access_restriction(self):
        protocol_df = build_atresmedia_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-06-11T00:00:00Z")
        excluded_df = build_atresmedia_non_incorporated_register(protocol_df)

        self.assertEqual(excluded_df.iloc[0]["unit_code"], "fiat-atresmedia")
        self.assertEqual(excluded_df.iloc[0]["access_category"], ATRESMEDIA_ACCESS_CATEGORY)
        self.assertIn("não incluído", excluded_df.iloc[0]["public_status"])
        self.assertIn("banco privado de imagens", excluded_df.iloc[0]["negative_reason"])
        self.assertIn("licenciamento pago", excluded_df.iloc[0]["negative_reason"])
        self.assertIn("acesso restrito e monetizado", excluded_df.iloc[0]["methodological_explanation"])
        self.assertFalse(bool(excluded_df.iloc[0]["blocks_expansion"]))

    def test_write_atresmedia_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archives-hub", "unit_label": "Archives Hub"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_atresmedia_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / ATRESMEDIA_PROTOCOL_FILENAME).exists())
            self.assertIn("fiat-atresmedia", excluded_df["unit_code"].tolist())
            self.assertIn("archives-hub", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
