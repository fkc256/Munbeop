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
│   └── stories/        # 사연 CRUD, Category
├── templates/
├── static/
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## 면책 고지

본 서비스는 법률 정보 제공 목적이며, 법률 자문이 아닙니다.
구체적인 법률 자문은 변호사와 상담하시기 바랍니다.
