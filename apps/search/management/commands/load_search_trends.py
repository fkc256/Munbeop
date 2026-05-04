"""실시간 검색어 시드 — 시연 시 빈 화면 방지.

각 검색어마다 다양한 빈도 (1~12회)로 SearchQuery 레코드 생성.
시간은 최근 24시간 내 분산 (랭킹 자연스러움).
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.search.models import SearchQuery
from apps.search.utils import extract_keywords


# (query, count) — count만큼 시드
SEEDS = [
    ("전세 보증금 못 받고 있어요", 12),
    ("부당해고 노동위원회", 9),
    ("이혼 양육비 산정", 8),
    ("아파트 매매 계약 해제", 7),
    ("교통사고 과실비율", 7),
    ("명예훼손 신고", 6),
    ("보이스피싱 환급", 5),
    ("월세 보증금 환불", 5),
    ("층간소음", 4),
    ("카톡으로 빌려준 돈", 3),
    ("중고거래 사기", 3),
    ("산업재해 신청", 2),
    ("사실혼 재산분할", 2),
    ("재택근무 산재", 1),
    ("유튜브 저작권", 1),
]


class Command(BaseCommand):
    help = "실시간 검색어 시드 (재실행 시 기존 시드 wipe 후 재생성)."

    def handle(self, *args, **options):
        # 시연용 시드는 재실행 안전 위해 기존 SearchQuery 전체 wipe
        # (실서비스에선 삭제 X — 시연 데이터셋 한정 정책)
        wiped, _ = SearchQuery.objects.all().delete()
        now = timezone.now()
        created = 0
        for query, count in SEEDS:
            kws = extract_keywords(query)
            for _ in range(count):
                # 최근 24시간 내 랜덤 분산
                offset = timedelta(seconds=random.randint(60, 24 * 3600))
                created_at = now - offset
                obj = SearchQuery.objects.create(
                    query=query,
                    keywords=",".join(kws)[:500],
                )
                # auto_now_add 우회 — 임의 시점 부여
                SearchQuery.objects.filter(pk=obj.pk).update(created_at=created_at)
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"이전 시드 {wiped}건 wipe, 새 시드 {created}건 생성 (검색어 {len(SEEDS)}종)"
        ))
