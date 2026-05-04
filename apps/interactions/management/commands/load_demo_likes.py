"""인기글 시연용 좋아요 폭탄 시드.

ghost 사용자 150명 일괄 생성 (anon_001~anon_150) + 사연마다 view_count 기반
좋아요 분배 (인기 후보 100~250, 일반 30~100, 비인기 5~30, 거의 안 본 0~5).

재실행 안전: 기존 ghost 사용자의 좋아요만 wipe 후 재시드 (실 사용자 좋아요 보존).
"""
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.interactions.models import Like
from apps.stories.models import Story


User = get_user_model()
GHOST_PREFIX = "anon_"
GHOST_COUNT = 250  # 인기 1위가 200+ 좋아요 받을 수 있게 충분히


class Command(BaseCommand):
    help = "인기글 시연용 좋아요 폭탄 시드 (ghost 150명 + 사연별 분배)."

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)  # 재현성

        # 1) ghost 사용자 150명 bulk_create (이미 있으면 skip)
        existing_ghost_usernames = set(
            User.objects.filter(username__startswith=GHOST_PREFIX)
            .values_list("username", flat=True)
        )
        to_create = []
        for i in range(1, GHOST_COUNT + 1):
            uname = f"{GHOST_PREFIX}{i:03d}"
            if uname in existing_ghost_usernames:
                continue
            u = User(
                username=uname,
                email=f"{uname}@munbeop.local",
                nickname=f"익명{i:03d}",
                is_active=True,
            )
            u.set_unusable_password()
            to_create.append(u)
        if to_create:
            User.objects.bulk_create(to_create)
        self.stdout.write(f"  ghost 사용자: 신규 {len(to_create)}명 / 전체 {User.objects.filter(username__startswith=GHOST_PREFIX).count()}명")

        ghost_users = list(
            User.objects.filter(username__startswith=GHOST_PREFIX).order_by("id")
        )
        ghost_user_ids = [u.id for u in ghost_users]

        # 2) ghost 좋아요 wipe (실 사용자 좋아요 보존)
        wiped, _ = Like.objects.filter(
            target_type="story", user_id__in=ghost_user_ids
        ).delete()
        self.stdout.write(f"  ghost 기존 좋아요 wipe: {wiped}건")

        # 3) view_count 기반 rank별 단조 감소 분배
        # 1위 220 → 2위 200 → 3위 180 ... 점차 줄어들어 차이가 명확히 보이게
        stories = list(Story.objects.order_by("-view_count"))
        bulk_likes = []
        for rank, s in enumerate(stories, start=1):
            v = s.view_count or 0
            if rank <= 10:
                # Top 10: 220 → 200 → 180 → 160 → 140 → 125 → 110 → 95 → 80 → 65
                base = max(220 - (rank - 1) * 18, 65)
                # 2~5 정도 가벼운 노이즈로 자연스러움
                target = base + random.randint(-4, 4)
            elif rank <= 25 and v >= 5:
                # 중위: 60 → 20 점차 감소 + 노이즈
                base = max(60 - (rank - 11) * 3, 20)
                target = base + random.randint(-5, 5)
            elif v >= 2:
                # 하위: 5~20 분포
                target = random.randint(5, 20)
            else:
                target = random.randint(0, 5)
            target = max(0, min(target, len(ghost_user_ids)))
            if target == 0:
                continue
            chosen = random.sample(ghost_user_ids, target)
            for uid in chosen:
                bulk_likes.append(Like(
                    user_id=uid, target_type="story", target_id=s.id
                ))
        Like.objects.bulk_create(bulk_likes, ignore_conflicts=True)
        total_story_likes = Like.objects.filter(target_type="story").count()
        self.stdout.write(
            self.style.SUCCESS(
                f"  좋아요 폭탄 시드: {len(bulk_likes)}건 / "
                f"전체 story like = {total_story_likes}건"
            )
        )
