"""위생지도 API. 앱의 지도·검색·상세 화면이 쓴다.

실행: docker compose up -d && uvicorn main:app --reload --app-dir api
문서: http://localhost:8000/docs
"""
import os

import psycopg
from fastapi import FastAPI, HTTPException, Query
from psycopg.rows import dict_row

DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/food")

app = FastAPI(title="위생지도 API")

# 지도 핀 상태에 필요한 것: 지금 유효한 위생등급이 있는지, 지금 공표 중인 처분 종류
SUMMARY = """
SELECT r.lcns_no, r.name, r.addr, r.cuisines, r.lat, r.lng,
  EXISTS (SELECT 1 FROM hygiene_grades g WHERE g.lcns_no = r.lcns_no AND g.asgn_to >= current_date) AS graded,
  ARRAY(SELECT DISTINCT v.category FROM violations v
        WHERE v.lcns_no = r.lcns_no AND v.public_until >= current_date) AS violations
"""


def query(sql, params):
    # shortcut: 요청마다 연결을 새로 연다. 실사용 트래픽이 생기면 psycopg_pool로 바꾼다
    with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
        return conn.execute(sql, params).fetchall()


@app.get("/restaurants/nearby")
def nearby(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius: int = Query(1000, ge=1, le=5000, description="미터"),
    cuisine: str | None = Query(None, description="치킨, 피자, 중식, 마라탕, 족발보쌈"),
    limit: int = Query(50, ge=1, le=200),
):
    """내 주변 가게, 가까운 순. 좌표 없는 가게는 빠진다."""
    return query(SUMMARY + """, round(ST_Distance(r.geog, here.p)) AS distance_m
        FROM restaurants r,
             (SELECT ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography AS p) here
        WHERE ST_DWithin(r.geog, here.p, %(radius)s)
          AND (%(cuisine)s::text IS NULL OR r.cuisines @> ARRAY[%(cuisine)s::text])
        ORDER BY distance_m LIMIT %(limit)s""", locals())


@app.get("/restaurants/search")
def search(
    q: str = Query(min_length=1, max_length=50, description="가게 이름 일부"),
    cuisine: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    """이름 검색. 위생등급 가게를 먼저 보여준다."""
    return query(SUMMARY + """
        FROM restaurants r
        WHERE strpos(lower(r.name), lower(%(q)s)) > 0
          AND (%(cuisine)s::text IS NULL OR r.cuisines @> ARRAY[%(cuisine)s::text])
        ORDER BY graded DESC, r.name LIMIT %(limit)s""", locals())


@app.get("/restaurants/{lcns_no}")
def detail(lcns_no: str):
    """가게 상세: 유효한 위생등급과 지금 공표 중인 처분만."""
    rows = query(SUMMARY + "FROM restaurants r WHERE r.lcns_no = %(lcns_no)s", locals())
    if not rows:
        raise HTTPException(404, "가게를 찾을 수 없습니다")
    shop = rows[0]
    shop["grades"] = query("""SELECT level, asgn_from, asgn_to, agency FROM hygiene_grades
        WHERE lcns_no = %(lcns_no)s AND asgn_to >= current_date ORDER BY asgn_to DESC""", locals())
    shop["violation_details"] = query("""SELECT category, dsps_type, content, law, decided, public_until
        FROM violations WHERE lcns_no = %(lcns_no)s AND public_until >= current_date
        ORDER BY decided DESC""", locals())
    return shop
