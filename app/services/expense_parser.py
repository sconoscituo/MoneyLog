"""카드 결제 SMS 문자 파싱 서비스

지원 형식:
  - [KB국민] 홍길동님 12,500원 스타벅스 승인
  - [신한카드] 15,000원 결제 배달의민족
  - [삼성카드] 승인 홍길동 23,000원 올리브영
  - [현대카드] 일시불 10,000원 GS25 승인완료
  - [하나카드] 홍길동 8,900원 승인 쿠팡
"""
import re
from datetime import date
from typing import Optional


# 카드사 패턴 (문자 발신자 패턴)
CARD_ISSUERS = [
    "KB국민", "신한", "삼성", "현대", "롯데", "하나", "우리", "농협",
    "IBK기업", "SC제일", "씨티", "카카오뱅크", "토스뱅크",
]

# 금액 정규식: 1,234,567원 또는 1234567원
AMOUNT_PATTERN = re.compile(r"([\d,]+)원")

# 카드 문자 감지용 키워드
CARD_KEYWORDS = ["승인", "결제", "카드", "일시불", "할부"]

# 제거할 노이즈 토큰
NOISE_TOKENS = {
    "승인", "결제", "완료", "일시불", "할부", "님", "카드",
    "이용", "내역", "안내", "알림", "취소",
}

# 카드사 이름 패턴 (대괄호 포함)
ISSUER_BRACKET_PATTERN = re.compile(
    r"\[(" + "|".join(CARD_ISSUERS) + r")[^\]]*\]"
)

# 카드 소유자 이름 패턴: "홍길동님" 처럼 반드시 '님'으로 끝나는 경우만 제거
# "스타벅스", "배달의민족" 같은 가맹점명은 '님'이 없으므로 제거되지 않음
KOREAN_NAME_PATTERN = re.compile(r"[가-힣]{2,4}님")


def parse_sms(sms_text: str) -> dict:
    """
    카드 결제 SMS를 파싱하여 지출 정보를 추출합니다.

    Returns:
        {
            "success": bool,
            "amount": float | None,
            "memo": str | None,
            "expense_date": date | None,
            "message": str,
        }
    """
    if not sms_text or not isinstance(sms_text, str):
        return {
            "success": False,
            "amount": None,
            "memo": None,
            "expense_date": None,
            "message": "유효하지 않은 입력입니다.",
        }

    text = sms_text.strip()

    if not text:
        return {
            "success": False,
            "amount": None,
            "memo": None,
            "expense_date": None,
            "message": "빈 문자열입니다.",
        }

    # 카드 문자 여부 확인
    is_card_sms = any(kw in text for kw in CARD_KEYWORDS) or bool(
        ISSUER_BRACKET_PATTERN.search(text)
    )
    if not is_card_sms:
        return {
            "success": False,
            "amount": None,
            "memo": None,
            "expense_date": None,
            "message": "카드 결제 문자가 아닌 것 같습니다. 키워드(승인, 결제, 카드)를 확인해주세요.",
        }

    # 금액 추출
    amount = _extract_amount(text)
    if amount is None:
        return {
            "success": False,
            "amount": None,
            "memo": None,
            "expense_date": None,
            "message": "금액을 파싱할 수 없습니다. '원' 단위가 포함된 금액이 있는지 확인해주세요.",
        }

    # 가맹점명(메모) 추출
    memo = _extract_merchant(text)

    return {
        "success": True,
        "amount": amount,
        "memo": memo or "",
        "expense_date": date.today(),
        "message": f"파싱 완료: {amount:,.0f}원 / {memo or '가맹점명 미확인'}",
    }


def _extract_amount(text: str) -> Optional[float]:
    """금액 추출 (콤마 포함 숫자 + '원')"""
    if not text:
        return None
    matches = AMOUNT_PATTERN.findall(text)
    if not matches:
        return None
    # 가장 큰 금액을 실제 결제 금액으로 간주
    amounts = []
    for m in matches:
        try:
            amounts.append(float(m.replace(",", "")))
        except ValueError:
            continue
    return max(amounts) if amounts else None


def _extract_merchant(text: str) -> Optional[str]:
    """가맹점명 추출

    전략:
    1. 금액 위치를 기준으로 금액 뒤쪽 텍스트를 우선 탐색
       (카드 SMS 패턴: [카드사] 이름 금액원 가맹점 승인)
    2. 뒤쪽에서 찾지 못하면 전체 텍스트에서 탐색
    """
    # 카드사 태그 제거
    cleaned = ISSUER_BRACKET_PATTERN.sub("", text).strip()

    # 금액 위치 파악 후 뒤쪽과 앞쪽 분리
    amount_match = AMOUNT_PATTERN.search(cleaned)
    if amount_match:
        after_amount = cleaned[amount_match.end():]
        before_amount = cleaned[:amount_match.start()]
    else:
        after_amount = ""
        before_amount = cleaned

    def _tokens_from(segment: str) -> list[str]:
        """세그먼트에서 의미 있는 토큰 추출"""
        # '님' 붙은 이름 제거
        segment = KOREAN_NAME_PATTERN.sub("", segment)
        # 금액 제거
        segment = AMOUNT_PATTERN.sub("", segment)
        tokens = re.split(r"[\s\[\]()｜|,]+", segment)
        return [t for t in tokens if t and t not in NOISE_TOKENS and len(t) > 1]

    # 금액 뒤쪽 토큰 우선
    after_tokens = _tokens_from(after_amount)
    if after_tokens:
        return max(after_tokens, key=len)

    # 금액 앞쪽 토큰 (이름 제외 후)
    before_tokens = _tokens_from(before_amount)
    if before_tokens:
        return max(before_tokens, key=len)

    return None
