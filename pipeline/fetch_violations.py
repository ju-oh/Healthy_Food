"""식품안전나라 I2630(식품접객업 행정처분)을 받아 부산·경남·경북만 data/violations.json에 저장한다.

사용법: 프로젝트 루트 .env에 FOODSAFETY_API_KEY=발급키 를 넣고 python pipeline/fetch_violations.py
키가 없으면 sample 키로 동작한다(최대 5건).
"""
import json
import os
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if ENV_FILE.exists():  # KEY=VALUE 줄만 읽는다. 이미 설정된 환경변수가 우선
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("FOODSAFETY_API_KEY", "sample")
SERVICE = "I2630"
PAGE = 5 if API_KEY == "sample" else 1000  # API 1회 최대 1000건
REGIONS = ("부산광역시", "경상남도", "경상북도")
OUT = Path(__file__).resolve().parent.parent / "data" / "violations.json"


def fetch_page(start, end):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{API_KEY}/{SERVICE}/json/{start}/{end}"
    with urllib.request.urlopen(url, timeout=30) as res:
        body = json.load(res)[SERVICE]
    code = body["RESULT"]["CODE"]
    if code == "INFO-200":  # 해당 데이터 없음
        return 0, []
    if code != "INFO-000":
        raise RuntimeError(f"API 오류 {code}: {body['RESULT']['MSG']}")
    return int(body["total_count"]), body.get("row", [])


def in_regions(row):
    return row.get("ADDR", "").startswith(REGIONS)


def main():
    total, rows = fetch_page(1, PAGE)
    if API_KEY != "sample":
        for start in range(PAGE + 1, total + 1, PAGE):
            rows += fetch_page(start, start + PAGE - 1)[1]
    picked = [r for r in rows if in_regions(r)]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(picked, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"전체 {total}건 중 {len(rows)}건 수집, 대상 지역 {len(picked)}건 → {OUT}")


if __name__ == "__main__":
    main()
