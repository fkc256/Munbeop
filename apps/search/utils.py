"""검색용 키워드 추출 유틸 (3차 — 단순 토큰화 + 조사 stripping).

⚠️ 4차 업그레이드 시 교체 포인트:
이 모듈 전체를 ``generate_embedding(text) -> vector`` 로 대체할 예정.
지금은 함수 인터페이스만 잘 잡아두고 단순 구현으로 동작 확인.
"""
import re

# 흔한 한국어 조사 — 길이 2짜리 우선, 그다음 1짜리
PARTICLES_2 = ("에서", "으로", "까지", "부터", "에게", "한테", "보다")
PARTICLES_1 = (
    "이", "가", "은", "는", "을", "를", "의", "에",
    "도", "만", "와", "과", "로",
)

KOREAN_STOPWORDS = {
    # 접속사/지시어
    "그리고", "그런데", "하지만", "그래서", "그러면", "그러나", "그리하여",
    # 존재/부재
    "있는", "있어요", "있습니다", "있다", "없는", "없어요", "없습니다", "없다",
    # 동사 마무리/조동사 (자주 나오는 종결형)
    "하는", "하고", "해서", "하면", "한다", "합니다", "했어요", "했습니다",
    "받고", "받아요", "받습니다", "받았어요", "받았습니다",
    "되는", "되어", "되어요", "됩니다", "되었습니다",
    "입니다", "이에요", "예요", "아니에요",
    # 인칭/호칭
    "저는", "제가", "나는", "내가", "저의", "나의",
    # 시간 부사
    "오늘", "어제", "내일", "지금", "방금",
    # 정도 부사
    "정말", "진짜", "너무", "아주", "매우", "조금", "약간",
    # 비교/지시
    "같은", "같이", "같아요", "이런", "그런", "저런",
    # 의문사
    "어떻게", "어떤", "무엇", "뭐", "왜", "언제", "어디",
    # 자주 등장하는 의미 약한 명사
    "경우", "사람", "것이", "것을", "것은", "거에", "거에요",
}


def strip_particle(token: str) -> str:
    """토큰 끝의 흔한 조사를 제거. 너무 짧으면 그대로 반환."""
    if len(token) < 3:
        return token
    for p in PARTICLES_2:
        if token.endswith(p) and len(token) - len(p) >= 2:
            return token[: -len(p)]
    for p in PARTICLES_1:
        if token.endswith(p) and len(token) - 1 >= 2:
            return token[:-1]
    return token


_TOKEN_SPLIT_RE = re.compile(r"[\s,.;:!?()\[\]{}\"'·…~`/\\\-_=+*&%$#@<>]+")


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    """자연어 텍스트 → 검색 키워드 리스트.

    흐름: 토큰 분할 → 조사 stripping → 2글자 이상 필터 → 불용어 제거 → 중복 제거 → 상한.
    """
    if not text:
        return []
    raw_tokens = [t for t in _TOKEN_SPLIT_RE.split(text.strip()) if t]
    seen: set[str] = set()
    out: list[str] = []
    for raw in raw_tokens:
        token = strip_particle(raw)
        if len(token) < 2:
            continue
        if token in KOREAN_STOPWORDS:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(token)
        if len(out) >= max_keywords:
            break
    return out
