# 부트캠프 3차 자가점검 체크리스트

## 1. 프로젝트 소개 ✅
- [x] 프로젝트명: 문법 (Munbeop)
- [x] 한 줄 소개: 일반인을 위한 법률 정보 검색 & 사례 학습 플랫폼
- [x] 문제 정의: 일반인이 법률 정보에 접근하기 어렵다
- [x] 사용자 정의: 분쟁/사고/계약 문제로 법률 정보가 필요한 일반인
- [x] 차별점: 일반인 친화 UX + "법령 먼저, 판례 나중" 흐름 + 자연어 사연 입력

## 2. 핵심 데이터 구조 ✅
- [x] 핵심 모델 설명 가능 (Story, Law, Precedent, Comment, Like, Bookmark)
- [x] User-Story-Category 관계 설명 가능
- [x] M2M 관계 설명 (Precedent ↔ Law via related_laws)
- [x] Self-FK 설명 (Comment.parent — 1단계 대댓글)
- [x] ERD 문서 존재: `docs/ERD.md` (mermaid + on_delete 표)

## 3. 기능 ✅
- [x] 회원가입 / 로그인 / 로그아웃 (JWT)
- [x] 사연 CRUD + 카테고리 필터 + 정렬 + 페이지네이션
- [x] 법령 / 판례 조회 + 검색
- [x] 통합 검색 ("법령 → 판례 → 유사 사연" 순서)
- [x] 댓글 + 1단계 대댓글
- [x] 좋아요 / 북마크 토글
- [x] 마이페이지 (내 사연 / 북마크)
- [x] 관리자 페이지 (8개 모델 커스터마이징, soft delete 처리)

## 4. 검색 동작 ✅
- [x] 자연어 입력 처리 (조사 stripping, 불용어 제거)
- [x] 한국어 ILIKE 매칭 (PostgreSQL `ILIKE`)
- [x] 매칭 점수 + 정렬 (score desc, 동점 시 도메인별 tiebreak)
- [x] 카테고리 필터 + 자기 사연 제외
- [x] 면책 고지 응답 포함

## 5. 인증 / 권한 ✅
- [x] JWT Access (1h) + Refresh (7d) + 회전 + 블랙리스트
- [x] 401 시 자동 refresh (클라이언트 JS)
- [x] 작성자 권한 (사연/댓글 수정/삭제는 작성자만)
- [x] 비인증 사용자 보호 (좋아요/북마크/댓글 작성 401)
- [x] 비활성 사용자 (`is_active=False`) 로그인 차단

## 6. 데이터 무결성 ✅
- [x] Soft Delete (Story, Comment) — `is_deleted` 필터, all_objects 노출
- [x] 페이지네이션 cap (max_page_size=50, DoS 방지)
- [x] N+1 방지 (Story 목록에서 annotate + Subquery + Exists)
- [x] 비밀번호 해시 저장 (Django `set_password`)
- [x] 입력 검증 (Serializer min/max length, 카테고리 매칭, parent 검증 등)
- [x] XSS 방지 (모든 사용자 입력은 JS `escapeHtml` 또는 textContent로)

## 7. 환경 / 배포 ✅
- [x] 환경 분리: `config/settings/dev.py`, `prod.py`
- [x] 비밀 정보 `.env` 분리 (gitignored), `.env.example` 제공
- [x] PostgreSQL 16 (STEP 7.5에서 SQLite → PostgreSQL 전환)
- [x] 정적 파일: `STATIC_ROOT` 설정 + `collectstatic` 동작
- [x] 보안 헤더 (prod): XSS_FILTER, NOSNIFF, X_FRAME_OPTIONS=DENY, REFERRER_POLICY

## 8. 산출물 / 재현성 ✅
- [x] README.md — 15분 안에 실행 가능한 설치 가이드
- [x] `fixtures/sample_data.json` — 시연 데이터 60객체 재현 가능
- [x] ERD: `docs/ERD.md`
- [x] API 명세: `docs/API.md`
- [x] 아키텍처: `docs/ARCHITECTURE.md`
- [x] 데이터셋 명세: `docs/SAMPLE_DATA.md`
- [x] 발표 자료 가이드: `docs/PITCH.md`
- [x] 자가점검: `docs/CHECKLIST.md` (이 문서)
- [x] git 히스토리: STEP별 커밋 + push (https://github.com/fkc256/Munbeop)

## 변호사법 109조 안전선 ✅
- [x] 변호사 매칭/광고 기능 X
- [x] 단정적 자문("당신은 ~해야 합니다") 출력 X
- [x] AI 답변 생성 X (4차에도 변동 없음)
- [x] 모든 응답에 면책 고지 노출
- [x] 사용자 정보를 변호사에게 전달하는 기능 X

## 가산점 누적 (+20 상한)

| 항목 | 점수 |
|------|------|
| JWT 인증 | +5 |
| 페이지네이션 고도화 (`page_size_query_param`, `max_page_size`) | +1 |
| Soft Delete (Story, Comment + 매니저 + admin all_objects) | +2 |
| 권한 (작성자만 수정/삭제, IsOwnerOrReadOnly) | +2 |
| 통합 검색 (자연어 입력, 조사 처리, 매칭 점수) | +2 |
| 인터랙션 (좋아요/북마크 토글) | +2 |
| 댓글 고도화 (1단계 대댓글, deleted placeholder) | +2 |
| Admin 커스터마이징 (8개 모델, 액션, list_editable, target_link) | +2 |
| PostgreSQL 전환 (SQLite → PG, 데이터 100% 보존) | +2 |
| **누적** | **+20** ← 상한 도달 |

## 절대 금지선 준수 확인 ✅
- [x] AI/임베딩/벡터DB ❌ (4차)
- [x] Docker / Celery / Redis ❌ (4차)
- [x] FastAPI 분리 ❌ (4차)
- [x] 변호사 매칭 / 광고 ❌ (영구)
- [x] 단정적 자문 출력 ❌ (영구)
- [x] AI가 법령/판례 본문을 생성·요약 ❌ (4차에도 X)
