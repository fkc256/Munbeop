"""
구조 검증 + 검색 동작 확인용 최소 시연 데이터 (Law 5건, Precedent 3건).

본격적인 법령/판례 데이터는 STEP 8 이후 별도 단계에서 적재 예정이며,
4차에서 국가법령정보센터 OpenAPI 연동으로 자동화될 예정.

내용 정확성 메모:
- 민법 750조, 형법 307조: 알려진 본문 그대로
- 근로기준법 23조 1항, 주임법 3조 1항: 1항만 발췌 (다른 항 미포함)
- 주임법 7조: 본문 일부 paraphrase + source_url 안내 문구
- Precedent 메타데이터(case_number/court/judgment_date): 모두 임시값 — `[임시]` 마커
- 발표 직전 임시 데이터 교체 필수 (검색에 `?keyword=임시`로 잡히는 점 주의)
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.legal_data.models import Law, Precedent
from apps.stories.models import Category


LAWS = [
    {
        "law_name": "주택임대차보호법",
        "article_number": "제7조",
        "article_title": "차임 등의 증감청구권",
        "content": (
            "당사자는 약정한 차임이나 보증금이 임차주택에 관한 조세, 공과금, 그 밖의 부담의 "
            "증감이나 경제사정의 변동으로 적절하지 아니하게 된 때에는 장래에 대하여 그 증감을 "
            "청구할 수 있다. 다만, 증액의 경우에는 대통령령으로 정하는 기준에 따른 비율을 "
            "초과하지 못한다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "housing",
        "keywords": "전세,월세,보증금,차임,증감,임대인,임차인",
        "source_url": "https://www.law.go.kr/법령/주택임대차보호법",
    },
    {
        "law_name": "주택임대차보호법",
        "article_number": "제3조",
        "article_title": "대항력 등",
        "content": (
            "① 임대차는 그 등기가 없는 경우에도 임차인이 주택의 인도와 주민등록을 마친 "
            "때에는 그 다음 날부터 제3자에 대하여 효력이 생긴다.\n"
            "(제1항만 발췌. 제2항~제5항은 source_url 참조)"
        ),
        "category_slug": "housing",
        "keywords": "대항력,전입신고,확정일자,임차인,보증금",
        "source_url": "https://www.law.go.kr/법령/주택임대차보호법",
    },
    {
        "law_name": "근로기준법",
        "article_number": "제23조",
        "article_title": "해고 등의 제한",
        "content": (
            "① 사용자는 근로자에게 정당한 이유 없이 해고, 휴직, 정직, 전직, 감봉, 그 밖의 "
            "징벌(이하 “부당해고등”이라 한다)을 하지 못한다.\n"
            "(제1항만 발췌. 제2항(요양 중 해고 제한 등)은 source_url 참조)"
        ),
        "category_slug": "labor",
        "keywords": "해고,정당한이유,징계,부당해고,근로자",
        "source_url": "https://www.law.go.kr/법령/근로기준법",
    },
    {
        "law_name": "형법",
        "article_number": "제307조",
        "article_title": "명예훼손",
        "content": (
            "① 공연히 사실을 적시하여 사람의 명예를 훼손한 자는 2년 이하의 징역이나 금고 "
            "또는 500만원 이하의 벌금에 처한다.\n"
            "② 공연히 허위의 사실을 적시하여 사람의 명예를 훼손한 자는 5년 이하의 징역, "
            "10년 이하의 자격정지 또는 1천만원 이하의 벌금에 처한다."
        ),
        "category_slug": "criminal",
        "keywords": "명예훼손,사실적시,허위사실,공연성",
        "source_url": "https://www.law.go.kr/법령/형법",
    },
    {
        "law_name": "민법",
        "article_number": "제750조",
        "article_title": "불법행위의 내용",
        "content": (
            "고의 또는 과실로 인한 위법행위로 타인에게 손해를 가한 자는 그 손해를 배상할 "
            "책임이 있다."
        ),
        "category_slug": "etc",
        "keywords": "불법행위,손해배상,고의,과실,위법",
        "source_url": "https://www.law.go.kr/법령/민법",
    },
]


PRECEDENTS = [
    {
        "case_number": "[임시] 2022다123456",
        "case_name": "임대차 보증금 반환 청구 사건",
        "court": "대법원",
        "judgment_date": date(2022, 6, 15),
        "summary": (
            "임차인의 원상복구 의무는 통상의 사용으로 인한 자연마모를 포함하지 않는다는 "
            "취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 임대차 종료 후 임차인의 원상복구 의무 범위가 쟁점이 되었다. "
            "법원은 통상적 사용으로 인한 자연마모는 임차인의 원상복구 의무 범위에 "
            "포함되지 않는다고 판단하였다."
        ),
        "category_slug": "housing",
        "keywords": "보증금,원상복구,자연마모,임차인,임대인",
        "result_type": "plaintiff_partial",
        "related_laws": [
            ("주택임대차보호법", "제7조"),
        ],
    },
    {
        "case_number": "[임시] 2023나98765",
        "case_name": "부당해고 구제 사건",
        "court": "서울중앙지방법원",
        "judgment_date": date(2023, 3, 22),
        "summary": (
            "절차적 정당성을 갖추지 못한 해고는 무효라는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 사용자가 징계위원회 절차를 거치지 않고 해고를 통보한 사안으로, "
            "법원은 해고에 정당한 이유가 있더라도 절차적 정당성을 결한 경우 해고가 "
            "무효임을 판시하였다."
        ),
        "category_slug": "labor",
        "keywords": "부당해고,절차,징계위원회,근로자",
        "result_type": "plaintiff_win",
        "related_laws": [
            ("근로기준법", "제23조"),
        ],
    },
    {
        "case_number": "[임시] 2021도54321",
        "case_name": "명예훼손 위법성 조각 사건",
        "court": "대법원",
        "judgment_date": date(2021, 11, 4),
        "summary": (
            "공익 목적이 인정되는 경우 명예훼손의 위법성이 조각될 수 있다는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 공적 사안에 관한 사실 적시가 명예훼손에 해당하는지가 쟁점이 되었다. "
            "법원은 공익 목적이 주된 동기이고 적시된 사실이 진실에 부합하는 경우 형법상 "
            "위법성이 조각된다고 판단하였다."
        ),
        "category_slug": "criminal",
        "keywords": "명예훼손,위법성조각,공익,사실적시",
        "result_type": "defendant_win",
        "related_laws": [
            ("형법", "제307조"),
        ],
    },
]


class Command(BaseCommand):
    help = "법령/판례 시연용 최소 데이터(Law 5건, Precedent 3건)를 등록(또는 갱신)한다."

    @transaction.atomic
    def handle(self, *args, **options):
        law_count = self._load_laws()
        prec_count, link_count = self._load_precedents()
        self.stdout.write(
            self.style.SUCCESS(
                f"Law {law_count}건, Precedent {prec_count}건 로드, 관계 {link_count}건 연결"
            )
        )

    def _load_laws(self) -> int:
        for entry in LAWS:
            cat = Category.objects.filter(slug=entry["category_slug"]).first()
            Law.objects.update_or_create(
                law_name=entry["law_name"],
                article_number=entry["article_number"],
                defaults={
                    "article_title": entry["article_title"],
                    "content": entry["content"],
                    "category": cat,
                    "keywords": entry["keywords"],
                    "source_url": entry["source_url"],
                    "is_active": True,
                },
            )
        return Law.objects.count()

    def _load_precedents(self) -> tuple[int, int]:
        link_count = 0
        for entry in PRECEDENTS:
            cat = Category.objects.filter(slug=entry["category_slug"]).first()
            prec, _ = Precedent.objects.update_or_create(
                case_number=entry["case_number"],
                court=entry["court"],
                defaults={
                    "case_name": entry["case_name"],
                    "judgment_date": entry["judgment_date"],
                    "summary": entry["summary"],
                    "content": entry["content"],
                    "category": cat,
                    "keywords": entry["keywords"],
                    "result_type": entry["result_type"],
                },
            )
            laws = []
            for law_name, article_number in entry["related_laws"]:
                law = Law.objects.filter(
                    law_name=law_name, article_number=article_number
                ).first()
                if law:
                    laws.append(law)
            prec.related_laws.set(laws)
            link_count += len(laws)
        return Precedent.objects.count(), link_count
