"""식품안전나라 C004(식품접객업소 위생등급 지정 현황)를 받아
부산·경남·경북의 현재 유효한 지정만 data/hygiene_grades.json에 저장한다.

사용법: python pipeline/fetch_hygiene_grades.py  (.env의 FOODSAFETY_API_KEY 사용)
"""
from datetime import date

from foodsafety import fetch_all, in_regions, save


def is_active(row, today):
    """만료·취소·폐업된 지정은 '지금 깨끗하다'는 근거가 아니므로 뺀다. today는 YYYYMMDD."""
    return (
        row.get("ASGN_TO", "") >= today
        and not row.get("ASGN_CANCEL_YMD")
        and row.get("CLSBIZ_DVS_CD_NM") == "정상"
    )


def main():
    today = date.today().strftime("%Y%m%d")
    total, rows = fetch_all("C004", 500)
    picked = [r for r in rows if in_regions(r) and is_active(r, today)]
    out = save("hygiene_grades.json", picked)
    print(f"전체 {total}건 중 {len(rows)}건 수집, 대상 지역 유효 지정 {len(picked)}건 → {out}")


if __name__ == "__main__":
    main()
