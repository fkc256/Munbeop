# 시연 데이터셋 (3차 단계)

이 문서는 **STEP 3.5에서 정리·확정한 시연용 데이터셋**의 명세입니다.
STEP 4(통합 검색) 이후의 모든 검증/시연은 이 데이터셋을 기준으로 합니다.

본격적인 법령/판례·사연 적재는 **STEP 8 이후 별도 단계**에서 진행되며,
4차에서 외부 OpenAPI 연동으로 자동화될 예정입니다.

---

## 1. Story (사연) — 13건

| id | category | view_count | 작성자 | 익명 | 제목 |
|----|----------|-----------:|--------|:----:|------|
| 1 | housing | 45 | testuser | - | 전세 보증금 반환 지연 문의 |
| 17 | housing | 15 | testuser | - | 전세 관련 추가 사연 #1 |
| 18 | housing | 3 | testuser | - | 전세 관련 추가 사연 #2 |
| 19 | housing | 0 | testuser | - | 전세 관련 추가 사연 #3 |
| 20 | housing | 7 | testuser | - | 전세 관련 추가 사연 #4 |
| 62 | labor | 50 | testuser | - | 3년 다닌 회사에서 갑작스러운 해고 통보 |
| 63 | consumer | 25 | testuser2 | - | 배송 중 파손된 가전, 환불 거부 당했습니다 |
| 64 | family | 35 | testuser | ✓ | 이혼 양육비 산정, 산정표대로 따라야 하나요? |
| 65 | traffic | 10 | testuser2 | - | 이면도로 사거리 사고, 과실비율 6:4 납득이 안 갑니다 |
| 66 | criminal | 8 | testuser | ✓ | 공공장소에서 험담 들었는데 명예훼손 신고 가능한가요? |
| 67 | realestate | 40 | testuser | - | 아파트 매매 계약을 매도인이 일방 해제 통보 |
| 68 | debt | 20 | testuser2 | ✓ | 카톡으로 빌려준 돈 1500만원, 회수 가능할까요? |
| 69 | etc | 5 | testuser | - | 윗집 누수로 손상, 윗집과 시공사 누구한테 청구하나요? |

### 분포 요약

- **카테고리 커버리지**: 9개 카테고리 모두 1건 이상 (housing 5건, 나머지 1건씩)
- **작성자**: testuser 10건, testuser2 3건
- **익명 처리**: 3건 (family, criminal, debt — 민감 카테고리)
- **view_count 범위**: 0 ~ 50 (인기순 정렬 시연용 분포)

### 법령/판례 매칭 의도

검색 시연 시 다음 매칭이 자연스럽게 나오도록 사연 키워드를 설계했습니다.

| 사연 id | 매칭 예상 Law | 매칭 예상 Precedent |
|---------|--------------|---------------------|
| 1, 17~20 (housing) | 주임법 제7조 / 제3조 | 임대차 보증금 반환 사건 |
| 62 (labor) | 근기법 제23조 | 부당해고 구제 사건 |
| 66 (criminal) | 형법 제307조 | 명예훼손 위법성 조각 사건 |
| 69 (etc) | 민법 제750조 | (없음 — 시연 시 "관련 판례 없음" 케이스) |

---

## 2. Law (법령) — 5건

| id | law_name | article_number | category | 본문 정확성 |
|----|----------|----------------|----------|-------------|
| 1 | 주택임대차보호법 | 제7조 | housing | paraphrase + source_url 안내 |
| 2 | 주택임대차보호법 | 제3조 | housing | 제1항만 발췌 |
| 3 | 근로기준법 | 제23조 | labor | 제1항만 발췌 |
| 4 | 형법 | 제307조 | criminal | 제1·2항 (확신도 높음) |
| 5 | 민법 | 제750조 | etc | 본문 (확신도 가장 높음) |

본문 정확성에 관한 자세한 내용은 STEP 3 산출물 보고의 verification list 참조.

---

## 3. Precedent (판례) — 3건

| id | case_number | court | judgment_date | category | result_type |
|----|-------------|-------|---------------|----------|-------------|
| 1 | `[임시] 2022다123456` | 대법원 | 2022-06-15 | housing | plaintiff_partial |
| 2 | `[임시] 2023나98765` | 서울중앙지방법원 | 2023-03-22 | labor | plaintiff_win |
| 3 | `[임시] 2021도54321` | 대법원 | 2021-11-04 | criminal | defendant_win |

⚠️ **모든 판례 메타데이터는 임시값**입니다. `case_number`에 `[임시]` 마커가 붙어 있고,
`content` 본문 첫 줄에도 `[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]` 마커가 있습니다.

발표/배포 직전 다음을 반드시 확인할 것:
- `?keyword=임시` 검색 시 매칭되지 않도록 모든 임시 마커 제거
- 정확한 case_number, court, judgment_date 로 교체
- content 본문을 정식 판례문으로 교체

### M2M (Precedent ↔ Law) 연결

| Precedent | → Related Law |
|-----------|---------------|
| `[임시] 2022다123456` (housing) | 주임법 제7조 |
| `[임시] 2023나98765` (labor) | 근기법 제23조 |
| `[임시] 2021도54321` (criminal) | 형법 제307조 |

---

## 4. 사용자 (User)

| id | username | password | nickname | 비고 |
|----|----------|----------|----------|------|
| 1 | testuser | testpass1234 | 테스트 | STEP 1 생성 |
| 2 | testuser2 | testpass1234 | 두번째 | STEP 2 생성 (소유권 검증용) |

---

## 5. 데이터셋 활용 범위

이 데이터셋은 다음 단계에서 동일하게 사용됩니다:

- **STEP 4** — 통합 검색 (사연/법령/판례 키워드 매칭)
- **STEP 5** — 댓글, 좋아요, 북마크 (interactions)
- **STEP 6** — 사용자 UI (Bootstrap 템플릿)
- **STEP 7~9** — 추가 기능 + 발표 시연

이후 STEP에서 검증용 시드를 추가할 경우 본 문서를 업데이트합니다.

## 6. 재현 (Reset 시 참고)

DB를 처음부터 다시 만드는 경우의 기본 절차:

```bash
python manage.py migrate
python manage.py load_categories         # Category 9개
python manage.py load_sample_data        # Law 5건, Precedent 3건
# Story 13건은 별도 시드 명령 없음 — 본 문서를 참고해 수동 재현하거나
# 필요 시 `apps/stories/management/commands/load_demo_stories.py` 추가
```

3차 단계에서는 Story 13건을 자동 시드 명령으로 만들 계획이 없습니다 (수동 입력 가정).
4차 진입 시 자동화 검토.
