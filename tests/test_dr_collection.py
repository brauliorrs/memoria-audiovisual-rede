import unittest

from memoria_audiovisual.dr import parse_dr_list_payload


class DrCollectionTests(unittest.TestCase):
    def test_parse_dr_list_payload_keeps_audiovisual_items(self):
        payload = {
            "items": [
                {"id": "1", "type": "program", "title": "Programa"},
                {"id": "2", "type": "episode", "title": "Episódio"},
                {"id": "3", "type": "show", "title": "Série"},
                {"id": "4", "type": "link", "title": "Link"},
                {"type": "program", "title": "Sem id"},
            ]
        }

        items = parse_dr_list_payload(payload)

        self.assertEqual([item["id"] for item in items], ["1", "2", "3"])


if __name__ == "__main__":
    unittest.main()
