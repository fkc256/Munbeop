# API 명세

기준 URL: `http://localhost:8000/api`
인증: JWT Bearer (Access 1시간 / Refresh 7일, 블랙리스트 + 회전).

응답은 명시 없으면 `application/json`. 페이지네이션은 `count / next / previous / results` 형식.
페이지 크기는 기본 10, `?page_size=` 로 조정 (최대 50).

---

## 인증 (`/api/accounts/`)

### POST `/api/accounts/signup/`
- 인증: ❌
- Body: `username`, `email`, `password`, `password2`, `nickname`
- 응답: 201 `{id, username, email, nickname, created_at}`
- 에러: 400 (필드별 에러 — `password2`, `email`, `username`)

### POST `/api/accounts/login/`
- 인증: ❌
- Body: `username`, `password`
- 응답: 200 `{access, refresh}`
- 에러: 401 (잘못된 자격 증명, `is_active=False`)

### POST `/api/accounts/login/refresh/`
- 인증: ❌
- Body: `refresh`
- 응답: 200 `{access, refresh}` (회전 정책)
- 에러: 401 (블랙리스트된 토큰 등)

### POST `/api/accounts/logout/`
- 인증: Access
- Body: `refresh`
- 응답: 205 (refresh 블랙리스트)

### GET `/api/accounts/me/`
- 인증: Access
- 응답: 200 `{id, username, email, nickname, created_at}`

---

## 카테고리 (`/api/categories/`)

### GET `/api/categories/`
- 인증: ❌
- 페이지네이션 ❌ (전체 9건)
- 응답: 200 `[{id, name, slug, description, order}, ...]`

---

## 사연 (`/api/stories/`)

### GET `/api/stories/`
- 인증: ❌
- 쿼리: `?category=<slug>` `?ordering=-created_at|-view_count` `?page=` `?page_size=` `?author=me` (인증 시)
- 응답: 200 페이지네이션 + 항목별 `category(nested)`, `author_display`, `view_count`, `comment_count`, `like_count`, `is_liked`, `is_bookmarked`

### POST `/api/stories/`
- 인증: Access
- Body: `title`(5~200), `content`(10+), `category`(id), `is_anonymous`
- 응답: 201 (Detail Serializer)

### GET `/api/stories/{id}/`
- 인증: ❌ (단, `is_owner`/`is_liked`/`is_bookmarked`는 인증 시 정확)
- 응답: 200, `view_count` +1 자동 증가
- 에러: 404 (soft-deleted 또는 미존재)

### PATCH `/api/stories/{id}/`
- 인증: Access (작성자만)
- Body: 부분 (title/content/category/is_anonymous)
- 응답: 200
- 에러: 403 (타인), 400 (검증)

### DELETE `/api/stories/{id}/`
- 인증: Access (작성자만)
- 응답: 204 (soft delete)
- 에러: 403, 404

---

## 법령 (`/api/laws/`)

### GET `/api/laws/`
- 인증: ❌
- 쿼리: `?category=` `?keyword=` `?ordering=law_name|article_number`
- 응답: 200 페이지네이션, `is_active=True`만

### GET `/api/laws/{id}/`
- 인증: ❌ (단, `is_bookmarked`는 인증 시)
- 응답: 200 `{... , related_precedents: [최근 5건]}`

---

## 판례 (`/api/precedents/`)

### GET `/api/precedents/`
- 인증: ❌
- 쿼리: `?category=` `?keyword=` `?court=<exact>` `?result_type=` `?ordering=-judgment_date`
- 응답: 200 페이지네이션

### GET `/api/precedents/{id}/`
- 인증: ❌ (`is_bookmarked` 인증 시)
- 응답: 200 `{..., related_laws: [...]}`

---

## 통합 검색 (`/api/search/`)

### POST `/api/search/`
- 인증: ❌
- Body: `query` (자연어), `category`(slug, 선택), `exclude_story_id`(선택)
- 응답: 200
  ```json
  {
    "query": "...",
    "extracted_keywords": ["전세", "보증금"],
    "results": {
      "laws":       [{...}, ...],   // Top 5
      "precedents": [{...}, ...],   // Top 10
      "stories":    [{...}, ...]    // Top 5
    },
    "counts": {"laws": 2, "precedents": 1, "stories": 5},
    "disclaimer": "본 검색 결과는 ..."
  }
  ```

각 결과 항목에 `matched_keywords`(매칭된 키워드 리스트) + `score`(매칭 키워드 개수) 포함.

### GET `/api/search/?q=...&category=...&exclude_story_id=...`
- POST와 동일 응답 형식 (URL 공유용)

---

## 댓글 (`/api/stories/{story_id}/comments/`, `/api/comments/{id}/`)

### GET `/api/stories/{story_id}/comments/`
- 인증: ❌
- 응답: 200 페이지네이션
- 최상위 댓글만 + 각 댓글에 `replies` (1단계 대댓글) nested
- soft-deleted 부모는 활성 대댓글 ≥1일 때만 placeholder("삭제된 댓글입니다")로 노출

### POST `/api/stories/{story_id}/comments/`
- 인증: Access
- Body: `content` (1~1000), `parent`(id, 선택)
- 응답: 201
- 에러: 400 (parent.parent != null → 대댓글에 답글 금지, 다른 사연의 댓글을 parent로 → 거부)

### GET / PATCH / DELETE `/api/comments/{id}/`
- PATCH/DELETE는 작성자만 (403 if not)
- DELETE는 soft delete (204)

---

## 좋아요 (`/api/likes/toggle/`)

### POST `/api/likes/toggle/`
- 인증: Access
- Body: `target_type` (`story` | `comment`), `target_id`
- 응답: 200 `{liked: true|false, count: <total>}`
- 에러: 404 (대상이 존재하지 않거나 soft-deleted), 401 (비인증)

---

## 북마크 (`/api/bookmarks/toggle/`, `/api/bookmarks/`)

### POST `/api/bookmarks/toggle/`
- 인증: Access
- Body: `target_type` (`story` | `law` | `precedent`), `target_id`
- 응답: 200 `{bookmarked: true|false}`
- 에러: 404, 401

### GET `/api/bookmarks/`
- 인증: Access (자기 북마크만)
- 쿼리: `?target_type=story|law|precedent`
- 응답: 200 페이지네이션, 각 항목에 `target_data` (대상 객체의 핵심 필드)

---

## 페이지 (`TemplateView` 라우트)

| Path | 설명 |
|------|------|
| `/` | 홈 |
| `/signup/`, `/login/` | 인증 |
| `/stories/`, `/stories/new/`, `/stories/{id}/`, `/stories/{id}/edit/` | 사연 |
| `/laws/`, `/laws/{id}/` | 법령 |
| `/precedents/`, `/precedents/{id}/` | 판례 |
| `/search/?q=...` | 통합 검색 결과 |
| `/me/` | 마이페이지 (비로그인 시 `/login/` redirect) |
| `/admin/` | Django 관리자 |

---

## 면책 고지

모든 검색 응답에 `disclaimer` 필드 포함:

> "본 검색 결과는 법률 정보 제공 목적이며, 법률 자문이 아닙니다. 구체적인 법률 자문은 변호사와 상담하시기 바랍니다."
