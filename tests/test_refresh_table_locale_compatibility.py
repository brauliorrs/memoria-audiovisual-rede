import unittest

from memoria_audiovisual.locale_catalog import translate_key


class RefreshTableLocaleCompatibilityTest(unittest.TestCase):
    def test_legacy_refresh_labels_remain_stable_in_all_languages(self):
        expected = {
            "overview.table.column.incluida_na_ultima_rodada": "incluída na última rodada",
            "overview.table.column.situacao_na_ultima_rodada": "situação na última rodada",
            "overview.table.column.ultima_rodada_bem_sucedida": "última rodada bem-sucedida",
            "overview.table.column.ultima_observacao_registrada": "última observação registrada",
        }

        for language in ("pt", "en", "es"):
            for key, label in expected.items():
                with self.subTest(language=language, key=key):
                    self.assertEqual(translate_key(key, language), label)


if __name__ == "__main__":
    unittest.main()
