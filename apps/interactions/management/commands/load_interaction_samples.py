"""STEP 6 UI 시연 시 댓글/좋아요/북마크 빈 화면 방지용 최소 시드.

생성 항목:
- testuser: id=1 사연에 댓글 1개
- testuser2: 위 댓글에 대댓글 1개
- testuser: id=62 (해고 사연)에 좋아요
- testuser: Law id=1, Precedent id=1 북마크
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.interactions.models import Bookmark, Comment, Like
from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story


User = get_user_model()


class Command(BaseCommand):
    help = "댓글/좋아요/북마크 시연용 최소 데이터 시드 (재실행 안전)."

    def handle(self, *args, **options):
        testuser = User.objects.get(username="testuser")
        testuser2 = User.objects.get(username="testuser2")

        story1 = Story.objects.get(id=1)
        story_labor = Story.objects.get(id=62)
        law1 = Law.objects.get(id=1)
        prec1 = Precedent.objects.get(id=1)

        # 1) testuser → story 1 에 댓글
        root_content = (
            "저도 비슷한 상황이에요. 보증금 못 받아서 골치 아팠는데 결국 임차권등기명령부터 "
            "신청했습니다. 도움 되셨으면 해서 댓글 남깁니다."
        )
        root_comment, root_created = Comment.objects.get_or_create(
            user=testuser,
            story=story1,
            parent=None,
            content=root_content,
        )

        # 2) testuser2 → 위 댓글에 대댓글
        reply_content = (
            "저는 내용증명부터 보내고 그래도 안 줘서 소액심판으로 갔습니다. 내용증명 단계에서 "
            "주는 경우도 있어요."
        )
        reply, reply_created = Comment.objects.get_or_create(
            user=testuser2,
            story=story1,
            parent=root_comment,
            content=reply_content,
        )

        # 3) testuser → story 62 좋아요
        like, like_created = Like.objects.get_or_create(
            user=testuser, target_type="story", target_id=story_labor.id
        )

        # 4) testuser → Law 1 / Precedent 1 북마크
        bm_law, bm_law_created = Bookmark.objects.get_or_create(
            user=testuser, target_type="law", target_id=law1.id
        )
        bm_prec, bm_prec_created = Bookmark.objects.get_or_create(
            user=testuser, target_type="precedent", target_id=prec1.id
        )

        self.stdout.write(
            self.style.SUCCESS(
                "댓글 2건 (root id={}, reply id={}), 좋아요 1건 (story id={}), 북마크 2건 (law id={}, precedent id={})".format(
                    root_comment.id, reply.id, story_labor.id, bm_law.id, bm_prec.id
                )
            )
        )
