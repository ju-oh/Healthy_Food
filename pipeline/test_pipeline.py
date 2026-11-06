import unittest

from fetch_hygiene_grades import is_active
from foodsafety import in_regions


class InRegionsTest(unittest.TestCase):
    def test_target_regions(self):
        for addr in ("부산광역시 해운대구 ...", "경상남도 창원시 ...", "경상북도 포항시 ..."):
            self.assertTrue(in_regions({"ADDR": addr}))

    def test_other_regions(self):
        for addr in ("서울특별시 동대문구 ...", "경기도 안산시 ...", ""):
            self.assertFalse(in_regions({"ADDR": addr}))
        self.assertFalse(in_regions({}))


class IsActiveTest(unittest.TestCase):
    OK = {"ASGN_TO": "20271231", "ASGN_CANCEL_YMD": "", "CLSBIZ_DVS_CD_NM": "정상"}

    def test_active(self):
        self.assertTrue(is_active(self.OK, "20261106"))
        self.assertTrue(is_active({**self.OK, "ASGN_TO": "20261106"}, "20261106"))  # 만료 당일까지 유효

    def test_inactive(self):
        self.assertFalse(is_active({**self.OK, "ASGN_TO": "20261105"}, "20261106"))
        self.assertFalse(is_active({**self.OK, "ASGN_CANCEL_YMD": "20260101"}, "20261106"))
        self.assertFalse(is_active({**self.OK, "CLSBIZ_DVS_CD_NM": "폐업"}, "20261106"))
        self.assertFalse(is_active({}, "20261106"))


if __name__ == "__main__":
    unittest.main()
