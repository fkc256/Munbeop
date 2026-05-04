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
        "keywords": "불법행위,손해배상,손해,배상,고의,과실,위법,누수,침해,청구",
        "source_url": "https://www.law.go.kr/법령/민법",
    },
    # === STEP 8 (사연-법령 매칭 빈 카테고리 보강 — 2026-05-01) ===
    {
        "law_name": "전자상거래 등에서의 소비자보호에 관한 법률",
        "article_number": "제17조",
        "article_title": "청약철회 등",
        "content": (
            "통신판매의 방법으로 재화등의 구매에 관한 계약을 체결한 소비자는 다음 각 호의 "
            "기간(거래당사자가 다음 각 호의 기간보다 긴 기간으로 약정한 경우에는 그 기간) "
            "이내에 해당 계약에 관한 청약철회등을 할 수 있다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "consumer",
        "keywords": "청약철회,환불,통신판매,7일,온라인쇼핑",
        "source_url": "https://www.law.go.kr/법령/전자상거래등에서의소비자보호에관한법률",
    },
    {
        "law_name": "약관의 규제에 관한 법률",
        "article_number": "제6조",
        "article_title": "일반원칙",
        "content": (
            "신의성실의 원칙을 위반하여 공정을 잃은 약관 조항은 무효로 한다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "consumer",
        "keywords": "약관,불공정,무효,신의성실,소비자",
        "source_url": "https://www.law.go.kr/법령/약관의규제에관한법률",
    },
    {
        "law_name": "민법",
        "article_number": "제837조",
        "article_title": "이혼과 자의 양육책임",
        "content": (
            "이혼하는 부모는 협의에 의하여 자(子)의 양육에 관한 사항을 정한다. 협의가 "
            "이루어지지 아니하거나 협의할 수 없는 때에는 가정법원이 직권으로 또는 당사자의 "
            "청구에 따라 정한다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "family",
        "keywords": "양육비,양육권,이혼,협의,가정법원",
        "source_url": "https://www.law.go.kr/법령/민법",
    },
    {
        "law_name": "민법",
        "article_number": "제839조의2",
        "article_title": "재산분할청구권",
        "content": (
            "협의상 이혼한 자의 일방은 다른 일방에 대하여 재산분할을 청구할 수 있다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "family",
        "keywords": "재산분할,이혼,협의,청구권",
        "source_url": "https://www.law.go.kr/법령/민법",
    },
    {
        "law_name": "자동차손해배상 보장법",
        "article_number": "제3조",
        "article_title": "자동차손해배상책임",
        "content": (
            "자기를 위하여 자동차를 운행하는 자는 그 운행으로 다른 사람을 사망하게 하거나 "
            "부상하게 한 경우에는 그 손해를 배상할 책임을 진다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "traffic",
        "keywords": "운행자책임,교통사고,손해배상,과실",
        "source_url": "https://www.law.go.kr/법령/자동차손해배상보장법",
    },
    {
        "law_name": "도로교통법",
        "article_number": "제54조",
        "article_title": "사고발생 시의 조치",
        "content": (
            "차 또는 노면전차의 운전 등 교통으로 인하여 사람을 사상하거나 물건을 손괴한 "
            "경우에는 그 차 또는 노면전차의 운전자나 그 밖의 승무원은 즉시 정차하여 사상자를 "
            "구호하는 등 필요한 조치를 하여야 한다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "traffic",
        "keywords": "교통사고,사고조치,운전자,구호의무",
        "source_url": "https://www.law.go.kr/법령/도로교통법",
    },
    {
        "law_name": "민법",
        "article_number": "제565조",
        "article_title": "해약금",
        "content": (
            "매매의 당사자 일방이 계약 당시에 금전 기타 물건을 계약금, 보증금 등의 명목으로 "
            "상대방에게 교부한 때에는 당사자간에 다른 약정이 없는 한 당사자의 일방이 이행에 "
            "착수할 때까지 교부자는 이를 포기하고 수령자는 그 배액을 상환하여 매매계약을 "
            "해제할 수 있다."
        ),
        "category_slug": "realestate",
        "keywords": "해약금,계약금,배액상환,매매계약,해제",
        "source_url": "https://www.law.go.kr/법령/민법",
    },
    {
        "law_name": "민법",
        "article_number": "제162조",
        "article_title": "채권, 재산권의 소멸시효",
        "content": (
            "① 채권은 10년간 행사하지 아니하면 소멸시효가 완성한다.\n"
            "(제1항만 발췌. 제2항(재산권 20년) 등은 source_url 참조)"
        ),
        "category_slug": "debt",
        "keywords": "소멸시효,채권,10년,차용,차용금,빌려준,카톡",
        "source_url": "https://www.law.go.kr/법령/민법",
    },
    {
        "law_name": "민법",
        "article_number": "제428조",
        "article_title": "보증채무의 내용",
        "content": (
            "① 보증인은 주채무자가 이행하지 아니하는 채무를 이행할 의무가 있다.\n"
            "(법조문 본문 일부 발췌 — 정확한 전문은 source_url 참조)"
        ),
        "category_slug": "debt",
        "keywords": "보증채무,주채무,이행의무,연대보증",
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
    # === STEP 8 (사연-법령 매칭 빈 카테고리 보강 — 2026-05-01) ===
    {
        "case_number": "[임시] 2022다112233",
        "case_name": "온라인 쇼핑몰 환불 거부 사건",
        "court": "서울중앙지방법원",
        "judgment_date": date(2022, 9, 8),
        "summary": (
            "통신판매업자가 청약철회 기간 내 환불 요청을 부당하게 거부한 경우 "
            "전자상거래법 위반에 해당한다는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 소비자가 배송 파손을 이유로 환불을 요청했으나 판매자가 '소비자 부주의'를 "
            "이유로 거부한 사안으로, 법원은 청약철회 기간 내 정당한 사유 없는 환불 거부는 "
            "위법하다고 판단하였다."
        ),
        "category_slug": "consumer",
        "keywords": "환불거부,청약철회,통신판매,소비자보호",
        "result_type": "plaintiff_win",
        "related_laws": [
            ("전자상거래 등에서의 소비자보호에 관한 법률", "제17조"),
        ],
    },
    {
        "case_number": "[임시] 2023느합3456",
        "case_name": "양육비 산정 기준 사건",
        "court": "서울가정법원",
        "judgment_date": date(2023, 5, 11),
        "summary": (
            "양육비 산정표는 합리적 기준이지만 양육의 구체적 사정을 종합 고려하여 "
            "조정할 수 있다는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 미성년 자녀의 양육비 액수가 쟁점이 된 가사사건으로, 가정법원은 "
            "양육비 산정표를 기준으로 하되 부모의 재산·소득, 자녀의 연령·교육환경 등을 "
            "종합하여 양육비를 정한다고 판시하였다."
        ),
        "category_slug": "family",
        "keywords": "양육비,산정표,이혼,가정법원,자녀",
        "result_type": "plaintiff_partial",
        "related_laws": [
            ("민법", "제837조"),
        ],
    },
    {
        "case_number": "[임시] 2022나445566",
        "case_name": "이면도로 신호 없는 사거리 사고 과실비율 사건",
        "court": "서울중앙지방법원",
        "judgment_date": date(2022, 11, 25),
        "summary": (
            "신호 없는 교차로에서 좌우 미확인 상태로 진입한 차량의 과실이 더 크게 "
            "인정될 수 있다는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 신호 없는 사거리에서 양 차량이 충돌한 사안으로, 법원은 좌우 안전을 "
            "확인하지 않고 진입한 차량의 과실이 더 크다고 판단하여 과실비율을 조정하였다."
        ),
        "category_slug": "traffic",
        "keywords": "교통사고,과실비율,이면도로,신호없는교차로,블랙박스",
        "result_type": "plaintiff_partial",
        "related_laws": [
            ("자동차손해배상 보장법", "제3조"),
        ],
    },
    {
        "case_number": "[임시] 2023가합7788",
        "case_name": "아파트 매매 일방 해제 통보 사건",
        "court": "서울중앙지방법원",
        "judgment_date": date(2023, 8, 17),
        "summary": (
            "매도인이 시세 상승을 이유로 일방 해제를 통보한 경우, 매수인은 계약 이행 "
            "강제 또는 손해배상을 선택할 수 있다는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 부동산 매매 계약 후 시세 상승으로 매도인이 일방 해제를 통보한 "
            "사안으로, 법원은 매수인이 이행이익 상실에 대한 손해배상을 청구할 수 있다고 "
            "판시하였다."
        ),
        "category_slug": "realestate",
        "keywords": "매매계약,일방해제,위약금,이행강제,부동산",
        "result_type": "plaintiff_win",
        "related_laws": [
            ("민법", "제565조"),
        ],
    },
    {
        "case_number": "[임시] 2021가소9876",
        "case_name": "카톡 메시지 차용 입증 사건",
        "court": "서울중앙지방법원",
        "judgment_date": date(2021, 7, 30),
        "summary": (
            "차용증 없이도 카카오톡 메시지와 계좌이체 내역으로 금전소비대차계약의 "
            "성립을 인정할 수 있다는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 차용증이 없고 카톡 메시지와 이체 내역만 있는 상황에서 금전소비대차의 "
            "성립이 다투어진 사안으로, 법원은 메시지 내용과 이체 정황을 종합해 채권 성립을 "
            "인정하였다."
        ),
        "category_slug": "debt",
        "keywords": "차용금,카카오톡,입증,소멸시효,금전소비대차",
        "result_type": "plaintiff_win",
        "related_laws": [
            ("민법", "제162조"),
        ],
    },
    {
        "case_number": "[임시] 2022가단55432",
        "case_name": "공동주택 누수 손해배상 사건",
        "court": "서울중앙지방법원",
        "judgment_date": date(2022, 4, 19),
        "summary": (
            "윗집 전유부분의 누수로 인한 아랫집 손해는 점유자가 제1차 책임을 지고, "
            "공용부분 결함은 관리주체가 책임을 진다는 취지의 판단."
        ),
        "content": (
            "[임시 본문 — STEP 8 이후 본격 적재 시 교체 예정]\n"
            "본 사건은 윗집의 배관 노후로 아랫집에 누수 피해가 발생한 사안으로, 법원은 "
            "전유부분 시설물의 점유자에게 1차적 손해배상 책임이 있다고 판단하였다."
        ),
        "category_slug": "etc",
        "keywords": "누수,손해배상,공동주택,점유자,불법행위",
        "result_type": "plaintiff_partial",
        "related_laws": [
            ("민법", "제750조"),
        ],
    },
]


class Command(BaseCommand):
    help = "법령/판례 시연용 데이터(Law 15건, Precedent 8건)를 등록(또는 갱신)한다."

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
