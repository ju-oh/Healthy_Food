"""적재된 로컬 DB로 API를 확인한다. DB가 꺼져 있으면 건너뛴다.

실행: python -m unittest discover -s api
"""
import unittest

import psycopg
from fastapi.testclient import TestClient

from main import DB_URL, app

try:
    psycopg.connect(DB_URL, connect_timeout=3).close()
    DB_UP = True
except psycopg.OperationalError:
    DB_UP = False

HAEUNDAE = {"lat": 35.1631, "lng": 129.1586}  # 해운대역


@unittest.skipUnless(DB_UP, "DB 꺼짐: docker compose up -d")
class ApiTest(unittest.TestCase):
    client = TestClient(app)

    def get(self, path, **params):
        res = self.client.get(path, params=params)
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()

    def test_nearby_sorted_within_radius(self):
        shops = self.get("/restaurants/nearby", **HAEUNDAE, radius=1000, cuisine="치킨")
        self.assertTrue(shops)
        dists = [s["distance_m"] for s in shops]
        self.assertEqual(dists, sorted(dists))
        self.assertLessEqual(dists[-1], 1000)
        self.assertTrue(all("치킨" in s["cuisines"] for s in shops))

    def test_search_then_detail(self):
        shops = self.get("/restaurants/search", q="bbq")  # 대소문자 무시
        self.assertTrue(shops)
        detail = self.get(f"/restaurants/{shops[0]['lcns_no']}")
        self.assertEqual(detail["name"], shops[0]["name"])
        self.assertIn("grades", detail)
        self.assertIn("violation_details", detail)

    def test_violation_shop_detail(self):
        with psycopg.connect(DB_URL) as conn:
            lcns = conn.execute("SELECT lcns_no FROM violations WHERE public_until >= current_date LIMIT 1").fetchone()
        if lcns:
            detail = self.get(f"/restaurants/{lcns[0]}")
            self.assertTrue(detail["violations"])
            self.assertTrue(detail["violation_details"])

    def test_bad_input(self):
        self.assertEqual(self.client.get("/restaurants/없는번호").status_code, 404)
        self.assertEqual(self.client.get("/restaurants/nearby", params={"lat": 999, "lng": 129}).status_code, 422)
        self.assertEqual(self.client.get("/restaurants/nearby", params={**HAEUNDAE, "radius": 99999}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
