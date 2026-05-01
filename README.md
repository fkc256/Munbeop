# 문법 (Munbeop)

> 법이 어려워서 망설이고 계신가요? 내 상황을 그대로 적으면 관련 법령과 판례, 비슷한 사연을 찾아드립니다.

**일반인을 위한 법률 정보 검색 & 사례 학습 플랫폼**.
케이스노트·엘박스 같은 변호사용 도구와 다르게 일반인 친화 UX와 자연어 입력에 집중했습니다.

## 주요 기능

- 자연어 사연 입력 → 관련 법령/판례 자동 매칭
- 통합 검색 (법령 → 판례 → 유사 사연 순서)
- 커뮤니티 (사연 공유, 댓글/대댓글, 좋아요)
- 북마크 (사연/법령/판례)
- 마이페이지 (내 사연/북마크)

## 차별점

- **일반인 친화 UX**: 변호사용 빽빽한 UI 안티패턴 회피, 친근한 톤
- **법령 먼저, 판례 나중**: 1차 자료부터 보여주는 학습 흐름
- **자연어 입력**: 키워드가 아니라 사연 그대로 — 조사 stripping + 불용어 처리
- **단정적 자문 X**: 변호사법 109조 안전선. AI 답변 생성 X. 모든 결과에 면책 고지.
- **무료 + 광고 + 정부 지원** 비즈니스 모델 (변호사 매칭/광고 ❌)

## 단계별 범위

- **3차 (현재, 4/27 ~ 5/6)**: 동작하는 웹서비스 MVP. 키워드 매칭 검색. PostgreSQL.
- **4차 (예정, 5/8 ~ 6/16)**: AI 임베딩, FastAPI 분리, Celery + Redis, Docker, 외부 API 연동.

3차에서는 의도적으로 다음을 추가하지 않습니다: AI/벡터DB, Docker, Celery, Redis, FastAPI 분리.

## 기술 스택

- Python 3.11+
- Django 5.x + Django REST Framework
- djangorestframework-simplejwt (JWT 인증)
- PostgreSQL 16 (STEP 7.5에서 SQLite → PostgreSQL 전환 완료)
- Django Template + Bootstrap 5 + vanilla JS (3차 후반에 적용 예정)
- python-decouple (.env 관리)

## 설치 및 실행

### 1) PostgreSQL 준비 (STEP 7.5에서 SQLite → PostgreSQL 전환)

```bash
# Ubuntu/WSL
sudo apt install postgresql postgresql-contrib
sudo service postgresql start

# DB 생성 (방법 A — 본인 OS 사용자를 owner로, socket peer 인증)
createdb -E UTF8 munbeop

# DB 생성 (방법 B — 전용 사용자 + 비밀번호, sudo 권한 있는 경우)
sudo -u postgres psql -c "CREATE USER munbeop_user WITH PASSWORD 'your-pw';"
sudo -u postgres psql -c "CREATE DATABASE munbeop OWNER munbeop_user ENCODING 'UTF8';"
```

### 2) Django 셋업

```bash
git clone https://github.com/fkc256/Munbeop.git
cd Munbeop

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# .env에서 DB_USER/DB_PASSWORD/DB_HOST 본인 환경에 맞게 수정
# (방법 A: DB_USER=$USER, DB_PASSWORD/DB_HOST 빈 값 — socket peer)
# (방법 B: DB_USER=munbeop_user, DB_PASSWORD=설정한 비밀번호, DB_HOST=localhost)

python manage.py migrate

# 시연 데이터셋 한 번에 (Story 13 + Law 5 + Precedent 3 + Comment + Like + Bookmark + 사용자)
python manage.py loaddata fixtures/sample_data.json
# loaddata 후 시퀀스 재정렬 (PostgreSQL 특이사항 — 다음 INSERT 시 PK 충돌 방지)
python manage.py sqlsequencereset accounts stories legal_data interactions search | psql -d munbeop

# (선택) 관리자 계정
python manage.py createsuperuser

# 서버 실행
python manage.py runserver

# (운영용) 정적 파일 — staticfiles/ 에 복사 (gitignored)
python manage.py collectstatic --noinput
```

### loaddata 대신 빈 DB로 시작하고 싶을 때

```bash
python manage.py migrate
python manage.py load_categories       # 카테고리 9개
python manage.py load_sample_data      # 법령 5 + 판례 3
# Story는 사용자가 UI에서 직접 작성 (시연 데이터셋은 fixtures/sample_data.json 참조)
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

페이지 라우트:

| Path        | 설명                                                  |
| ----------- | ----------------------------------------------------- |
| `/`         | 홈 (히어로 검색 + 카테고리 9개 + 인기 사연 5건)       |
| `/signup/`  | 회원가입 페이지                                       |
| `/login/`   | 로그인 페이지                                         |
| `/stories/` | 사연 목록 (카테고리 필터, 정렬, 페이지네이션)         |
| `/stories/new/` | 사연 작성 폼 (로그인 필요)                        |
| `/stories/{id}/` | 사연 상세 + **자동 검색**(법령/판례/유사 사연) + 댓글 |
| `/stories/{id}/edit/` | 사연 수정 폼 (작성자만)                      |
| `/laws/`    | 법령 목록 (카테고리/키워드 필터)                      |
| `/laws/{id}/` | 법령 상세 (관련 판례 + 북마크)                      |
| `/precedents/` | 판례 목록 (카테고리/키워드/결과 필터)              |
| `/precedents/{id}/` | 판례 상세 (관련 법령 + 북마크)                |
| `/search/?q=...` | 통합 검색 결과 (법령 → 판례 → 사연 순)         |
| `/me/`      | 마이페이지 (내 사연 / 북마크 — 비로그인 시 로그인 redirect) |

## 발표 시연 흐름

```
홈 → 검색창 입력 ("전세 보증금 못 받고 있어요")
  → /search/ : 관련 법령(주임법 7조/3조) + 판례 + 비슷한 사연
  → 사연 상세 클릭 : 본문 + 자동 검색 결과 + 댓글
  → 좋아요/북마크/댓글 작성
  → 마이페이지 → 내 사연/북마크 확인
```

전 과정이 끊김 없이 동작. 자세한 시연 데이터셋은 [docs/SAMPLE_DATA.md](docs/SAMPLE_DATA.md) 참조.

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

## 관리자 페이지

`http://localhost:8000/admin/` — `createsuperuser`로 만든 계정으로 로그인.

기본 Django 어드민 위에 다음을 커스터마이징:

- **User**: `story_count`(활성 사연 수), `activate/deactivate_users` 액션
- **Story**: `Story.all_objects` queryset (soft-deleted 포함), `comment_count_display`/`like_count_display`, `bulk_soft_delete`/`bulk_restore`/`bulk_hard_delete` 액션
- **Category**: `list_editable=order`로 정렬 순서 즉시 변경, `story/law/precedent_count`
- **Law**: `list_editable=is_active`로 폐지 처리 빠르게, `precedent_count_display`/`bookmark_count_display`, `activate/deactivate_laws` 액션
- **Precedent**: `filter_horizontal=related_laws`로 M2M 편집, `date_hierarchy=judgment_date`
- **Comment**: `Comment.all_objects` queryset, `story_link`(클릭 가능), `parent_id_display`, `like_count_display`
- **Like / Bookmark**: `target_link`로 대상 객체 admin 페이지로 1-클릭 이동

운영자 사용 시나리오:
1. 신고된 사연·댓글 검토 → 부적절하면 `bulk_soft_delete`
2. 사용자 계정 차단 → `is_active=False` 액션 (즉시 로그인 차단)
3. 폐지된 법령 처리 → `is_active=False` (API 응답에서 제외)
4. 카테고리 순서 조정 → list view에서 `order` 직접 편집
5. 잘못 등록된 데이터 영구 삭제 → `bulk_hard_delete` (확인 메시지 노출)

## 시연용 계정

`fixtures/sample_data.json` loaddata 후 다음 계정 사용 가능:

| username | password | 역할 |
|----------|----------|------|
| testuser | testpass1234 | 일반 사용자 (사연 10건 작성자) |
| testuser2 | testpass1234 | 일반 사용자 (소유권 분리 테스트용) |
| admin | admin1234 | 관리자 (Django Admin 접근) |

## 산출물 (docs/)

| 문서 | 내용 |
|------|------|
| [docs/ERD.md](docs/ERD.md) | 데이터 모델 다이어그램 + 관계 명세 |
| [docs/API.md](docs/API.md) | 모든 API 엔드포인트 명세 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 시스템 아키텍처 + 4차 확장 청사진 |
| [docs/SAMPLE_DATA.md](docs/SAMPLE_DATA.md) | 시연 데이터셋 명세 |
| [docs/CHECKLIST.md](docs/CHECKLIST.md) | 부트캠프 자가점검 통과 표 |
| [docs/PITCH.md](docs/PITCH.md) | 발표 가이드 (10분 시간 분배) |

## 데이터 적재 정책 (3차 단계)

현재 DB에는 구조 검증용 최소 데이터(법령 5건, 판례 3건)만 입력되어 있습니다.

- 본격적인 법령/판례 데이터는 **STEP 8 이후 별도 단계**에서 적재 예정
- **4차 단계**에서 [국가법령정보센터 OpenAPI](https://www.law.go.kr/) 연동으로 자동화 예정
- 현재 시연용 판례의 `case_number` / `judgment_date` / `content`는 임시값이며 `[임시]` 마커가 붙어 있음 — 발표/배포 전 실제 데이터로 교체 필수

## 변경 이력

- **2026-05-01 (STEP 7.5)** — SQLite → PostgreSQL 16 전환. 시연 데이터셋(60 객체) 무손실 마이그레이션, 한국어 ILIKE 검색 동작 확인. 이전 SQLite 설정은 `config/settings/dev.py`에 주석으로 보존.

## 면책 고지

본 서비스는 법률 정보 제공 목적이며, 법률 자문이 아닙니다.
구체적인 법률 자문은 변호사와 상담하시기 바랍니다.
