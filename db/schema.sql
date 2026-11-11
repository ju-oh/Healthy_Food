CREATE EXTENSION IF NOT EXISTS postgis;

-- 가게: 위생등급 업소 + (이미 없어진 가게를 뺀) 행정처분 업소. 인허가번호로 식별
CREATE TABLE IF NOT EXISTS restaurants (
    lcns_no   text PRIMARY KEY,
    name      text NOT NULL,
    addr      text NOT NULL,
    industry  text,
    cuisines  text[] NOT NULL DEFAULT '{}',  -- 이름으로 추정한 배달 종목 (치킨, 중식 ...)
    lat       double precision,              -- 지오코딩 실패 시 NULL (지도에서 제외)
    lng       double precision,
    geog      geography(Point, 4326)         -- lat/lng로 적재 후 채움. "내 주변 N km" 검색용
);
CREATE INDEX IF NOT EXISTS restaurants_geog_idx ON restaurants USING gist (geog);
CREATE INDEX IF NOT EXISTS restaurants_cuisines_idx ON restaurants USING gin (cuisines);

-- 위생등급 지정 (유효한 것만 적재)
CREATE TABLE IF NOT EXISTS hygiene_grades (
    asgn_no    text PRIMARY KEY,
    lcns_no    text NOT NULL REFERENCES restaurants ON DELETE CASCADE,
    level      text NOT NULL,   -- 현재 데이터는 전부 '적합'
    asgn_from  date,
    asgn_to    date,
    agency     text
);

-- 행정처분 (category: hygiene / conduct / unknown. closed는 적재하지 않음)
CREATE TABLE IF NOT EXISTS violations (
    seq           text PRIMARY KEY,
    lcns_no       text NOT NULL REFERENCES restaurants ON DELETE CASCADE,
    category      text NOT NULL,
    dsps_type     text,          -- 영업정지, 영업소폐쇄 ...
    content       text,          -- 위반 내용
    law           text,          -- 근거 법령
    decided       date,
    public_until  date           -- 공표 종료일. 지나면 앱에서 숨긴다
);
