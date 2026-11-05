import unittest

from fetch_violations import in_regions


class InRegionsTest(unittest.TestCase):
    def test_target_regions(self):
        for addr in ("부산광역시 해운대구 ...", "경상남도 창원시 ...", "경상북도 포항시 ..."):
            self.assertTrue(in_regions({"ADDR": addr}))

    def test_other_regions(self):
        for addr in ("서울특별시 동대문구 ...", "경기도 안산시 ...", ""):
            self.assertFalse(in_regions({"ADDR": addr}))
        self.assertFalse(in_regions({}))


if __name__ == "__main__":
    unittest.main()
