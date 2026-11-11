import unittest

from build_load_sql import build, copy_block
from classify import classify
from cuisine import cuisines
from fetch_hygiene_grades import is_active
from foodsafety import in_regions
from geocode import clean


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


class ClassifyTest(unittest.TestCase):
    CASES = {  # 실제 수집 데이터에서 가져온 문장
        "소비기한 경과제품을 조리 목적으로 보관(1차)": "hygiene",
        "지하수 수질검사 미실시(2차)": "hygiene",
        "유독유해물질이 들어 있거나 묻어 있는 것이나 그러할 염려가 있는 식품 조리판매(복어요리)": "hygiene",
        "조리음식 내 이물(바퀴벌레) 혼입 경로를 확인함.": "hygiene",
        "청소년인 장00(18세) 등 3명에세 연령을 확인하지 않고 청소년 유행 약물인 참이슬소주": "conduct",
        "단란주점 영업자 유흥접객원 고용 유흥접객행위(1차)": "conduct",
        "도박 장소 제공 및 도박 행위 묵인": "conduct",
        "영업정지 처분 기간 중에 영업을 한 경우": "conduct",
        "(20260914)영업시설의 전부를 철거한 경우": "closed",
        "정당한 사유 없이 6개월 이상 계속 휴업": "closed",
        "사업자등록 폐업(2025. 12. 31.자)": "closed",
        "시설없이 영업신고 한 경우": "closed",
        "식품위생법 제36조 영업소시설물 전부 철거": "closed",  # 법령명의 '위생'에 걸리면 안 됨
        "식품위생법 제 75조(허가취소 등)": "unknown",
        "": "unknown",
    }

    def test_cases(self):
        for text, expected in self.CASES.items():
            self.assertEqual(classify({"VILTCN": text}), expected, text)


class CuisinesTest(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(cuisines("홍콩반점0410 해운대점"), ["중식"])
        self.assertEqual(cuisines("교촌치킨 창원점"), ["치킨"])
        self.assertEqual(cuisines("BBQ 포항점"), ["치킨"])
        self.assertEqual(cuisines("도미노피자 김해점"), ["피자"])
        self.assertEqual(cuisines("가장맛있는족발"), ["족발보쌈"])
        self.assertEqual(cuisines("화성(상)휴게소(닭강정탕수육)"), ["중식", "치킨"])
        self.assertEqual(cuisines("스타벅스서동탄DT점"), [])
        self.assertEqual(cuisines("탕화쿵푸마라탕 대신점"), ["마라탕"])
        # 지점명 오탐 (실제 데이터)
        self.assertEqual(cuisines("스텔라떡볶이 경북경주용황점"), [])
        self.assertEqual(cuisines("60계 경북경주현곡점"), ["치킨"])
        self.assertEqual(cuisines("뚜레쥬르옥동호반점"), [])
        self.assertEqual(cuisines("이디야 부산차이나타운점"), [])


class CleanAddressTest(unittest.TestCase):
    def test_cases(self):  # 실제 수집 데이터의 주소 형태
        self.assertEqual(clean("경상남도 밀양시 하남읍 수산중앙로 97-1(1층)"), "경상남도 밀양시 하남읍 수산중앙로 97-1")
        self.assertEqual(clean("부산광역시 동래구 온천장로107번길 44(온천동,4층)"), "부산광역시 동래구 온천장로107번길 44")
        self.assertEqual(clean("경상북도 울진군 울진읍 울진중앙로 137"), "경상북도 울진군 울진읍 울진중앙로 137")
        self.assertEqual(clean("부산광역시 해운대구 센텀남대로 35, 1층 101호"), "부산광역시 해운대구 센텀남대로 35")


class BuildTest(unittest.TestCase):
    G = {"LCNS_NO": "1", "BSSH_NM": "교촌치킨 창원점", "ADDR": "경상남도 창원시 A로 1(1층)", "INDUTY_NM": "일반음식점",
         "HG_ASGN_NO": "제HG1호", "HG_ASGN_LV": "적합", "ASGN_FROM": "20250101", "ASGN_TO": "20270101", "HG_ASGN_NM": "식약처"}
    V = {"LCNS_NO": "1", "PRCSCITYPOINT_BSSHNM": "다른이름", "ADDR": "x", "INDUTY_CD_NM": "x", "DSPSDTLS_SEQ": "9",
         "DSPS_TYPECD_NM": "영업정지", "VILTCN": "소비기한 경과제품 보관", "LAWORD_CD_NM": "법", "DSPS_DCSNDT": "20260101",
         "PUBLIC_DT": "2026-12-08 00:00:00.0"}

    def test_build(self):
        closed = {**self.V, "LCNS_NO": "2", "DSPSDTLS_SEQ": "10", "VILTCN": "영업시설 전부 철거"}
        shops, grades, viols = build([self.G], [self.V, closed], {"경상남도 창원시 A로 1": [35.1, 128.6]})
        self.assertEqual(shops, [["1", "교촌치킨 창원점", "경상남도 창원시 A로 1(1층)", "일반음식점", "{치킨}", 35.1, 128.6]])
        self.assertEqual(grades[0][3:5], ["20250101", "20270101"])
        self.assertEqual([v[0] for v in viols], ["9"])  # 철거(closed)는 빠짐
        self.assertEqual(viols[0][2], "hygiene")
        self.assertEqual(viols[0][7], "2026-12-08")

    def test_no_coords(self):
        shops, _, _ = build([self.G], [], {})
        self.assertEqual(shops[0][5:], ["", ""])

    def test_copy_escapes(self):
        block = copy_block("t", ["a"], [['쉼표, "따옴표"\n줄바꿈']])
        self.assertIn('"쉼표, ""따옴표""\n줄바꿈"', block)  # 따옴표로 감싸져 한 값으로 유지
        self.assertTrue(block.endswith("\\.\n"))


if __name__ == "__main__":
    unittest.main()
