from django.core.management.base import BaseCommand

from apps.stories.models import Category


CATEGORIES = [
    ("housing", "전세/월세", "전세, 월세, 보증금, 임대차 관련 분쟁"),
    ("labor", "직장/노동", "임금, 해고, 근로계약, 직장 내 괴롭힘 관련"),
    ("consumer", "소비자 분쟁", "환불, 교환, 계약 해지, 온라인 쇼핑 분쟁"),
    ("family", "이혼/가족", "이혼, 양육권, 상속, 가족 관계 분쟁"),
    ("traffic", "교통사고", "자동차 사고, 보험 처리, 과실 비율"),
    ("criminal", "형사", "고소/고발, 형사 절차, 피해자 권리"),
    ("realestate", "부동산 매매", "부동산 매매 계약, 등기, 명도 분쟁"),
    ("debt", "채권/채무", "대여금, 보증, 채권 추심"),
    ("etc", "기타", "위 분류에 해당하지 않는 기타 분쟁"),
]


class Command(BaseCommand):
    help = "분쟁 카테고리 9개를 등록(또는 갱신)한다."

    def handle(self, *args, **options):
        for order, (slug, name, desc) in enumerate(CATEGORIES, start=1):
            Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "order": order, "description": desc},
            )
        count = Category.objects.count()
        self.stdout.write(self.style.SUCCESS(f"{count}개 카테고리 로드 완료"))
