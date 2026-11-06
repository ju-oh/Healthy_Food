"""식품안전나라 Open API 공통: .env 키 로딩, 페이지 단위 전체 수집, 대상 지역 필터, JSON 저장."""
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REGIONS = ("부산광역시", "경상남도", "경상북도")

ENV_FILE = ROOT / ".env"
if ENV_FILE.exists():  # KEY=VALUE 줄만 읽는다. 이미 설정된 환경변수가 우선
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("FOODSAFETY_API_KEY", "sample")


def fetch_page(service, start, end):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{API_KEY}/{service}/json/{start}/{end}"
    with urllib.request.urlopen(url, timeout=30) as res:
        body = json.load(res)[service]
    code = body["RESULT"]["CODE"]
    if code == "INFO-200":  # 해당 데이터 없음
        return 0, []
    if code != "INFO-000":
        raise RuntimeError(f"{service} API 오류 {code}: {body['RESULT']['MSG']}")
    return int(body["total_count"]), body.get("row", [])


def fetch_all(service, page_size):
    """page_size는 서비스별 1회 호출 한도. sample 키는 5건만 준다."""
    if API_KEY == "sample":
        return fetch_page(service, 1, 5)
    total, rows = fetch_page(service, 1, page_size)
    for start in range(page_size + 1, total + 1, page_size):
        rows += fetch_page(service, start, start + page_size - 1)[1]
    return total, rows


def in_regions(row):
    return row.get("ADDR", "").startswith(REGIONS)


def save(name, rows):
    DATA.mkdir(exist_ok=True)
    out = DATA / name
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
