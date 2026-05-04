"""댓글/좋아요/북마크 시연용 시드 (재실행 안전).

전문가 톤 / 비전문가 공감 / 경험담 세 결을 섞어 커뮤니티 분위기를 살린다.
- testuser, testuser2 외에 lawhelper(법률 도움), survivor(경험자) 두 캐릭터
- 45건 사연 중 시연 핵심 사연(카테고리당 1~2개)에 댓글 + 일부에 베스트 댓글 (좋아요 N개) + 신고 흐름
- 일부 댓글에 대댓글로 답변 흐름 표현

⚠️ 단정적 자문 금지선: "당신은 ~해야 합니다" 표현 X.
"참고로 ~ 절차가 있어요", "저는 ~로 해결했어요" 톤.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.interactions.models import Bookmark, Comment, Like, Report
from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story


User = get_user_model()


COMMUNITY_USERS = [
    {"username": "lawhelper", "email": "lawhelper@munbeop.local",
     "nickname": "도움이", "password": "lawhelp1234"},
    {"username": "survivor", "email": "survivor@munbeop.local",
     "nickname": "겪어본사람", "password": "survive1234"},
]


# (story_title_keyword, author, content, marker, reply_to_marker)
# story_title_keyword로 사연을 찾음 (id 의존 X — 재시드 안전)
COMMENTS = [
    # === housing 시리즈 ===
    ("전세 만기 두 달", "lawhelper",
     "참고로 만기 1개월 전까지 임대인이 갱신 거절·조건 변경 통지 안 하면 묵시적 갱신이 "
     "성립합니다. 연락두절 자체로 임차인이 불리해지진 않으니 카톡·문자 기록은 모두 "
     "보존해두세요.", "h1", None),
    ("전세 만기 두 달", "survivor",
     "저도 같은 상황 겪었는데 내용증명 한 번 보내니까 그제서야 연락 왔어요. 우체국에서 "
     "쉽게 보낼 수 있고 비용 5천원 안 됩니다.", None, "h1"),
    ("전세 만기 두 달", "testuser",
     "이사 못 가는 상황이 생기면 임차권등기명령부터 신청하세요. 보증금 안 받고 이사 가도 "
     "대항력·우선변제권 유지됩니다.", None, None),

    ("월세 보증금에서 도배", "lawhelper",
     "통상의 마모와 자연 노후화는 임차인 부담이 아닙니다. 입주 시 사진이 없어도 "
     "출장비 영수증, 도배지 견적서 등을 요구하면 부풀린 금액 확인 가능해요.", None, None),
    ("월세 보증금에서 도배", "survivor",
     "저는 같은 케이스에서 한국소비자원 분쟁조정으로 80% 환수받았어요. 비용도 "
     "거의 안 들고요.", None, None),

    ("재계약 시 집주인이 일방적으로", "lawhelper",
     "주택임대차보호법상 임대료 인상은 5%를 초과할 수 없어요. 5% 초과 요구는 "
     "거부해도 됩니다. 거부 후에도 임대인이 계약 해지 통보하면 부당한 거절이라 "
     "묵시적 갱신 적용됩니다.", "h2", None),
    ("재계약 시 집주인이 일방적으로", "testuser2",
     "5% 룰은 정말 든든한 보호망이에요. 저도 작년에 동일하게 거부했고 그대로 "
     "기존 임대료로 갱신했습니다.", None, "h2"),

    ("전세사기 의심", "lawhelper",
     "근저당이 시세의 70% 넘으면 위험 신호입니다. 전세보증보험(HUG, SGI) 가입 가능 여부도 "
     "사전에 확인하시고, 불가능하면 계약 다시 생각하세요.", None, None),

    # === labor 시리즈 ===
    ("수습 3개월 끝나고", "lawhelper",
     "수습 기간이라도 정당한 사유 없는 본채용 거부는 부당해고에 해당할 수 있습니다. "
     "평가 기준이 사전 공개되지 않았다면 절차적 정당성도 결여됐다고 볼 여지가 있어요.",
     "l1", None),
    ("수습 3개월 끝나고", "survivor",
     "저도 비슷하게 수습 종료 통보받고 노동위원회 갔는데, 평가서 자료를 회사가 "
     "제대로 못 내서 제 손 들어줬습니다. 3개월 이내가 부당해고 구제신청 기한이니 "
     "빠르게 움직이세요.", None, "l1"),
    ("수습 3개월 끝나고", "testuser",
     "노무사 무료 상담도 활용해보세요. 노동권익센터(서울/경기 등)에서 상담 도와줍니다.",
     None, None),

    ("주말 출근 강요", "lawhelper",
     "연봉제라도 법정수당은 별도 지급 의무가 있습니다(포괄임금제 약정이 명확한 경우 "
     "예외). 노동청 진정으로 충분히 받을 수 있고, 진정 자체에 비용 안 듭니다.",
     None, None),
    ("주말 출근 강요", "survivor",
     "저는 카톡으로 주말 출근 지시받은 캡처본 챙겨서 진정 넣었어요. 6개월치 미지급 수당 "
     "다 받았습니다.", None, None),

    ("직장 내 괴롭힘 신고", "lawhelper",
     "근로기준법 제76조의3에 따라 직장 내 괴롭힘 신고자에 대한 불리한 처우는 "
     "금지됩니다. 따돌림도 정황 증거(메신저 배제, 회의 미참여 통보 등)로 입증 "
     "가능하면 같은 조항 적용됩니다.", None, None),

    # === consumer 시리즈 ===
    ("중고거래 사기", "lawhelper",
     "송금 직후 신고하면 지급정지 조치가 가능합니다. 사기이용계좌 신고는 금융감독원 "
     "1332, 경찰청 사이버수사대 모두 접수 가능해요. 빠를수록 회수 가능성이 높습니다.",
     "c1", None),
    ("중고거래 사기", "survivor",
     "저는 100만원 사기당했는데 신고 30분 만에 지급정지로 80만원 회수했어요. "
     "더치트 같은 사기 조회 사이트에 미리 계좌번호 검색하는 습관 들이세요.",
     None, "c1"),

    ("헬스장 6개월 결제", "lawhelper",
     "할부 거래라면 신용카드사 차지백(이의 제기) 신청 가능합니다. 폐업 사실 입증 "
     "(폐업 신고 자료, 매장 폐쇄 사진)을 첨부하면 잔여 기간만큼 환불됩니다.", None, None),
    ("헬스장 6개월 결제", "testuser",
     "한국소비자원 1372 소비자 상담도 함께 이용해보세요. 무료 분쟁 조정 진행됩니다.",
     None, None),

    ("온라인 강의 환불", "lawhelper",
     "전자상거래법상 디지털 콘텐츠도 일정 조건 하에 청약철회 가능합니다. '수강 시작 "
     "시 환불 불가' 약관은 약관규제법 제6조의 불공정약관으로 무효 소지 큽니다. "
     "소비자분쟁조정위 신청 권장.", None, None),

    # === family 시리즈 ===
    ("이혼 후 양육비 약속", "lawhelper",
     "양육비 이행관리원 외에 가정법원에 양육비 직접지급명령(전 배우자의 회사 급여에서 "
     "공제)을 신청할 수 있어요. 미이행 시 감치까지 가능합니다.", "f1", None),
    ("이혼 후 양육비 약속", "survivor",
     "저는 직접지급명령 신청 후 두 달 만에 정상 입금되기 시작했어요. 회사도 알게 되니 "
     "전 배우자가 빠르게 움직이더라고요.", None, "f1"),
    ("이혼 후 양육비 약속", "testuser2",
     "양육비 미지급은 신상 공개 제도(배드파더스 같은 공익 사이트)도 있긴 하지만 "
     "법적 절차부터 밟는 게 안전합니다.", None, None),

    ("재산분할 협의 중", "lawhelper",
     "재산분할 회피 목적의 처분은 사해행위 취소 소송으로 되돌릴 수 있습니다. "
     "다만 가까운 친족과의 거래라도 거래 시점·대가성 등 입증 자료가 핵심이에요. "
     "가압류부터 빠르게 신청하시는 게 좋습니다.", None, None),

    ("이혼 시 친권과 양육권 분리", "lawhelper",
     "친권과 양육권 분리는 협의로 가능하지만, 실무에서는 분쟁 소지가 커서 보통 같이 "
     "갖는 걸 권장합니다. 분리 시 학교·의료 등 결정권 다툼이 생길 수 있어요.",
     None, None),

    # === traffic 시리즈 ===
    ("우회전 사고", "lawhelper",
     "보행자 신호가 명확히 빨간불이었다면 보행자 과실이 인정될 수 있습니다. "
     "블랙박스 영상을 손해보험협회 분쟁심의위원회에 제출해 과실비율 재산정 신청 "
     "가능해요.", "t1", None),
    ("우회전 사고", "survivor",
     "저는 블랙박스에서 신호등 잘 안 보였는데, 인근 CCTV(편의점) 보존 요청해서 "
     "과실 비율 뒤집었습니다. 사고 직후 빠르게 움직여야 CCTV가 살아있어요.",
     None, "t1"),
    ("우회전 사고", "testuser",
     "보험사가 100% 운전자 과실로 가는 건 흔한 1차 판단인데, 분쟁심의위까지 가면 "
     "조정될 가능성이 꽤 있습니다.", None, None),

    ("주차장 후진 사고", "lawhelper",
     "비접촉 사고도 인과관계가 입증되면 책임이 인정될 수 있지만, 실제로는 입증이 "
     "어려워 다툴 여지가 큽니다. 주변 CCTV·블랙박스 다 모으세요.", None, None),

    ("음주운전 차량에 추돌", "lawhelper",
     "음주운전은 형사 처벌과 별개로 보험에서 사고부담금이 가중되고, 위자료도 "
     "통상보다 높게 산정됩니다. 보험사 제시안만 보지 마시고 한국교통연구원 자료 등을 "
     "참고해 협상하세요.", None, None),

    # === criminal 시리즈 ===
    ("전 연인이 SNS", "lawhelper",
     "사실 적시도 명예훼손이 됩니다(형법 제307조 제1항). 사생활 노출은 별도로 "
     "성폭력처벌법 또는 정보통신망법상 명예훼손 처벌 가능. 캡처와 게시 시점 기록 "
     "남겨두세요.", "cr1", None),
    ("전 연인이 SNS", "survivor",
     "저는 SNS 신고 + 경찰 사이버수사대 동시 신고로 게시물 빠르게 내렸어요. "
     "경찰 신고가 SNS 운영사 대응을 빠르게 만듭니다.", None, "cr1"),
    ("전 연인이 SNS", "testuser",
     "변호사 통한 가처분(게시 금지)도 빠른 효과 있어요. 비용은 들지만 즉시 정지가 "
     "필요하면 고려해보세요.", None, None),

    ("보이스피싱으로 600만원", "lawhelper",
     "전기통신금융사기특별법상 30분 내 신고 시 지급정지 조치가 가능합니다. "
     "지급정지된 금액은 환급 절차로 돌려받을 수 있어요. 경찰 신고와 별개로 "
     "송금 은행에도 즉시 통보 필수.", None, None),

    ("회사 동료가 제 SNS", "lawhelper",
     "비공개 글의 무단 캡처·공개는 정보통신망법상 명예훼손 또는 사생활 침해에 해당할 "
     "수 있어요. 해당 단톡방 화면, 캡처 시점 기록을 모두 보존하세요.", None, None),

    # === realestate 시리즈 ===
    ("아파트 매매 — 잔금 직전", "lawhelper",
     "가압류는 매수인이 알 수 없었던 사정 변화이므로 계약 해제 사유가 될 수 있습니다. "
     "다만 매도인이 즉시 해제 시 손해배상 청구 가능. 계약 해제 vs 가압류 해소 후 "
     "잔금 중 어느 쪽이 유리한지 변호사 상담 권장.", "re1", None),
    ("아파트 매매 — 잔금 직전", "testuser2",
     "저는 비슷한 케이스에서 잔금 일정 미루고 매도인이 가압류 해소할 때까지 보증금 "
     "공탁하는 방식으로 갔어요. 확실한 보호 장치 필요해요.", None, "re1"),

    ("오피스텔 매매 — 임차인", "lawhelper",
     "매도인이 명도 책임을 부담하는 게 일반적입니다. 매매계약서 명도 조항 확인하시고, "
     "조항이 없어도 계약상 의무 위반으로 해제·손해배상 청구 가능합니다.", None, None),

    # === debt 시리즈 ===
    ("보증 잘못 서서", "lawhelper",
     "보증채무도 일반 채권 시효 10년 적용입니다. 다만 채권자가 청구·소송 등 시효 중단 "
     "행위를 하면 시효가 갱신돼요. 청구 받으신 시점이 시효 진행 중이었는지 확인 "
     "필요합니다.", "d1", None),
    ("보증 잘못 서서", "survivor",
     "저는 보증 책임 시효 항변으로 일부 면책됐어요. 시효 중단 사실 입증은 채권자가 "
     "해야 합니다.", None, "d1"),

    ("사채업자한테 협박", "lawhelper",
     "법정 최고 이자율(연 20%) 초과분은 무효이고 갚을 의무 없어요. 협박은 별도 "
     "형사 처벌(공갈죄)이고, 등록 안 된 대부업자라면 미등록 대부업으로 추가 처벌 "
     "대상입니다. 통화 녹음 보존하세요.", None, None),

    ("회생 절차 후 가족", "lawhelper",
     "회생 절차의 면책 효력은 채무자 본인에 한정됩니다. 보증인의 보증채무는 별도로 "
     "남고요. 부모님 보증 부분은 주채무 이행 가능 여부와 별개로 다툴 수 있는 항변 "
     "사유가 있는지 검토 필요합니다.", None, None),

    # === etc 시리즈 ===
    ("층간소음 분쟁", "lawhelper",
     "환경분쟁조정위(중앙·지방)에 신청 가능하고, 조정 결과는 합의 시 법적 효력이 "
     "있습니다. 직접 민사로 가도 되지만 비용·시간 많이 들어 우선 조정 권장.",
     None, None),

    ("반려견이 옆집", "lawhelper",
     "동물 점유자 책임(민법 제759조)에 따라 견주가 손해를 배상해야 합니다. 치료비는 "
     "당연히 인정되고, 정신적 위자료는 일반적으로 소액(20만원 내외) 인정 사례가 "
     "많습니다.", "p1", None),
    # === 작성자 뱃지 시연용 — testuser2가 자기 사연(공방)에 댓글 답변 ===
    ("집에서 운영한 공방", "testuser2",
     "댓글 감사합니다! 일단 환경분쟁조정위 문의해보고 결과 공유드릴게요.", None, None),
    # 추가 답글 예시 (반려견 사연에 작성자 답변)
    ("반려견이 옆집", "testuser",
     "감사합니다. 동물 점유자 책임 조항으로 정리하면 협상 잘 풀릴 것 같아요.",
     None, "p1"),
]


# 베스트 댓글로 만들기 위한 좋아요 시드
# (story_title_keyword, comment_marker_or_first10chars, like_user_username_list)
LIKE_SEEDS = [
    # h1: 전세 만기 두 달 lawhelper 댓글 — 좋아요 4개 (베스트)
    ("전세 만기 두 달", "참고로 만기 1개월 전까지", ["testuser", "testuser2", "survivor", "demo_helper"]),
    # l1: 수습 3개월 lawhelper — 좋아요 3개 (베스트)
    ("수습 3개월 끝나고", "수습 기간이라도 정당한", ["testuser2", "survivor", "demo_helper"]),
    # cr1: 전 연인 SNS lawhelper — 좋아요 5개 (베스트, 가장 많이)
    ("전 연인이 SNS", "사실 적시도 명예훼손", ["testuser", "testuser2", "survivor", "demo_helper", "demo_helper2"]),
]


# 신고 시드 — 신고 누적 자동 삭제 시연용
# 가짜 댓글 1건 작성 후 3건 신고 → 자동 삭제 발동
REPORT_DEMO = {
    "story_title_keyword": "층간소음 분쟁",
    "spam_author": "demo_helper",
    "spam_content": "광고: 신비한 만능 약 판매 중! 카톡 문의 ★★★ (이 댓글은 시연용 신고 대상)",
    "reporters": ["testuser", "testuser2", "survivor"],
    "reasons": ["spam", "spam", "spam"],
}


class Command(BaseCommand):
    help = "댓글/좋아요/북마크 + 베스트 댓글 + 신고 시연 데이터 시드 (재실행 안전)."

    def handle(self, *args, **options):
        # 1) 추가 사용자 (lawhelper, survivor) + 좋아요 시드용 demo 사용자 2명
        all_users_spec = COMMUNITY_USERS + [
            {"username": "demo_helper", "email": "demo_helper@munbeop.local",
             "nickname": "도움주는1", "password": "demoH1234"},
            {"username": "demo_helper2", "email": "demo_helper2@munbeop.local",
             "nickname": "도움주는2", "password": "demoH1234"},
        ]
        for spec in all_users_spec:
            u, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={"email": spec["email"], "nickname": spec["nickname"], "is_active": True},
            )
            if created or not u.has_usable_password():
                u.set_password(spec["password"])
                u.save()

        # 2) 댓글
        marker_to_id = {}
        created_count = 0
        for story_kw, username, content, marker, reply_to in COMMENTS:
            try:
                user = User.objects.get(username=username)
                story = Story.objects.filter(title__icontains=story_kw).first()
                if not story:
                    continue
            except User.DoesNotExist:
                continue

            parent = None
            if reply_to:
                pid = marker_to_id.get(reply_to)
                if pid:
                    parent = Comment.objects.filter(id=pid).first()

            comment, created = Comment.objects.get_or_create(
                user=user, story=story, parent=parent, content=content,
            )
            if marker:
                marker_to_id[marker] = comment.id
            if created:
                created_count += 1

        # 3) 좋아요 (베스트 댓글 만들기)
        for story_kw, content_prefix, liker_usernames in LIKE_SEEDS:
            story = Story.objects.filter(title__icontains=story_kw).first()
            if not story:
                continue
            comment = Comment.objects.filter(
                story=story, content__startswith=content_prefix
            ).first()
            if not comment:
                continue
            for uname in liker_usernames:
                liker = User.objects.filter(username=uname).first()
                if liker:
                    Like.objects.get_or_create(
                        user=liker, target_type="comment", target_id=comment.id
                    )

        # 4) 신고 시연 데이터 — 광고성 댓글 1건 + 신고 3건 → 자동 삭제 발동
        spam_user = User.objects.filter(username=REPORT_DEMO["spam_author"]).first()
        target_story = Story.objects.filter(
            title__icontains=REPORT_DEMO["story_title_keyword"]
        ).first()
        if spam_user and target_story:
            spam_comment, _ = Comment.objects.get_or_create(
                user=spam_user, story=target_story, parent=None,
                content=REPORT_DEMO["spam_content"],
            )
            for uname, reason in zip(REPORT_DEMO["reporters"], REPORT_DEMO["reasons"]):
                reporter = User.objects.filter(username=uname).first()
                if reporter and reporter.id != spam_comment.user_id:
                    Report.objects.get_or_create(
                        user=reporter, comment=spam_comment,
                        defaults={"reason": reason, "detail": ""},
                    )
            # 임계값 도달 → 자동 삭제
            if spam_comment.reports.count() >= Report.REPORT_THRESHOLD and not spam_comment.is_deleted:
                spam_comment.soft_delete(reason="report")

        # 5) 기존 좋아요 / 북마크 시드 (스토리 좋아요 + 북마크)
        testuser = User.objects.get(username="testuser")
        # 첫 번째 labor 사연 좋아요
        labor_story = Story.objects.filter(category__slug="labor").order_by("-view_count").first()
        if labor_story:
            Like.objects.get_or_create(
                user=testuser, target_type="story", target_id=labor_story.id
            )
        # Law 1 / Precedent 1 북마크
        law1 = Law.objects.filter(id=1).first()
        prec1 = Precedent.objects.filter(id=1).first()
        if law1:
            Bookmark.objects.get_or_create(
                user=testuser, target_type="law", target_id=law1.id
            )
        if prec1:
            Bookmark.objects.get_or_create(
                user=testuser, target_type="precedent", target_id=prec1.id
            )

        comment_total = Comment.all_objects.count()
        comment_active = Comment.objects.count()
        like_total = Like.objects.count()
        bookmark_total = Bookmark.objects.count()
        report_total = Report.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"댓글 시드: 신규 {created_count}건 / 전체 {comment_total} (active {comment_active}) / "
                f"좋아요 {like_total} / 북마크 {bookmark_total} / 신고 {report_total} / "
                f"커뮤니티 사용자 {len(all_users_spec)}명"
            )
        )
