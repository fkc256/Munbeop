# 시스템 아키텍처

## 1. 전체 구조 (3차)

```
[사용자 브라우저]
       │
       ▼ HTTP (Django 템플릿 렌더, `<script>` 인라인)
[Django Template + Bootstrap 5 + vanilla JS]
       │
       ▼ fetch (JWT Bearer)
[DRF REST API]
       │
       ▼
[Django ORM]
       │
       ▼
[PostgreSQL 16]
```

WSGI 서버는 `runserver` (개발) — 4차에서 gunicorn + nginx 도입 예정.

## 2. 앱 책임 분리

도메인 책임으로 나눈 5개 + 공용 1개:

| 앱 | 책임 | 핵심 모델 |
|------|------|-----------|
| `apps.accounts` | 사용자 / 인증 | `User` (AbstractUser + nickname) |
| `apps.stories` | 사연 + 분쟁 카테고리 (도메인 핵심) | `Story`, `Category` |
| `apps.legal_data` | 법령 / 판례 (참조 데이터) | `Law`, `Precedent` |
| `apps.interactions` | 사용자 행동 (댓글/좋아요/북마크) | `Comment`, `Like`, `Bookmark` |
| `apps.search` | 통합 검색 (4차에서 임베딩으로 교체될 자리) | (모델 없음) |
| `apps.common` | 공용 컴포넌트 | `StandardPagination` |

## 3. 데이터 흐름

```
[사용자 입력]
   │
   ▼ HTTP/fetch
[URLConf]
   │ → admin/, api/accounts/, api/, ...
   ▼
[DRF View / TemplateView]
   │ → Permission 검사 (IsOwnerOrReadOnly 등)
   ▼
[Serializer]
   │ → 입력 검증 + 출력 직렬화
   ▼
[Service / ORM Queryset]
   │ → select_related / prefetch_related / annotate
   ▼
[PostgreSQL]
```

## 4. 인증 흐름

```
1. POST /api/accounts/login/ {username, password}
   → access (1h) + refresh (7d) 발급
2. 클라이언트 (JS): localStorage 에 저장, fetch 시 `Authorization: Bearer <access>`
3. access 만료(401) → refresh로 자동 재발급 (rotate=True, 이전 refresh 블랙리스트)
4. 로그아웃: refresh 블랙리스트 → 더 이상 재발급 X
```

## 5. 검색 알고리즘 (3차)

```
[사용자 자연어 입력]
   │
   ▼
[utils.extract_keywords]
   - 토큰 분할 (공백/문장부호)
   - 한국어 조사 stripping (보증금을 → 보증금)
   - 불용어 제거 (저는, 입니다, 어떻게, ...)
   - 길이 ≥ 2, 중복 제거, 상한 10
   ▼
[services.search_laws / search_precedents / search_stories]
   - Q-OR ILIKE 매칭 (icontains, 영문 case-insensitive)
   - Python-side 점수: 매칭된 distinct 키워드 개수
   - Tiebreak:
     * Laws: score desc → updated_at desc
     * Precedents: score desc → judgment_date desc
     * Stories: score desc → view_count desc
   - Top N (5/10/5)
   ▼
[UnifiedSearchView]
   - 결과를 "법령 → 판례 → 사연" 순으로 묶어 반환
   - 면책 고지 포함
```

### 4차 교체 자리

같은 시그니처 / 동일 contract (인스턴스에 `_matched_keywords`, `_score` 부착)를 유지하므로
ViewSet/Serializer 수정 없이 검색 엔진만 swap:

```
extract_keywords(text) -> list[str]   →   generate_embedding(text) -> vector[1536]
search_*(keywords, ...) -> [Model]    →   ANN(cosine_similarity, top_k)
```

PostgreSQL pgvector 확장 또는 별도 vector store (Qdrant 등) 도입 예정.

## 6. Soft Delete 정책

| 모델 | 정책 |
|------|------|
| `Story` | `is_deleted` + `deleted_at`. `Story.objects` 매니저가 자동 필터. `all_objects`는 admin/감사용 |
| `Comment` | 동일. 추가로 "활성 대댓글이 있는 deleted 부모"는 placeholder로 보존 |
| `User` | Django 기본 `is_active`로 처리 (`is_active=False` 시 로그인 차단) |
| `Like`, `Bookmark` | 토글 방식이므로 hard delete |

## 7. 페이지네이션

`apps.common.pagination.StandardPagination`:
- `page_size = 10` (기본)
- `page_size_query_param = 'page_size'` (클라이언트 조정)
- `max_page_size = 50` (DoS 방지 자동 cap)

## 8. 환경 분리

| 설정 | dev.py | prod.py |
|------|--------|---------|
| DEBUG | True | False |
| ALLOWED_HOSTS | `*` | `.env` 의 `DJANGO_ALLOWED_HOSTS` |
| DB | PostgreSQL (`.env` `DB_*`) | 동일 (4차에서 매니지드 PG로) |
| CORS | `ALLOW_ALL=True` | `ALLOWED_ORIGINS=[]` (4차에서 화이트리스트) |
| 보안 헤더 | 없음 | XSS_FILTER, NOSNIFF, X_FRAME_OPTIONS=DENY, REFERRER_POLICY=same-origin |

## 9. 4차 확장 청사진

```
[브라우저]
   │
   ▼
[nginx (정적 파일 + reverse proxy)]
   │
   ├─→ [Django (gunicorn) — 사용자 요청, ORM, 인증]
   │       │
   │       ▼
   │   [PostgreSQL + pgvector]
   │
   └─→ [FastAPI (HuggingFace 임베딩)]
           │
           ▼
       [Celery worker + Redis broker]
           │
           ▼
       [국가법령정보센터 OpenAPI 크롤러 (주기 적재)]

모니터링: Prometheus + Grafana
배포: Docker Compose (개발) / K8s (운영)
```

3차의 `apps.search` 서비스 함수는 그대로 두고 내부 구현만 임베딩 매칭으로 교체.
ViewSet/Serializer/URLConf는 변경 없음.
