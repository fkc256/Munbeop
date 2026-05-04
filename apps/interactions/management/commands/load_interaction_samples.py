"""댓글/좋아요/북마크 시연용 시드 (재실행 안전).

전문가 톤 / 비전문가 공감 / 경험담 세 결을 섞어 커뮤니티 분위기를 살린다.
- testuser, testuser2 외에 lawhelper(법률 도움), survivor(경험자) 두 캐릭터 추가
- 9개 시연 사연 모두에 댓글 2~3건씩
- 일부 댓글에 대댓글로 답변 흐름 표현

⚠️ 단정적 자문 금지선: "당신은 ~해야 합니다" 표현 X.
대신 "참고로 ~ 절차가 있어요", "저는 ~로 해결했어요" 톤.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.interactions.models import Bookmark, Comment, Like
from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story


User = get_user_model()


COMMUNITY_USERS = [
    {"username": "lawhelper", "email": "lawhelper@munbeop.local",
     "nickname": "도움이", "password": "lawhelp1234"},
    {"username": "survivor", "email": "survivor@munbeop.local",
     "nickname": "겪어본사람", "password": "survive1234"},
]


# (story_id, author_username, content, parent_marker, reply_to_marker)
# parent_marker가 set이면 그 댓글에 대댓글, marker는 임의 식별자
COMMENTS = [
    # === id=1 housing — 전세 보증금 반환 지연 ===
    (1, "testuser",
     "저도 비슷한 상황이에요. 보증금 못 받아서 골치 아팠는데 결국 임차권등기명령부터 "
     "신청했습니다. 도움 되셨으면 해서 댓글 남깁니다.",
     "h1", None),
    (1, "testuser2",
     "저는 내용증명부터 보내고 그래도 안 줘서 소액심판으로 갔습니다. 내용증명 단계에서 "
     "주는 경우도 있어요.",
     None, "h1"),
    (1, "lawhelper",
     "참고로 임차권등기명령은 임대차 종료 후 보증금을 돌려받지 못한 경우 신청할 수 있어요. "
     "주민등록을 옮기더라도 대항력·우선변제권이 유지된다는 점이 핵심입니다.",
     None, "h1"),
    (1, "survivor",
     "저는 1년 끌었어요. 지급명령 → 강제집행 순서로 갔는데, 처음부터 변호사 도움 받았으면 "
     "더 빨랐을 것 같습니다.",
     "h2", None),

    # === id=62 labor — 갑작스러운 해고 ===
    (62, "lawhelper",
     "근로기준법 제23조에 따라 정당한 이유 없는 해고는 부당해고에 해당할 수 있습니다. "
     "노동위원회에 부당해고 구제신청(해고일로부터 3개월 이내)이 가능하다는 점 참고하세요.",
     "l1", None),
    (62, "survivor",
     "저도 같은 상황 겪었어요. 회사 사정 핑계는 정리해고 요건(긴박한 경영상 필요 등)을 "
     "갖춰야 인정되는데, 그게 안 되면 부당해고로 다툴 수 있어요.",
     None, "l1"),
    (62, "testuser2",
     "서면통지 없는 해고는 그것 자체로 무효 사유가 될 수 있다고 들었어요. 통지서나 "
     "녹취 같은 증거 챙겨두세요.",
     None, None),

    # === id=63 consumer — 배송 파손 환불 거부 ===
    (63, "lawhelper",
     "전자상거래법상 통신판매로 산 물건은 7일 이내 청약철회가 가능합니다. 파손 사진과 "
     "박스 상태 사진을 함께 남겨두시고, 한국소비자원 1372 상담을 권장드립니다.",
     None, None),
    (63, "survivor",
     "저는 카드사 차지백 신청해서 환불받았어요. 판매자가 안 들어주면 결제수단 쪽으로 "
     "한번 알아보세요.",
     None, None),
    (63, "testuser",
     "받자마자 사진 찍어두신 게 잘하신 일이에요. 분쟁조정위에 그 자료 그대로 제출하면 "
     "통상 빠르게 처리되더라고요.",
     None, None),

    # === id=64 family — 양육비 산정 ===
    (64, "lawhelper",
     "서울가정법원 양육비 산정표를 기준으로 부모 합산소득과 자녀 연령을 대입하면 표준 "
     "양육비가 나옵니다. 협의 안 되면 가정법원 양육비 청구로 결정됩니다.",
     None, None),
    (64, "survivor",
     "저도 산정표 보고 협의 시도했는데 결국 법원 결정으로 갔어요. 한 번 정해도 사정이 "
     "바뀌면 양육비 변경심판 청구할 수 있어요.",
     None, None),

    # === id=65 traffic — 과실비율 ===
    (65, "lawhelper",
     "과실비율은 손해보험협회 「자동차사고 과실비율 인정기준」을 따릅니다. 보험사가 정한 "
     "비율이 부당하다면 금융감독원 분쟁조정 또는 소송으로 다툴 수 있어요.",
     None, None),
    (65, "testuser",
     "블랙박스 영상이 있으면 큰 무기예요. 손해보험협회 분쟁심의위원회에 영상 첨부해서 "
     "이의 제기 해보세요.",
     None, None),
    (65, "survivor",
     "저는 6:4에서 4:6으로 뒤집었어요. 영상에서 상대방 진입 속도, 좌우 미확인이 명확히 "
     "찍혀 있으면 가능합니다.",
     None, None),

    # === id=66 criminal — 명예훼손 ===
    (66, "lawhelper",
     "공연성(불특정 다수 인식 가능) + 사실 적시 + 명예 훼손 가능성, 세 요건이 인정되면 "
     "형법 제307조 명예훼손에 해당할 수 있습니다. 함께 들은 친구의 진술이 증거가 될 수 있어요.",
     None, None),
    (66, "survivor",
     "저는 친구 진술서 받고 카페 CCTV 보존 요청까지 해놓고 고소 진행했어요. 시간 지나면 "
     "CCTV가 사라지니 빠르게 움직이는 게 좋아요.",
     None, None),

    # === id=67 realestate — 매매 일방 해제 ===
    (67, "lawhelper",
     "민법 제565조 해약금 규정상 이행 착수 전이면 매도인은 계약금의 배액 상환으로 해제할 "
     "수 있습니다. 다만 매수인이 이미 이행에 착수한 단계라면 다툼 여지가 있어요.",
     "r1", None),
    (67, "testuser",
     "이사 준비도 다 하셨다니 이행착수로 인정될 가능성도 있겠네요. 해제 통보 받은 시점, "
     "이사 준비 정황 등 시간순으로 자료 정리해두세요.",
     None, "r1"),
    (67, "survivor",
     "저는 비슷한 케이스에서 이행이익 손해배상 청구로 갔습니다. 위약금만 받기보다 "
     "추가 청구도 가능한지 변호사에게 한 번 상담받아보세요.",
     None, None),

    # === id=68 debt — 카톡 차용 ===
    (68, "lawhelper",
     "차용증이 없어도 카카오톡 메시지와 계좌이체 내역으로 금전소비대차계약의 성립을 "
     "입증할 수 있습니다. 민사상 채권 소멸시효는 10년이라 시효는 아직 충분합니다.",
     None, None),
    (68, "survivor",
     "저는 카톡 백업본을 노트북으로 옮겨서 PDF로 출력해서 증거로 제출했어요. 화면 캡처 "
     "말고 백업본이 더 확실해요.",
     None, None),
    (68, "testuser",
     "지급명령 신청도 고려해보세요. 상대방이 이의 신청 안 하면 그대로 확정돼서 강제집행 "
     "가능합니다.",
     None, None),

    # === id=69 etc — 윗집 누수 ===
    (69, "lawhelper",
     "전유부분(윗집 내부) 누수는 점유자(윗집 소유자/세입자)가 1차 책임을 집니다. "
     "공용부분(공용 배관 등) 결함이라면 관리주체나 시공사에 청구할 수 있어요.",
     None, None),
    (69, "survivor",
     "저도 비슷한 일 있었는데 아파트 관리사무소 통해서 누수 원인 진단부터 받았어요. "
     "원인 파악이 책임 소재 가르는 핵심이에요.",
     None, None),
]


class Command(BaseCommand):
    help = "댓글/좋아요/북마크 시연용 데이터 시드 (재실행 안전, 다양한 톤)."

    def handle(self, *args, **options):
        # 1) 추가 사용자 (lawhelper, survivor)
        for spec in COMMUNITY_USERS:
            u, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "nickname": spec["nickname"],
                    "is_active": True,
                },
            )
            if created or not u.has_usable_password():
                u.set_password(spec["password"])
                u.save()

        # 2) 댓글: parent_marker로 부모 등록 후 reply_to_marker로 대댓글 연결
        marker_to_id = {}
        created_count = 0
        for story_id, username, content, marker, reply_to in COMMENTS:
            try:
                user = User.objects.get(username=username)
                story = Story.objects.get(id=story_id)
            except (User.DoesNotExist, Story.DoesNotExist):
                continue

            parent = None
            if reply_to:
                parent_id = marker_to_id.get(reply_to)
                if parent_id:
                    parent = Comment.objects.filter(id=parent_id).first()

            comment, created = Comment.objects.get_or_create(
                user=user,
                story=story,
                parent=parent,
                content=content,
            )
            if marker:
                marker_to_id[marker] = comment.id
            if created:
                created_count += 1

        # 3) 좋아요 / 북마크 (기존 시드 보존)
        testuser = User.objects.get(username="testuser")
        story_labor = Story.objects.get(id=62)
        law1 = Law.objects.get(id=1)
        prec1 = Precedent.objects.get(id=1)

        Like.objects.get_or_create(
            user=testuser, target_type="story", target_id=story_labor.id
        )
        Bookmark.objects.get_or_create(
            user=testuser, target_type="law", target_id=law1.id
        )
        Bookmark.objects.get_or_create(
            user=testuser, target_type="precedent", target_id=prec1.id
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"커뮤니티 사용자 {len(COMMUNITY_USERS)}명, 댓글 시드 (신규 {created_count}건), "
                "좋아요/북마크 기존 시드 유지"
            )
        )
