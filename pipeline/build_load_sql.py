"""수집·분류·지오코딩 결과를 합쳐 DB 적재용 data/load.sql을 만든다.

사용법:
  python pipeline/build_load_sql.py
  docker compose exec -T db psql -U postgres -d food -v ON_ERROR_STOP=1 < data/load.sql

파이썬 DB 드라이버 없이 psql의 COPY로 넣는다. 매번 테이블을 비우고 다시 넣으므로 여러 번 돌려도 된다.
"""
import csv
import io
import json

from classify import classify
from cuisine import cuisines
from foodsafety import DATA
from geocode import clean


def date(s):
    """'20250128' / '2026-12-08 00:00:00.0' → '20250128' / '2026-12-08'. 빈 값·'-'는 NULL."""
    s = (s or "").strip()
    return s[:10] if s and s != "-" else ""


def build(grades, violations, coords):
    """(restaurants, hygiene_grades, violations) 행 리스트."""
    shops = {}

    def add_shop(lcns, name, addr, industry):
        if lcns in shops:  # 위생등급 쪽 정보를 먼저 넣으므로 그걸 우선한다
            return
        lat, lng = coords.get(clean(addr)) or ("", "")
        shops[lcns] = [lcns, name, addr, industry, "{" + ",".join(cuisines(name)) + "}", lat, lng]

    grade_rows = []
    for g in grades:
        add_shop(g["LCNS_NO"], g["BSSH_NM"], g["ADDR"], g["INDUTY_NM"])
        grade_rows.append([g["HG_ASGN_NO"], g["LCNS_NO"], g["HG_ASGN_LV"],
                           date(g["ASGN_FROM"]), date(g["ASGN_TO"]), g["HG_ASGN_NM"]])

    violation_rows = []
    for v in violations:
        category = classify(v)
        if category == "closed":  # 이미 없는 가게는 적재하지 않는다
            continue
        add_shop(v["LCNS_NO"], v["PRCSCITYPOINT_BSSHNM"], v["ADDR"], v["INDUTY_CD_NM"])
        violation_rows.append([v["DSPSDTLS_SEQ"], v["LCNS_NO"], category, v["DSPS_TYPECD_NM"],
                               v["VILTCN"], v["LAWORD_CD_NM"], date(v["DSPS_DCSNDT"]), date(v["PUBLIC_DT"])])

    return list(shops.values()), grade_rows, violation_rows


def copy_block(table, columns, rows):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)  # 쉼표·따옴표·줄바꿈은 csv 모듈이 이스케이프
    return f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv);\n{buf.getvalue()}\\.\n"


def main():
    load = lambda name: json.loads((DATA / name).read_text(encoding="utf-8"))
    shops, grades, violations = build(load("hygiene_grades.json"), load("violations.json"), load("geocode_cache.json"))
    sql = (
        "BEGIN;\nTRUNCATE restaurants CASCADE;\n"
        + copy_block("restaurants", ["lcns_no", "name", "addr", "industry", "cuisines", "lat", "lng"], shops)
        + copy_block("hygiene_grades", ["asgn_no", "lcns_no", "level", "asgn_from", "asgn_to", "agency"], grades)
        + copy_block("violations", ["seq", "lcns_no", "category", "dsps_type", "content", "law", "decided", "public_until"], violations)
        + "UPDATE restaurants SET geog = ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography WHERE lat IS NOT NULL;\n"
        + "COMMIT;\n"
    )
    out = DATA / "load.sql"
    out.write_text(sql, encoding="utf-8")
    print(f"가게 {len(shops)} · 위생등급 {len(grades)} · 행정처분 {len(violations)} → {out}")
    print(f"좌표 없음 {sum(1 for s in shops if s[5] == '')}곳")


if __name__ == "__main__":
    main()
