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

# 6. (선택) 관리자 계정
python manage.py createsuperuser

# 7. 서버 실행
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
│   └── accounts/       # 사용자 관리, JWT 인증
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
