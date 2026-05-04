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
| 62 | labor | 50 | testuser | - | 3년 다닌 회사에서 갑작스러운 해고 통보 |
| 63 | consumer | 25 | testuser2 | - | 배송 중 파손된 가전, 환불 거부 당했습니다 |
| 64 | family | 35 | testuser | ✓ | 이혼 양육비 산정, 산정표대로 따라야 하나요? |
| 65 | traffic | 10 | testuser2 | - | 이면도로 사거리 사고, 과실비율 6:4 납득이 안 갑니다 |
| 66 | criminal | 8 | testuser | ✓ | 공공장소에서 험담 들었는데 명예훼손 신고 가능한가요? |
| 67 | realestate | 40 | testuser | - | 아파트 매매 계약을 매도인이 일방 해제 통보 |
| 68 | debt | 20 | testuser2 | ✓ | 카톡으로 빌려준 돈 1500만원, 회수 가능할까요? |
| 69 | etc | 5 | testuser | - | 윗집 누수로 손상, 윗집과 시공사 누구한테 청구하나요? |

**STEP 2.5 잔여 housing seed (id=17~20)는 STEP 8에서 hard delete** — 본문이 빈약("전세 보증금 관련 새 사연 #N 입니다." 한 줄)해서 사용자 시연 시 노이즈로 작용. 본문 충실한 id=1 housing 사연 1건 유지.

### 분포 요약 (STEP 8 정리 후)

- **카테고리 커버리지**: 9개 카테고리 모두 1건씩 (총 9건)
- **작성자**: testuser 6건, testuser2 3건
- **익명 처리**: 3건 (family, criminal, debt — 민감 카테고리)
- **view_count 범위**: 5 ~ 50 (인기순 정렬 시연용 분포)

### 법령/판례 매칭 의도

검색 시연 시 다음 매칭이 자연스럽게 나오도록 사연 키워드를 설계했습니다.

| 사연 id | 매칭 예상 Law | 매칭 예상 Precedent |
|---------|--------------|---------------------|
| 1, 17~20 (housing) | 주임법 제7조 / 제3조 | 임대차 보증금 반환 사건 |
| 62 (labor) | 근기법 제23조 | 부당해고 구제 사건 |
| 66 (criminal) | 형법 제307조 | 명예훼손 위법성 조각 사건 |
| 69 (etc) | 민법 제750조 | (없음 — 시연 시 "관련 판례 없음" 케이스) |

---

## 2. Law (법령) — 14건

STEP 8에서 매칭 빈 카테고리 보강 (consumer/family/traffic/realestate/debt 각 1~2건 + etc 1건).

| 카테고리 | 법령 |
|---------|------|
| housing | 주임법 제7조, 제3조 |
| labor | 근로기준법 제23조 |
| consumer | 전자상거래법 제17조, 약관규제법 제6조 |
| family | 민법 제837조, 제839조의2 |
| traffic | 자동차손해배상법 제3조, 도로교통법 제54조 |
| criminal | 형법 제307조 |
| realestate | 민법 제565조 |
| debt | 민법 제162조, 제428조 |
| etc | 민법 제750조 |

본문 정확성에 관한 자세한 내용은 STEP 3 산출물 보고의 verification list 참조.

---

## 3. Precedent (판례) — 9건

각 카테고리에 1건씩 매칭. 사연 상세 페이지에서 자동 검색 시 카테고리 컨텍스트로 정확히 매칭.

| id | case_number | court | judgment_date | category | result_type |
|----|-------------|-------|---------------|----------|-------------|
| 1 | `[임시] 2022다123456` | 대법원 | 2022-06-15 | housing | plaintiff_partial |
| 2 | `[임시] 2023나98765` | 서울중앙지방법원 | 2023-03-22 | labor | plaintiff_win |
| 3 | `[임시] 2021도54321` | 대법원 | 2021-11-04 | criminal | defendant_win |
| + | `[임시] 2022다112233` | 서울중앙지방법원 | 2022-09-08 | consumer | plaintiff_win |
| + | `[임시] 2023느합3456` | 서울가정법원 | 2023-05-11 | family | plaintiff_partial |
| + | `[임시] 2022나445566` | 서울중앙지방법원 | 2022-11-25 | traffic | plaintiff_partial |
| + | `[임시] 2023가합7788` | 서울중앙지방법원 | 2023-08-17 | realestate | plaintiff_win |
| + | `[임시] 2021가소9876` | 서울중앙지방법원 | 2021-07-30 | debt | plaintiff_win |
| + | `[임시] 2022가단55432` | 서울중앙지방법원 | 2022-04-19 | etc | plaintiff_partial |

⚠️ **모든 판례 메타데이터는 임시값**입니다. `case_number`에 `[임시]` 마커, `content` 본문 첫 줄에도 `[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]` 마커. 발표/배포 직전 정식 데이터로 교체 필수.

---

## 4. 사용자 (User) — 6명

| id | username | password | nickname | 비고 |
|----|----------|----------|----------|------|
| 1 | testuser | testpass1234 | 테스트 | STEP 1 생성, 사연 6건 작성 |
| 2 | testuser2 | testpass1234 | 두번째 | STEP 2 생성 (소유권 검증), 사연 3건 작성 |
| 3 | testuser3 | testpass1234 | 세번째 | STEP 6A 생성 (회원가입 검증) |
| 4 | admin | admin1234 | 관리자 | STEP 7 생성 (Django Admin) |
| 5 | lawhelper | lawhelp1234 | 도움이 | STEP 8 — 댓글 전문가 톤 캐릭터 |
| 6 | survivor | survive1234 | 겪어본사람 | STEP 8 — 댓글 경험담 캐릭터 |

## 5. 댓글 (Comment) — 25건

9개 시연 사연 모두에 댓글 2~4건씩. 톤 다양화:
- **lawhelper (도움이)**: "참고로 ~ 절차가 있어요", "법조문상 ~" — 전문가 톤
- **survivor (겪어본사람)**: "저도 비슷한 상황 겪었어요", "저는 ~로 해결했어요" — 경험담
- **testuser / testuser2**: 비전문가 공감 / 추가 팁

대댓글: 일부 댓글에 답변 흐름으로 1단계 reply (총 3건 정도).

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
