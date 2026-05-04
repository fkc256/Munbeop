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

    # =========================================================================
    # === Phase 2 확장: 댓글 0건 사연 18건 + 1건 사연 14건 + 2건 사연 8건 보강 ===
    # === 모든 사연에 최소 3건 + 일부에 베스트 댓글 후보 ===
    # =========================================================================

    # --- housing 보강 ---
    # id=74 원룸 곰팡이 (0건 → 3건)
    ("원룸 곰팡이", "lawhelper",
     "결로·단열 부실은 임대인의 수선의무(민법 제623조) 영역입니다. 입주 후 한 달 내 발생이라면 원래 하자였을 가능성이 높아요. 사진·동영상 시기별로 보존하세요.", None, None),
    ("원룸 곰팡이", "survivor",
     "저도 같은 일 겪었어요. 곰팡이 검출업체 검사 받고 결과지를 임대인에게 내밀었더니 그제서야 도배·단열 공사 해줬습니다.", None, None),
    ("원룸 곰팡이", "testuser",
     "환기는 일반인이 할 수 있는 수준이고, 구조적 단열 결함은 임대인 책임이라는 게 일관된 판례 입장입니다.", None, None),

    # id=76 전세사기 (1건 → 3건)
    ("전세사기 의심", "survivor",
     "저는 그 매물 포기했어요. 보험 가입 안 되는 매물은 위험 신호예요. 시간이 좀 걸려도 안전한 매물 찾는 게 낫습니다.", None, None),
    ("전세사기 의심", "testuser2",
     "공인중개사가 '문제없다'는 말 자체가 위험합니다. 본인이 보증서지 않는 한 책임 안 져요.", None, None),

    # --- labor 보강 ---
    # id=79 직장 내 괴롭힘 (1건 → 3건)
    ("직장 내 괴롭힘 신고", "survivor",
     "저는 따돌림 정황 카톡 캡처와 회의 배제 메일 보존해서 노동위원회 갔어요. 시간 걸리지만 인정받았습니다.", None, None),
    ("직장 내 괴롭힘 신고", "testuser",
     "사내 신고 절차 진행과 별개로 외부 상담(고용노동부 1350) 병행하시면 좋아요.", None, None),

    # id=80 퇴직금 지연 (0건 → 3건)
    ("퇴직금 지급이 한 달", "lawhelper",
     "근로기준법 제36조상 퇴직 후 14일 이내 지급이 원칙이고, 지연이자(연 20%)도 청구 가능합니다. 노동청 진정으로 빠르게 해결됩니다.", None, None),
    ("퇴직금 지급이 한 달", "survivor",
     "저는 노동청 진정 넣고 일주일 만에 회사가 입금했어요. 진정만 들어가도 회사들 빠르게 움직입니다.", None, None),
    ("퇴직금 지급이 한 달", "testuser2",
     "임금체불·퇴직금 미지급은 형사처벌 대상이라 회사가 부담스러워합니다.", None, None),

    # id=81 재택산재 (0건 → 3건)
    ("재택근무 중 사고", "lawhelper",
     "재택근무도 근로 시간·업무 관련성 입증 시 산재 인정됩니다(고용노동부 지침). 회사가 거부해도 근로복지공단에 직접 신청 가능합니다.", None, None),
    ("재택근무 중 사고", "survivor",
     "저도 재택 중 다친 적 있는데 공단에 직접 신청해서 인정받았어요. 회사 거부와 별개로 진행 가능합니다.", None, None),
    ("재택근무 중 사고", "testuser",
     "근무 시간·장소·업무 관련성 입증 자료(업무 PC 로그, 미팅 시간 등) 미리 챙기시면 도움돼요.", None, None),

    # --- consumer 보강 ---
    # id=84 온라인 강의 환불 (1건 → 3건)
    ("온라인 강의 환불", "survivor",
     "저는 같은 케이스 분쟁조정위 신청해서 80% 환불받았어요. 무료 절차고 보통 1~2개월 걸립니다.", None, None),
    ("온라인 강의 환불", "testuser2",
     "전자상거래법상 7일 내 청약철회 권리는 약관으로 배제 못 합니다. 강하게 주장하세요.", None, None),

    # id=85 택시 미터기 (0건 → 3건)
    ("택시 미터기 조작", "lawhelper",
     "택시 부당요금은 다산콜(120) 또는 관할 시·도청 교통 민원실에 영수증·결제내역 첨부해서 신고하면 환불 처리됩니다.", None, None),
    ("택시 미터기 조작", "survivor",
     "저는 다산콜 신고 후 일주일 만에 환불받았어요. 카드 결제면 추적 쉬워서 빠릅니다.", None, None),
    ("택시 미터기 조작", "testuser",
     "택시 영수증의 차량 번호와 시간대 기록이 핵심이에요. GPS 경로 데이터 요청도 가능합니다.", None, None),

    # id=86 구독 자동결제 (0건 → 3건)
    ("구독 자동결제 해지", "lawhelper",
     "전자상거래법상 정기결제 해지는 가입과 동등한 수준의 절차로 가능해야 합니다. 일부러 어렵게 만든 약관은 불공정약관으로 무효 소지 있어요.", None, None),
    ("구독 자동결제 해지", "survivor",
     "카드사에 정기결제 차단 요청도 한 방법이에요. 카드사 콜센터에 사업자명 알려주면 막아줍니다.", None, None),
    ("구독 자동결제 해지", "testuser2",
     "한국소비자원에 신고하면 사업자한테 시정 권고 들어갑니다. 구독 해지 어렵게 한 사례 많이 처리됐어요.", None, None),

    # --- family 보강 ---
    # id=88 재산분할 회피 (1건 → 3건)
    ("재산분할 협의 중", "survivor",
     "저는 가압류 신청한 후 협상이 빨라졌어요. 재산 처분이 더 어려워지면 합의 가능성도 올라갑니다.", None, None),
    ("재산분할 협의 중", "testuser",
     "최근 5년 이내 가족 명의 이전 내역은 사해행위로 의심받기 쉽습니다. 등기 이력 다 모아두세요.", None, None),

    # id=89 친권/양육권 분리 (1건 → 3건)
    ("이혼 시 친권과 양육권", "survivor",
     "저는 분리하지 말라는 변호사 조언 받아서 양쪽 다 가져왔어요. 분리하면 학교 동의서마다 갈등 생깁니다.", None, None),
    ("이혼 시 친권과 양육권", "testuser2",
     "상대방이 양육에 무관심하면 양쪽 다 가져오는 게 일반적입니다. 분리는 특수한 사정이 있을 때만.", None, None),

    # id=90 사실혼 (0건 → 3건)
    ("사실혼 관계 해소", "lawhelper",
     "사실혼은 혼인의사 + 공동생활 + 사회적 인식이 있으면 인정됩니다. 친지·이웃 진술서, 공동 통장, 결혼식 사진 등이 입증 자료가 됩니다.", None, None),
    ("사실혼 관계 해소", "survivor",
     "저는 사실혼 인정받고 재산분할 50% 받았어요. 공동 명의 부동산이 있으면 더 명확해집니다.", None, None),
    ("사실혼 관계 해소", "testuser",
     "사실혼도 법률혼과 같이 재산분할·위자료 청구 가능합니다. 다만 상속권은 인정 안 돼요.", None, None),

    # id=91 조부모 면접교섭권 (0건 → 3건)
    ("조부모가 손주 면접교섭권", "lawhelper",
     "민법 개정(2017)으로 조부모도 면접교섭권 청구 가능합니다. 가정법원에 청구하시고 자녀의 복리에 부합하면 인정됩니다.", None, None),
    ("조부모가 손주 면접교섭권", "survivor",
     "저희 부모님도 청구해서 한 달에 한 번 만나기로 결정 받으셨어요. 시간이 오래 걸렸지만 결과는 좋았습니다.", None, None),
    ("조부모가 손주 면접교섭권", "testuser2",
     "자녀 의사도 중요해서 손자 나이가 어느 정도 있으면 의견 들어요.", None, None),

    # --- traffic 보강 ---
    # id=93 비접촉 사고 (1건 → 3건)
    ("주차장 후진 사고", "survivor",
     "저도 비슷한 일 있었는데 블랙박스 영상으로 인과관계 입증 어렵다는 보험사 의견 받고 책임 면제됐어요.", None, None),
    ("주차장 후진 사고", "testuser",
     "비접촉 사고는 입증 책임이 청구하는 쪽에 있습니다. 적극적으로 부인하세요.", None, None),

    # id=94 음주운전 추돌 (1건 → 3건)
    ("음주운전 차량에 추돌", "survivor",
     "저도 음주차량에 받혔는데 합의금이 보통의 1.5배 정도 나왔어요. 위자료 가중 청구 가능합니다.", None, None),
    ("음주운전 차량에 추돌", "testuser2",
     "보험사 제시안 수락 전에 손해사정사 무료 상담 한 번 받아보시면 좋아요. 누락된 항목 잡아줍니다.", None, None),

    # id=95 킥보드 사고 (0건 → 3건)
    ("킥보드 사고", "lawhelper",
     "전동킥보드는 도로교통법상 원동기장치자전거에 해당해 보험 가입 의무가 있습니다(공유 킥보드는 업체가 가입). 자동차 운전자 과실이 명확하면 자동차보험으로 보상됩니다.", None, None),
    ("킥보드 사고", "survivor",
     "저는 공유킥보드 타다 비슷한 사고 났는데 업체 보험 + 상대 차량 보험 동시 적용으로 보상받았어요.", None, None),
    ("킥보드 사고", "testuser",
     "치료비·휴업손해·위자료 모두 청구 가능. 진단서·영수증 다 모으세요.", None, None),

    # id=96 자전거 vs 보행자 (0건 → 3건)
    ("자전거 vs 보행자 사고", "lawhelper",
     "도로교통법 위반(인도 주행)이라 자전거 운전자 책임이 큽니다. 다만 일상생활배상책임보험에 가입돼 있으면 보상 가능해요(주택종합보험에 통상 포함).", None, None),
    ("자전거 vs 보행자 사고", "survivor",
     "저도 일상배상책임보험으로 처리한 적 있어요. 부모님 보험에 자녀까지 포함돼 있는 경우도 많으니 확인해보세요.", None, None),
    ("자전거 vs 보행자 사고", "testuser2",
     "중상해라면 형사 처벌(과실치상) 가능성도 있어 합의 시도가 중요합니다.", None, None),

    # --- criminal 보강 ---
    # id=98 보이스피싱 (1건 → 3건)
    ("보이스피싱으로 600만원", "survivor",
     "저도 비슷한 케이스인데 신고 빨라서 200만원 회수했어요. 30분 안이면 가능성 있습니다.", None, None),
    ("보이스피싱으로 600만원", "testuser",
     "신고 후에도 통신사·신용카드사에 명의도용 차단 요청해놓으세요. 2차 피해 예방 차원입니다.", None, None),

    # id=99 SNS 무단 캡처 (1건 → 3건)
    ("회사 동료가 제 SNS", "survivor",
     "저는 같은 일로 회사에 공식 항의했고 동료가 사과·삭제했어요. 형사 신고까지 안 가도 해결될 수 있습니다.", None, None),
    ("회사 동료가 제 SNS", "testuser2",
     "단톡방 내용도 캡처해두세요. 회사 내 징계 절차에서 증거가 됩니다.", None, None),

    # id=100 건물주 무단진입 (0건 → 3건)
    ("건물주가 임차인 비밀번호", "lawhelper",
     "임차인 동의 없는 출입은 주거침입(형법 제319조)에 해당합니다. CCTV·도어록 출입 기록 보존하세요.", None, None),
    ("건물주가 임차인 비밀번호", "survivor",
     "저도 비슷한 일로 경찰 신고 후 건물주가 사과·향후 출입 자제 각서 받았어요.", None, None),
    ("건물주가 임차인 비밀번호", "testuser",
     "도어록 비밀번호도 즉시 변경하시고 임대차 계약서에 출입 동의 조항 확인하세요.", None, None),

    # id=101 층간소음 보복 (0건 → 3건)
    ("층간소음 보복", "lawhelper",
     "고의적 소음·욕설은 경범죄처벌법(인근소란) 또는 정보통신망법(욕설이 메시지로 갔다면)으로 처벌 가능합니다. 소음 측정·녹취 기록 보존 필수.", None, None),
    ("층간소음 보복", "survivor",
     "저는 층간소음 이웃사이센터(국가소음정보시스템)에 신청해서 중재받았어요. 무료에 효과 좋습니다.", None, None),
    ("층간소음 보복", "testuser2",
     "112 신고도 가능합니다. 야간 시간대(밤 10시~새벽 6시)에 반복되면 더 강하게 다룹니다.", None, None),

    # --- realestate 보강 ---
    # id=103 명도 거부 (1건 → 3건)
    ("오피스텔 매매 — 임차인", "survivor",
     "저는 명도소송 + 강제집행까지 갔는데 5개월 걸렸어요. 매도인이 약속한 명도 책임 안 지면 매매대금에서 공제하는 조건도 협상 가능합니다.", None, None),
    ("오피스텔 매매 — 임차인", "testuser",
     "잔금 일부를 명도 완료 시까지 보류하는 조건을 미리 계약서에 넣었으면 좋았겠네요.", None, None),

    # id=104 하자 매매 (0건 → 3건)
    ("공인중개사 설명과 다른 하자", "lawhelper",
     "매도인이 알면서 숨긴 하자는 사기 또는 하자담보책임(민법 제580조)으로 다툴 수 있습니다. 중개사도 설명의무 위반으로 책임 가능. 하자 발견 즉시 사진·영상 보존하세요.", None, None),
    ("공인중개사 설명과 다른 하자", "survivor",
     "저는 매도인·중개사 둘 다 상대로 손해배상 받았어요. 중개사보험으로 일부 보상됩니다.", None, None),
    ("공인중개사 설명과 다른 하자", "testuser2",
     "한국공인중개사협회에 진정 넣으면 자체 조사도 진행됩니다.", None, None),

    # id=105 다운계약 (0건 → 3건)
    ("다운계약 강요", "lawhelper",
     "다운계약은 매수인도 처벌 대상입니다(부동산 거래신고법 위반, 과태료). 양도세 추징도 매도인뿐 아니라 매수인 보유 기간에 영향 줍니다. 거부하시는 게 맞습니다.", None, None),
    ("다운계약 강요", "survivor",
     "저는 거부했더니 매도인이 다른 매수자 찾는다고 했지만, 결국 다시 와서 정상 계약했어요. 강요는 협상 카드일 뿐입니다.", None, None),
    ("다운계약 강요", "testuser",
     "정상 신고한 매수인은 추후 양도세 절감 효과가 있어요. 손해 보는 거 아닙니다.", None, None),

    # id=106 재개발 입주권 (0건 → 3건)
    ("재개발 지역 빌라 매수", "lawhelper",
     "재개발 입주권 자격은 조합 정관·관리처분계획에 따라 다양합니다. 중개사 설명과 다르면 설명의무 위반·기망에 의한 계약취소 가능성이 있어요.", None, None),
    ("재개발 지역 빌라 매수", "survivor",
     "저도 비슷한 케이스로 매도인·중개사 상대 손해배상 청구해서 일부 받았어요. 매도인의 인지 여부 입증이 핵심.", None, None),
    ("재개발 지역 빌라 매수", "testuser2",
     "조합 정관 + 관리처분계획서 보고 자격 확인하셨어야 했어요. 지금이라도 조합에 정확한 사유서 받으시고 변호사 상담 권장.", None, None),

    # --- debt 보강 ---
    # id=108 사채 협박 (1건 → 3건)
    ("사채업자한테 협박", "survivor",
     "저는 미등록 사채라 모든 통화 녹음하고 경찰 신고했어요. 사채업자 본인이 처벌받고 초과 이자도 안 갚았습니다.", None, None),
    ("사채업자한테 협박", "testuser2",
     "금융감독원 불법사금융 신고센터(1332)에도 함께 신고하세요. 더 빠르게 움직입니다.", None, None),

    # id=109 회생 보증인 (1건 → 3건)
    ("회생 절차 후 가족", "survivor",
     "저희 케이스에선 부모님이 별도로 채권자와 분할 합의 봤어요. 회생 후엔 채권자도 강하게 못 나오는 경우가 많습니다.", None, None),
    ("회생 절차 후 가족", "testuser",
     "보증인 입장에서도 개인회생 신청 가능하니 부담이 크면 함께 검토하세요.", None, None),

    # id=110 동업자 횡령 (0건 → 3건)
    ("전 동업자가 회사 자금", "lawhelper",
     "동업 자금의 사적 사용은 횡령(형법 제356조 또는 제355조)에 해당합니다. 거래 영수증·카드 명세서 보존 후 형사 고소 + 민사 청구 병행 가능합니다.", None, None),
    ("전 동업자가 회사 자금", "survivor",
     "저는 동업 정산 분쟁에서 카드 명세를 1년치 분석해서 형사·민사 동시 진행했어요. 시간 걸리지만 회수했습니다.", None, None),
    ("전 동업자가 회사 자금", "testuser2",
     "동업계약서에 정산 조항 있으면 그게 1차 기준이에요. 없어도 사실관계로 청구 가능합니다.", None, None),

    # id=111 카드 결제 분쟁 (0건 → 3건)
    ("카드 결제 대금 분쟁", "lawhelper",
     "여신전문금융업법상 부정사용으로 의심되면 카드사가 조사 의무가 있습니다. 거부 시 금융감독원 분쟁조정 신청 가능. 본인 인증이 정상이라도 명의도용 정황을 입증하면 책임 면제됩니다.", None, None),
    ("카드 결제 대금 분쟁", "survivor",
     "저는 카드사 거부 후 금감원 분쟁조정으로 100% 환불받았어요. 시간은 좀 걸렸지만 결과 좋았습니다.", None, None),
    ("카드 결제 대금 분쟁", "testuser",
     "결제 시점·장소 본인 알리바이 자료 챙기시고 결제 알림 안 받은 정황도 입증하시면 도움됩니다.", None, None),

    # --- etc 보강 ---
    # id=112 층간소음 (1건 → 3건)
    ("층간소음 분쟁 — 관리사무소", "survivor",
     "저는 환경분쟁조정위 신청 후 위층이 매트 깔고 활동시간 조정해서 해결됐어요. 무료고 효과 있었습니다.", None, None),
    ("층간소음 분쟁 — 관리사무소", "testuser",
     "공동주택관리법 개정으로 관리사무소 중재 의무가 강화됐어요. 관리사무소 응대 기록도 챙기시면 후속 절차에서 도움됩니다.", None, None),

    # id=113 반려견 분쟁 (2건 → 3건)
    ("반려견이 옆집", "testuser2",
     "동물병원 진단서·치료비 영수증 모으고, 정신적 위자료는 통상 10~30만원 선이라 너무 과도하면 거절도 가능합니다.", None, None),

    # id=114 공방 영업 (1건 + 작성자 답변 → 3건)
    ("집에서 운영한 공방", "lawhelper",
     "주거지역에서도 일정 규모·소음 기준 내라면 가내 사업 가능합니다. 다만 이웃 민원 누적 시 행정처분 가능성이 있어 사전에 관할 구청 문의하시는 게 안전.", None, None),
    ("집에서 운영한 공방", "survivor",
     "저도 같은 케이스로 구청 상담받았는데 실제로 영업 중단 명령까지 가는 경우는 드물어요. 이웃과 시간대 협의로 푸는 게 일반적.", None, None),

    # id=115 단체 소송 (0건 → 3건)
    ("온라인 사기 피해 모임", "lawhelper",
     "공동소송 또는 공동고소로 진행 가능합니다. 변호사 한 명이 다수 의뢰인을 대리하는 형태로 비용 부담을 나누는 케이스가 많아요. 법무법인에 단체 상담 요청해보세요.", None, None),
    ("온라인 사기 피해 모임", "survivor",
     "저도 비슷한 모임에서 공동 고소 진행했어요. 30명 정도 모이니 변호사 비용이 1인당 부담 가능한 수준이 됐습니다.", None, None),
    ("온라인 사기 피해 모임", "testuser2",
     "경찰 신고도 동시에 들어가야 효과 좋아요. 피해자 다수 신고는 수사 우선순위가 올라갑니다.", None, None),

    # id=116 유튜브 도용 (0건 → 3건)
    ("유튜브 영상 무단 도용", "lawhelper",
     "유튜브 자체 저작권 신고(Copyright Strike)로 1차 대응하시고, 손해배상은 별도 민사 청구 필요. 조회수 기반 추정 수익 + 명예회복 비용까지 청구 가능해요.", None, None),
    ("유튜브 영상 무단 도용", "survivor",
     "저는 신고 한 번에 채널 영상 내려졌어요. 같은 채널이 반복 도용하면 채널 자체 폭파됩니다.", None, None),
    ("유튜브 영상 무단 도용", "testuser",
     "한국저작권위원회 분쟁조정 신청도 좋은 방법이에요. 무료고 빠릅니다.", None, None),

    # === 댓글 2건 사연 보강 (1건씩 추가, 다양성 위함) ===
    ("월세 보증금에서 도배", "testuser",
     "1년 미만 거주면 도배 비용 거의 없는 게 정상이에요. 영수증 없이 청구하는 건 위법 소지.", None, None),
    ("재계약 시 집주인이 일방적으로", "survivor",
     "5%룰 거부했더니 집주인이 1년만 더 살라고 했어요. 결국 그렇게 합의 봤고요.", None, None),
    ("주말 출근 강요", "testuser",
     "근로계약서에 포괄임금제 명시 안 됐다면 별도 수당 받을 권리 있어요.", None, None),
    ("중고거래 사기", "testuser",
     "더치트 등록도 도움됩니다. 다른 피해자들 모이면 공동 고소도 진행되더라고요.", None, None),
    ("헬스장 6개월 결제", "survivor",
     "한국체육시설협회에 신고하면 폐업 정보 공유돼서 다른 피해자 보호에도 도움됩니다.", None, None),
    ("아파트 매매 — 잔금 직전", "lawhelper",
     "가압류 해소 전에 잔금 치르면 위험하니 반드시 등기 다시 확인 후 진행하세요.", None, None),
    ("보증 잘못 서서", "testuser2",
     "시효 항변 외에 보증 의사 표시의 흠결(강박·기망)도 다툴 수 있어요. 당시 정황 자료 모으세요.", None, None),
]


# 모든 사연에 베스트 댓글 후보 1건씩 (lawhelper 전문가 댓글에 좋아요 시드)
# 사연 키워드 → 좋아요 줄 사용자 명단 (3명 이상이면 베스트 자동 발동)
EXTRA_LIKE_SEEDS = [
    # housing
    ("월세 보증금에서 도배", "통상의 마모와 자연 노후화는", ["testuser", "testuser2", "survivor"]),
    ("원룸 곰팡이", "결로·단열 부실은 임대인의 수선의무", ["testuser", "testuser2", "survivor", "demo_helper"]),
    ("재계약 시 집주인이 일방적으로", "주택임대차보호법상 임대료 인상", ["survivor", "demo_helper", "demo_helper2"]),
    ("전세사기 의심", "근저당이 시세의 70% 넘으면", ["testuser", "testuser2", "survivor"]),
    # labor
    ("주말 출근 강요", "연봉제라도 법정수당", ["testuser", "survivor", "demo_helper"]),
    ("직장 내 괴롭힘 신고", "근로기준법 제76조의3", ["testuser", "testuser2", "demo_helper2"]),
    ("퇴직금 지급이 한 달", "근로기준법 제36조상 퇴직", ["survivor", "demo_helper", "demo_helper2"]),
    ("재택근무 중 사고", "재택근무도 근로 시간·업무 관련성", ["testuser", "survivor", "demo_helper"]),
    # consumer
    ("중고거래 사기", "송금 직후 신고하면 지급정지", ["testuser2", "survivor", "demo_helper"]),
    ("헬스장 6개월 결제", "할부 거래라면 신용카드사 차지백", ["testuser", "survivor", "demo_helper2"]),
    ("온라인 강의 환불", "전자상거래법상 디지털 콘텐츠", ["testuser2", "survivor", "demo_helper"]),
    ("택시 미터기 조작", "택시 부당요금은 다산콜", ["testuser", "demo_helper", "demo_helper2"]),
    ("구독 자동결제 해지", "전자상거래법상 정기결제", ["testuser2", "survivor", "demo_helper"]),
    # family
    ("이혼 후 양육비 약속", "양육비 이행관리원 외에", ["testuser", "testuser2", "demo_helper"]),
    ("재산분할 협의 중", "재산분할 회피 목적의 처분", ["survivor", "demo_helper", "demo_helper2"]),
    ("이혼 시 친권과 양육권", "친권과 양육권 분리는 협의로", ["testuser2", "survivor", "demo_helper"]),
    ("사실혼 관계 해소", "사실혼은 혼인의사", ["testuser", "survivor", "demo_helper"]),
    ("조부모가 손주 면접교섭권", "민법 개정(2017)으로 조부모", ["testuser2", "survivor", "demo_helper2"]),
    # traffic
    ("우회전 사고", "보행자 신호가 명확히 빨간불", ["testuser", "testuser2", "survivor", "demo_helper"]),
    ("주차장 후진 사고", "비접촉 사고도 인과관계가 입증", ["testuser", "survivor", "demo_helper"]),
    ("음주운전 차량에 추돌", "음주운전은 형사 처벌과 별개", ["testuser2", "survivor", "demo_helper2"]),
    ("킥보드 사고", "전동킥보드는 도로교통법상", ["testuser", "survivor", "demo_helper"]),
    ("자전거 vs 보행자 사고", "도로교통법 위반(인도 주행)", ["testuser2", "demo_helper", "demo_helper2"]),
    # criminal
    ("보이스피싱으로 600만원", "전기통신금융사기특별법상 30분", ["testuser2", "survivor", "demo_helper"]),
    ("회사 동료가 제 SNS", "비공개 글의 무단 캡처", ["testuser", "survivor", "demo_helper2"]),
    ("건물주가 임차인 비밀번호", "임차인 동의 없는 출입은 주거침입", ["testuser", "testuser2", "demo_helper"]),
    ("층간소음 보복", "고의적 소음·욕설은 경범죄처벌법", ["survivor", "demo_helper", "demo_helper2"]),
    # realestate
    ("아파트 매매 — 잔금 직전", "가압류는 매수인이 알 수 없었던", ["testuser2", "survivor", "demo_helper"]),
    ("오피스텔 매매 — 임차인", "매도인이 명도 책임을 부담", ["testuser", "survivor", "demo_helper2"]),
    ("공인중개사 설명과 다른 하자", "매도인이 알면서 숨긴 하자", ["testuser2", "survivor", "demo_helper"]),
    ("다운계약 강요", "다운계약은 매수인도 처벌", ["testuser", "survivor", "demo_helper2"]),
    ("재개발 지역 빌라 매수", "재개발 입주권 자격은 조합 정관", ["testuser2", "demo_helper", "demo_helper2"]),
    # debt
    ("보증 잘못 서서", "보증채무도 일반 채권 시효", ["testuser2", "survivor", "demo_helper"]),
    ("사채업자한테 협박", "법정 최고 이자율(연 20%)", ["testuser", "survivor", "demo_helper2"]),
    ("회생 절차 후 가족", "회생 절차의 면책 효력", ["testuser2", "survivor", "demo_helper"]),
    ("전 동업자가 회사 자금", "동업 자금의 사적 사용은 횡령", ["testuser", "survivor", "demo_helper2"]),
    ("카드 결제 대금 분쟁", "여신전문금융업법상 부정사용", ["testuser2", "survivor", "demo_helper"]),
    # etc
    ("층간소음 분쟁 — 관리사무소", "환경분쟁조정위(중앙·지방)에 신청", ["testuser", "testuser2", "demo_helper"]),
    ("반려견이 옆집", "동물 점유자 책임(민법 제759조)", ["survivor", "demo_helper", "demo_helper2"]),
    ("집에서 운영한 공방", "주거지역에서도 일정 규모", ["testuser", "survivor", "demo_helper"]),
    ("온라인 사기 피해 모임", "공동소송 또는 공동고소로", ["testuser2", "survivor", "demo_helper"]),
    ("유튜브 영상 무단 도용", "유튜브 자체 저작권 신고", ["testuser", "survivor", "demo_helper2"]),
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

        # 3) 좋아요 (베스트 댓글 만들기) — 기존 + 확장 시드 합쳐서
        all_like_seeds = LIKE_SEEDS + EXTRA_LIKE_SEEDS
        for story_kw, content_prefix, liker_usernames in all_like_seeds:
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
