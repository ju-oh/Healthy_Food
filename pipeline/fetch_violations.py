"""식품안전나라 I2630(식품접객업 행정처분)을 받아 부산·경남·경북만 data/violations.json에 저장한다.

사용법: 프로젝트 루트 .env에 FOODSAFETY_API_KEY=발급키 를 넣고 python pipeline/fetch_violations.py
키가 없으면 sample 키로 동작한다(최대 5건).
"""
from foodsafety import fetch_all, in_regions, save


def main():
    total, rows = fetch_all("I2630", 1000)
    picked = [r for r in rows if in_regions(r)]
    out = save("violations.json", picked)
    print(f"전체 {total}건 중 {len(rows)}건 수집, 대상 지역 {len(picked)}건 → {out}")


if __name__ == "__main__":
    main()
