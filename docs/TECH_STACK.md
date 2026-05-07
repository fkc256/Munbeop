# 기술 스택

문법(Munbeop) 프로젝트의 3차 단계 기술 스택을 한 곳에 정리한 문서.

---

## 1. 언어 & 런타임

| 항목 | 버전 | 비고 |
|------|------|------|
| Python | 3.11+ | 3.12 환경에서 개발/테스트 |
| Node.js | (사용 안 함) | 빌드 도구 없이 vanilla JS 사용 |

## 2. 백엔드

| 항목 | 버전 | 역할 |
|------|------|------|
| **Django** | 5.0 ~ 5.2 | 웹 프레임워크 (URLConf, ORM, Admin, Template) |
| **Django REST Framework (DRF)** | 3.15+ | REST API (ViewSet, Serializer, Pagination, Permission) |
| **djangorestframework-simplejwt** | 5.3+ | JWT 인증 (Access/Refresh, 회전, 블랙리스트) |
| **django-cors-headers** | 4.3+ | CORS 처리 |
| **python-decouple** | 3.8+ | `.env` 환경변수 분리 |

## 3. 데이터베이스

| 항목 | 버전 | 비고 |
|------|------|------|
| **PostgreSQL** | 16 | 메인 DB (3차 STEP 7.5에서 SQLite → PostgreSQL 전환) |
| **psycopg[binary]** | 3.1+ | PostgreSQL 어댑터 (psycopg3) |

3차 초기에는 SQLite 사용 → STEP 7.5에서 PostgreSQL로 전환.
4차에서 pgvector 확장 추가 예정 (임베딩 검색용).

## 4. 인증 & 권한

| 항목 | 적용 |
|------|------|
| 인증 방식 | JWT Bearer (Access 1h / Refresh 7d) |
| Refresh 정책 | 회전 (`ROTATE_REFRESH_TOKENS=True`) + 블랙리스트 |
| 비밀번호 해시 | Django 기본 PBKDF2 (`set_password`) |
| 권한 클래스 | `IsAuthenticatedOrReadOnly` (전역) + `IsOwnerOrReadOnly`, `IsCommentOwnerOrReadOnly` 커스텀 |
| 401 자동 refresh | 클라이언트 JS가 자동 처리 (`api.js` 안에서) |

## 5. 검색 & 로직

| 항목 | 3차 구현 | 4차 계획 |
|------|---------|---------|
| 키워드 추출 | 토큰 분리 + 한국어 조사 stripping + 불용어 제거 | 임베딩 벡터 (HuggingFace 모델) |
| 매칭 알고리즘 | ILIKE Q-OR 매칭 (Python 점수 계산) | pgvector cosine 유사도 |
| 추가 가중치 | 카테고리 boost + engagement (view·like·comment) | 사용자 행동 임베딩 (협업 필터링) |
| 인기글 점수 | `log10(view+1)×2 + like×3 + comment×5` | 동일 (시간 감쇠 추가 가능) |
| 실시간 검색어 | `SearchQuery` 모델 자동 기록 + 24h 빈도 집계 | 동일 (분석용 데이터로 활용) |

## 6. 프론트엔드

| 항목 | 비고 |
|------|------|
| 렌더링 방식 | **Django Template + 클라이언트 JS** (SPA 아님) |
| HTML 템플릿 | `base.html` + `pages/*.html` (12개 페이지) |
| CSS | **vanilla CSS** + CSS 변수 디자인 토큰 |
| JS | **vanilla JS** (프레임워크 없음) — `api.js` / `auth.js` / `common.js` |
| 외부 라이브러리 | Pretendard 폰트 (CDN), Bootstrap 5 grid 일부 (CDN) |
| 디자인 시스템 | Slate Navy(`#1E293B`) + Warm Gold(`#A88E54`) 톤 |

## 7. 페이지네이션

| 항목 | 값 |
|------|------|
| 클래스 | `apps.common.pagination.StandardPagination` (PageNumberPagination 확장) |
| 기본 페이지 크기 | 10 |
| 클라이언트 조정 | `?page_size=20` (1~50) |
| 최대 cap | 50 (DoS 방지) |

## 8. 정적 파일

| 항목 | 경로 |
|------|------|
| 소스 | `static/` (개발용, git 추적) |
| collectstatic 출력 | `staticfiles/` (gitignored) |
| 운영 서빙 | nginx (4차 예정) |

## 9. 배포 / 환경 분리

| 환경 | settings 모듈 | DEBUG | 비고 |
|------|--------------|------|------|
| 개발 | `config.settings.dev` | True | runserver, CORS 전체 허용 |
| 운영 | `config.settings.prod` | False | 보안 헤더 (XSS, NOSNIFF, X-FRAME-OPTIONS=DENY, REFERRER_POLICY), CORS 화이트리스트 |

## 10. 보안

| 항목 | 처리 |
|------|------|
| 비밀 정보 | `.env` 분리 (gitignored), `.env.example` 제공 |
| SECRET_KEY | `python-decouple`로 환경변수 주입 |
| CSRF | Django 기본 활성 (REST API는 JWT라 면제) |
| XSS 방지 | 템플릿 자동 escape + JS의 `escapeHtml()` 헬퍼 |
| 비밀번호 | PBKDF2 해시 (Django 기본) |
| 보안 헤더 | prod settings에서 적용 (XSS_FILTER, NOSNIFF, X_FRAME_OPTIONS=DENY, REFERRER_POLICY=same-origin) |
| 비활성 사용자 | `is_active=False` 시 로그인 차단 |
| 댓글 신고 자동 | 임계 3건 누적 시 `deletion_reason='report'` 자동 처리 |

## 11. 데이터 무결성

| 패턴 | 적용 모델 |
|------|----------|
| **Soft Delete** | `Story`, `Comment` (`is_deleted` + `deleted_at`) |
| **이중 매니저** | `objects` (활성만) + `all_objects` (전체, admin용) |
| **on_delete 정책** | User → Story·Comment: SET_NULL / Category → Story: PROTECT / Story → Comment: CASCADE / User → Like·Bookmark·Report: CASCADE |
| **unique_together** | Like / Bookmark `(user, target_type, target_id)`, Report `(user, comment)`, Law `(law_name, article_number)`, Precedent `(case_number, court)` |
| **인덱스** | Story `(-created_at)`, Comment `(story, created_at)` + `parent`, Law `law_name`, Precedent `(court, -judgment_date)`, SearchQuery `(query, created_at)` |

## 12. 의존성 전체 (`requirements.txt`)

```
Django>=5.0,<6.0
djangorestframework>=3.15,<4.0
djangorestframework-simplejwt>=5.3,<6.0
python-decouple>=3.8,<4.0
django-cors-headers>=4.3,<5.0
psycopg[binary]>=3.1,<4.0
```

총 6개 패키지 (Django 생태계 표준 조합).

## 13. 개발 도구

| 도구 | 용도 |
|------|------|
| **git** + GitHub | 버전 관리 (https://github.com/fkc256/Munbeop) |
| `manage.py` | Django 명령 (migrate, runserver, dumpdata, loaddata, shell, createsuperuser) |
| Custom management commands | `load_categories`, `load_sample_data`, `load_demo_stories`, `load_interaction_samples`, `load_demo_likes`, `load_search_trends` |
| `dumpdata` / `loaddata` | 시연 데이터 백업/복원 (`fixtures/sample_data.json`) |
| `pyflakes` | 미사용 import 검사 |

## 14. 외부 서비스 / CDN

| 항목 | 용도 |
|------|------|
| Pretendard CDN (jsdelivr) | 한글 웹폰트 |
| Bootstrap 5 grid (jsdelivr) | 그리드 유틸 일부 |

외부 API 호출은 3차에서 0건 (4차에서 국가법령정보센터 OpenAPI 추가 예정).

## 15. 성능 최적화

| 항목 | 적용 |
|------|------|
| **N+1 방지** | `select_related`, `prefetch_related`, `annotate` (Story 목록 응답 페이지당 2 쿼리로 측정) |
| Subquery + Coalesce | Story `like_count` 집계 (target_type='story') |
| Exists annotation | 인증 사용자 `is_liked`, `is_bookmarked` (단일 쿼리) |
| Bulk operations | `bulk_create` (좋아요 시드 2,300건 적재) |
| view_count race-safe | F-expression `view_count = view_count + 1` (atomic) |

## 16. 테스트 / 검증

3차에서는 자동 테스트 코드 미작성. 대신 STEP별 검증 시나리오(curl + shell)로 수동 검증.

| 검증 방식 | 적용 |
|----------|------|
| `python manage.py check` | 모든 STEP 후 실행 |
| Curl 시나리오 | 각 STEP 산출물 보고에 5~30개 시나리오 검증 |
| Shell 검증 | Soft Delete 정합성, 베이스라인 카운트 |
| Pyflakes | 미사용 import 검사 (apps/ + config/) |

자동 테스트 코드는 4차에서 추가 예정 (pytest-django).

## 17. 4차에서 추가될 기술

| 항목 | 용도 |
|------|------|
| **FastAPI** | 임베딩 모델 별도 서빙 (Django와 분리) |
| **HuggingFace Transformers** | 한국어 임베딩 모델 (`ko-sroberta`, `Sentence-Korean` 등 후보) |
| **pgvector** | PostgreSQL 벡터 확장 (cosine 유사도 검색) |
| **Celery + Redis** | 비동기 큐 (검색 임베딩 / 외부 API 적재) |
| **Docker Compose** | 멀티 컨테이너 (Django + FastAPI + Redis + PG + nginx) |
| **gunicorn** | WSGI 서버 (운영) |
| **nginx** | 정적 파일 + 리버스 프록시 |
| **Prometheus + Grafana** | 모니터링 + 메트릭 |
| **국가법령정보센터 OpenAPI** | 법령 자동 적재 |
| **pytest-django** | 자동 테스트 |

---

## 한 줄 요약

> Django 5 + DRF + PostgreSQL 16 + JWT + Vanilla JS 조합. 3차는 키워드 매칭 기반, 4차에서 임베딩 + 비동기 인프라로 확장 예정. 검색 모듈은 함수 시그니처 유지로 swap-friendly 설계.
