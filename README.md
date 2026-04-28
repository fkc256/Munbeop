# 문법 (Munbeop)

일반인을 위한 법률 정보 검색 & 사례 학습 플랫폼 (부트캠프 3차 단계)

## 단계별 범위

- **3차 (현재, 4/27 ~ 5/6)**: 동작하는 웹서비스 MVP. AI 없음. 키워드 검색만.
- **4차 (예정, 5/8 ~ 6/16)**: AI 임베딩, FastAPI 분리, Celery + Redis, Docker, 모니터링.

3차에서는 의도적으로 다음을 추가하지 않습니다: AI/벡터DB, Docker, Celery, Redis, FastAPI 분리, PostgreSQL 전환.

## 기술 스택

- Python 3.11+
- Django 5.x + Django REST Framework
- djangorestframework-simplejwt (JWT 인증)
- SQLite (3차) → PostgreSQL (4차에서 전환)
- Django Template + Bootstrap 5 + vanilla JS (3차 후반에 적용 예정)
- python-decouple (.env 관리)

## 설치 및 실행

```bash
# 1. 클론
git clone https://github.com/fkc256/Munbeop.git
cd Munbeop

# 2. 가상환경
python3 -m venv .venv
source .venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 — SECRET_KEY는 본인 환경에 맞게 변경
cp .env.example .env
# (필요 시) SECRET_KEY 새로 발급:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 5. 마이그레이션
python manage.py migrate

# 6. 카테고리 초기 데이터 (재실행 안전)
python manage.py load_categories

# 6-1. 법령/판례 시연용 최소 데이터 (재실행 안전)
python manage.py load_sample_data

# 7. (선택) 관리자 계정
python manage.py createsuperuser

# 8. 서버 실행
python manage.py runserver
```

`http://localhost:8000/admin/` — Django 관리자 페이지.

## API 엔드포인트 (현재까지)

| Method | Path                              | 설명                       | 인증     |
| ------ | --------------------------------- | -------------------------- | -------- |
| POST   | `/api/accounts/signup/`           | 회원가입                   | -        |
| POST   | `/api/accounts/login/`            | 로그인 (access/refresh 발급) | -        |
| POST   | `/api/accounts/login/refresh/`    | access 토큰 재발급         | refresh  |
| POST   | `/api/accounts/logout/`           | 로그아웃 (refresh 블랙리스트) | access   |
| GET    | `/api/accounts/me/`               | 내 정보 조회               | access   |
| GET    | `/api/categories/`                | 카테고리 목록              | -        |
| GET    | `/api/stories/`                   | 사연 목록 (페이지네이션)   | -        |
| POST   | `/api/stories/`                   | 사연 작성                  | access   |
| GET    | `/api/stories/{id}/`              | 사연 상세 (view_count++)   | -        |
| PATCH  | `/api/stories/{id}/`              | 사연 수정 (작성자만)       | access   |
| DELETE | `/api/stories/{id}/`              | 사연 삭제 (soft, 작성자만) | access   |
| GET    | `/api/laws/`                      | 법령 목록                  | -        |
| GET    | `/api/laws/{id}/`                 | 법령 상세 (관련 판례 5건)  | -        |
| GET    | `/api/precedents/`                | 판례 목록                  | -        |
| GET    | `/api/precedents/{id}/`           | 판례 상세 (관련 법령 M2M)  | -        |
| POST   | `/api/search/`                    | 통합 검색 (법령+판례+사연) | -        |
| GET    | `/api/search/`                    | 통합 검색 (URL 공유용)     | -        |
| GET    | `/api/stories/{id}/comments/`     | 댓글 목록 (대댓글 nested)  | -        |
| POST   | `/api/stories/{id}/comments/`     | 댓글/대댓글 작성           | access   |
| PATCH  | `/api/comments/{id}/`             | 댓글 수정 (작성자만)       | access   |
| DELETE | `/api/comments/{id}/`             | 댓글 삭제 (soft, 작성자만) | access   |
| POST   | `/api/likes/toggle/`              | 좋아요 토글                | access   |
| POST   | `/api/bookmarks/toggle/`          | 북마크 토글                | access   |
| GET    | `/api/bookmarks/`                 | 내 북마크 목록 (필터 지원) | access   |

법령/판례 쿼리 파라미터:
- `?category=housing` — 카테고리 slug
- `?keyword=보증금` — 법령은 law_name/keywords/content, 판례는 case_name/keywords/summary 부분 일치
- `?court=대법원` — 판례 법원 정확 일치 (줄임 표기 매칭 X. 정규화는 4차에서 처리)
- `?result_type=plaintiff_win` — 판례 결과 (plaintiff_win/plaintiff_partial/defendant_win/settled/etc)
- `?ordering=-judgment_date` — 판례 기본 정렬, `?ordering=law_name`도 가능

쿼리 파라미터 (사연 목록):
- `?category=housing` — 카테고리 slug 필터 (housing/labor/consumer/family/traffic/criminal/realestate/debt/etc)
- `?ordering=-created_at` (기본) / `?ordering=-view_count`
- `?page=2` — 페이지네이션 (기본 page_size=10)
- `?page_size=20` — 페이지 크기 조정 (최대 50, 초과 시 50으로 자동 제한)

## API 사용 예시

### 회원가입

```bash
curl -X POST http://localhost:8000/api/accounts/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@test.com",
    "password": "testpass1234",
    "password2": "testpass1234",
    "nickname": "테스트"
  }'
```

### 로그인 → 토큰 받기

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass1234"}'
# 응답: {"access": "...", "refresh": "..."}
```

### 인증된 요청 (`/me/`)

```bash
curl -X GET http://localhost:8000/api/accounts/me/ \
  -H "Authorization: Bearer <access_token>"
```

### 로그아웃

```bash
curl -X POST http://localhost:8000/api/accounts/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

### 카테고리 목록

```bash
curl http://localhost:8000/api/categories/
```

### 사연 작성

```bash
curl -X POST http://localhost:8000/api/stories/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "전세 보증금 못 받고 있어요",
    "content": "집주인이 보증금 반환을 미루고 있습니다.",
    "category": 1,
    "is_anonymous": false
  }'
```

### 통합 검색 (사연 한 줄 입력 → 법령 + 판례 + 유사 사연)

```bash
# POST 버전 (자연어 입력)
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"전세 보증금을 못 받고 있어요","category":"housing"}'

# GET 버전 (URL 공유용)
curl -G --data-urlencode "q=부당해고" http://localhost:8000/api/search/
```

요청 파라미터:
- `query` (POST) / `q` (GET) — 자연어 입력
- `category` — 카테고리 slug 필터 (선택)
- `exclude_story_id` — 사연 상세 페이지에서 자기 사연 제외용 (선택)

응답 구조:
- `extracted_keywords` — 입력에서 추출한 키워드 (조사 stripping + 불용어 제거 적용)
- `results.laws` (Top 5) / `results.precedents` (Top 10) / `results.stories` (Top 5)
- 각 결과 항목에 `matched_keywords`(매칭된 키워드 리스트)와 `score`(매칭 키워드 개수) 포함
- `disclaimer` — 법률 자문이 아니라는 면책 고지 (모든 응답에 포함)

⚠️ **검색 알고리즘 4차 업그레이드 계획**: 현재는 키워드 기반 ILIKE 매칭이며,
4차에서 임베딩 기반 유사도 검색으로 업그레이드 예정. `apps/search/utils.py`의
`extract_keywords` 와 `apps/search/services.py`의 `search_*` 함수가 교체 포인트.

### 댓글 / 좋아요 / 북마크

```bash
# 댓글 작성 (인증 필요)
curl -X POST http://localhost:8000/api/stories/1/comments/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"content":"공감합니다"}'

# 대댓글 작성 (parent 지정 — 1단계만 허용)
curl -X POST http://localhost:8000/api/stories/1/comments/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"content":"답변 감사","parent":1}'

# 좋아요 토글 (story 또는 comment)
curl -X POST http://localhost:8000/api/likes/toggle/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"target_type":"story","target_id":1}'
# 응답: {"liked": true, "count": 1}

# 북마크 토글 (story / law / precedent)
curl -X POST http://localhost:8000/api/bookmarks/toggle/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"target_type":"law","target_id":1}'

# 내 북마크 목록 (필터)
curl -H "Authorization: Bearer <access>" \
  "http://localhost:8000/api/bookmarks/?target_type=law"
```

**대댓글 정책**: 댓글에는 1단계 대댓글까지만 허용됩니다. 대댓글에 다시 대댓글을 달면 400을 반환합니다.

**삭제된 댓글 표시**: 작성자가 자기 댓글을 삭제(soft) 했을 때, 그 아래 활성 대댓글이 있으면 부모 자리에 "삭제된 댓글입니다" placeholder를 보여주고 대댓글은 그대로 노출합니다. 활성 대댓글이 없으면 부모는 목록에서 사라집니다.

**Story/Law/Precedent 응답 추가 필드**: 인증 사용자가 호출하면 `is_liked`, `is_bookmarked`, `like_count`, `comment_count` 가 포함됩니다 (Story 한정 — Law/Precedent 상세는 `is_bookmarked`만). 비인증 호출 시 `is_*` 필드는 항상 `false`.

### 사연 목록 (필터/정렬/페이지네이션)

```bash
# 기본 (page_size=10)
curl http://localhost:8000/api/stories/

# page_size 조정 — 1페이지에 20건
curl "http://localhost:8000/api/stories/?page=1&page_size=20"

# max_page_size(50) 초과 요청은 자동으로 50건으로 제한됨
curl "http://localhost:8000/api/stories/?page_size=999"

# 카테고리 필터 + 정렬 + 페이지 조합
curl "http://localhost:8000/api/stories/?category=housing&ordering=-view_count&page=1"
```

## 프로젝트 구조

```
munbeop/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py     # 4차에서 PostgreSQL 설정 추가 예정
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/       # 사용자 관리, JWT 인증
│   ├── stories/        # 사연 CRUD, Category
│   ├── legal_data/     # 법령(Law), 판례(Precedent) — 구조 검증용 최소 데이터
│   ├── search/         # 통합 검색 (3차 키워드 매칭 → 4차 임베딩으로 교체 예정)
│   └── common/         # 공용 페이지네이션 등
├── templates/
├── static/
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## 데이터 적재 정책 (3차 단계)

현재 DB에는 구조 검증용 최소 데이터(법령 5건, 판례 3건)만 입력되어 있습니다.

- 본격적인 법령/판례 데이터는 **STEP 8 이후 별도 단계**에서 적재 예정
- **4차 단계**에서 [국가법령정보센터 OpenAPI](https://www.law.go.kr/) 연동으로 자동화 예정
- 현재 시연용 판례의 `case_number` / `judgment_date` / `content`는 임시값이며 `[임시]` 마커가 붙어 있음 — 발표/배포 전 실제 데이터로 교체 필수

## 면책 고지

본 서비스는 법률 정보 제공 목적이며, 법률 자문이 아닙니다.
구체적인 법률 자문은 변호사와 상담하시기 바랍니다.
