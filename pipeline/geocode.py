"""수집한 가게 주소를 카카오 로컬 API로 좌표(위도·경도)로 바꿔 data/geocode_cache.json에 저장한다.

사용법: .env에 KAKAO_REST_API_KEY=키 를 넣고 python pipeline/geocode.py
캐시에 있는 주소는 다시 부르지 않으므로, 여러 번 돌려도 새 주소만 호출한다.
대상: 위생등급 업소 전부 + 행정처분 중 closed(이미 없는 가게)가 아닌 것.
"""
import json
import os
import re
import urllib.parse
import urllib.request

from classify import classify
from foodsafety import DATA

CACHE = DATA / "geocode_cache.json"
URL = "https://dapi.kakao.com/v2/local/search/address.json?query="


def clean(addr):
    """'수산중앙로 97-1(1층)' → '수산중앙로 97-1'. 괄호 속 층·동 정보와 쉼표 뒤 상세주소는 검색을 방해한다."""
    return re.sub(r"\(.*?\)", "", addr).split(",")[0].strip()


def lookup(addr, key):
    """좌표 [위도, 경도]. 카카오가 못 찾으면 None."""
    req = urllib.request.Request(URL + urllib.parse.quote(addr), headers={"Authorization": f"KakaoAK {key}"})
    with urllib.request.urlopen(req, timeout=10) as res:
        docs = json.load(res)["documents"]
    return [float(docs[0]["y"]), float(docs[0]["x"])] if docs else None


def targets():
    grades = json.loads((DATA / "hygiene_grades.json").read_text(encoding="utf-8"))
    violations = json.loads((DATA / "violations.json").read_text(encoding="utf-8"))
    rows = grades + [v for v in violations if classify(v) != "closed"]  # 저장된 파일에 CATEGORY가 없을 수도 있어 다시 분류
    return sorted({clean(r["ADDR"]) for r in rows if r.get("ADDR")})


def main():
    key = os.environ.get("KAKAO_REST_API_KEY")
    if not key:
        raise SystemExit(".env에 KAKAO_REST_API_KEY가 없습니다.")
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = [a for a in targets() if a not in cache]
    print(f"대상 주소 {len(todo) + len(cache)}개 중 새로 변환할 것 {len(todo)}개", flush=True)
    try:
        for i, addr in enumerate(todo, 1):
            cache[addr] = lookup(addr, key)
            if i % 500 == 0:
                print(f"  {i}/{len(todo)}", flush=True)
    finally:  # 중간에 끊겨도 받은 만큼은 저장해서 다음 실행 때 이어서 한다
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    failed = [a for a, v in cache.items() if v is None]
    print(f"완료: 성공 {len(cache) - len(failed)}, 실패 {len(failed)} → {CACHE}")
    for a in failed[:20]:
        print("  못 찾음:", a)


if __name__ == "__main__":
    main()
