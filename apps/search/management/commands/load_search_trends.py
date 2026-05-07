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


# (query, count) — count만큼 시드. Top 10이 위젯에 노출 (단조 감소).
SEEDS = [
    # === Top 10 (위젯 노출) ===
    ("전세 보증금 못 받고 있어요", 32),
    ("부당해고 노동위원회 신청", 27),
    ("이혼 양육비 산정 기준", 23),
    ("아파트 매매 계약 일방 해제", 21),
    ("교통사고 과실비율 이의제기", 18),
    ("명예훼손 고소 절차", 16),
    ("보이스피싱 피해금 환급", 14),
    ("월세 보증금 도배 공제", 12),
    ("층간소음 분쟁조정", 11),
    ("카톡으로 빌려준 돈 회수", 10),
    # === 11~30위 (데이터 풍부 — 검색 시 매칭 개선) ===
    ("중고거래 사기 신고", 9),
    ("임대차 분쟁 조정", 8),
    ("주차장 후진 사고", 8),
    ("산업재해 인정 기준", 7),
    ("음주운전 합의금", 7),
    ("사실혼 재산분할", 6),
    ("재택근무 산재", 6),
    ("회사 사정 해고 정당성", 5),
    ("층간소음 보복", 5),
    ("주말 출근 수당", 5),
    ("전세사기 보증보험", 4),
    ("양육비 미지급 강제집행", 4),
    ("매매계약 가압류", 4),
    ("사채 이자율 상한", 3),
    ("동업 자금 횡령", 3),
    ("재산분할 사해행위", 3),
    ("개인회생 보증인", 3),
    ("유튜브 영상 무단도용", 2),
    ("반려견 물림 사고", 2),
    ("건물주 무단 출입", 2),
    ("공방 영업 민원", 1),
    ("킥보드 사고 보험", 1),
    ("자전거 보행자 사고", 1),
    ("재개발 입주권 자격", 1),
    ("OTT 구독 해지", 1),
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
