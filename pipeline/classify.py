"""행정처분을 위반 내용(VILTCN) 키워드로 분류한다.

hygiene : 위생 관련 (소비기한 경과, 이물, 유독물질, 수질검사 미실시 등) → 앱에서 위생 경고
conduct : 영업질서 위반 (청소년 주류, 유흥접객, 도박 등) → 위생과 무관, 표시 방식은 별도 결정
closed  : 철거·멸실·폐업·장기휴업에 따른 행정 정리 → 이미 없는 가게, 지도에서 제외
unknown : 규칙에 안 걸림 → 수집 때 개수를 출력해 사람이 보고 규칙 추가

검사 순서가 중요하다: '청소년 유해 약물(소주)'처럼 conduct 문장에 위생 단어가 섞이므로 conduct를 먼저 본다.
"""
RULES = (
    ("conduct", ("청소년", "주류", "유흥", "노래", "춤", "도박", "성매매", "처분 기간 중")),
    ("hygiene", ("소비기한", "유통기한", "이물", "유독", "유해물질", "수질검사", "부패", "변질", "곰팡이")),
    ("closed", ("철거", "멸실", "폐업", "휴업", "말소", "폐쇄", "시설없", "시설 없", "소재지 변경")),
)


def classify(row):
    text = row.get("VILTCN", "")
    for category, words in RULES:
        if any(w in text for w in words):
            return category
    return "unknown"
