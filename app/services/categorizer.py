"""AI 카테고리 자동 분류 서비스

Gemini API 키가 있으면 AI 분류를 사용하고,
없으면 키워드 기반 룰 분류로 폴백합니다.
"""
import json
import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── 키워드 기반 카테고리 규칙 ────────────────────────────────────────────────
# (카테고리 이름 → 키워드 목록)
KEYWORD_RULES: dict[str, list[str]] = {
    "식비": [
        "스타벅스", "맥도날드", "버거킹", "롯데리아", "맘스터치", "KFC",
        "이디야", "투썸", "할리스", "파리바게뜨", "뚜레쥬르", "편의점",
        "GS25", "CU", "세븐일레븐", "이마트24", "식당", "음식", "카페",
        "치킨", "피자", "BBQ", "교촌", "BHC", "네네치킨", "도미노",
        "한식", "중식", "일식", "분식", "김밥", "라면", "국밥",
    ],
    "배달": [
        "배달의민족", "배민", "쿠팡이츠", "요기요", "배달",
    ],
    "교통": [
        "택시", "카카오택시", "우버", "지하철", "버스", "코레일", "SRT",
        "KTX", "고속버스", "시외버스", "티머니", "주유", "주차",
        "GS칼텍스", "SK에너지", "현대오일뱅크", "S-OIL",
    ],
    "쇼핑": [
        "쿠팡", "11번가", "G마켓", "옥션", "위메프", "티몬", "SSG",
        "롯데쇼핑", "현대백화점", "신세계", "이마트", "홈플러스", "코스트코",
        "올리브영", "다이소", "무신사", "에이블리", "지그재그",
    ],
    "의료/건강": [
        "병원", "의원", "약국", "약", "치과", "한의원", "헬스", "피트니스",
        "스포츠센터", "요가", "필라테스",
    ],
    "문화/여가": [
        "CGV", "롯데시네마", "메가박스", "영화", "공연", "콘서트",
        "게임", "넷플릭스", "유튜브", "멜론", "스포티파이", "책", "도서",
    ],
    "통신": [
        "SKT", "KT", "LGU+", "SKB", "통신", "인터넷", "휴대폰",
    ],
    "공과금": [
        "전기", "가스", "수도", "관리비", "아파트", "한전", "도시가스",
    ],
    "구독": [
        "구독", "월정액", "정기결제", "애플", "구글", "마이크로소프트",
        "어도비", "노션", "슬랙",
    ],
    "여행": [
        "호텔", "숙박", "에어비앤비", "여행", "항공", "대한항공", "아시아나",
        "제주항공", "진에어", "티웨이",
    ],
}


def classify_by_keyword(memo: str) -> Optional[str]:
    """키워드 기반 카테고리 분류 (폴백)"""
    memo_lower = memo.lower()
    for category_name, keywords in KEYWORD_RULES.items():
        for kw in keywords:
            if kw.lower() in memo_lower:
                return category_name
    return None


async def suggest_category_by_ai(memo: str, category_names: list[str]) -> Optional[str]:
    """
    Gemini API를 사용한 AI 카테고리 추천.
    API 키가 없거나 오류 시 None 반환.
    """
    if not settings.gemini_api_key:
        return None

    prompt = f"""다음 지출 메모를 보고 가장 적합한 카테고리를 하나만 선택해주세요.

메모: {memo}

선택 가능한 카테고리:
{", ".join(category_names)}

반드시 위 카테고리 중 하나만 답하세요. 다른 설명 없이 카테고리 이름만 출력하세요."""

    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-flash:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 50, "temperature": 0.1},
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"x-goog-api-key": settings.gemini_api_key},
            )
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # 반환된 텍스트가 카테고리 목록에 있으면 반환
            if text in category_names:
                return text
            # 부분 매칭
            for name in category_names:
                if name in text:
                    return name
    except Exception as e:
        logger.warning(f"Gemini API 호출 실패: {e}")

    return None


async def suggest_category(memo: str, categories: list) -> Optional[int]:
    """
    메모를 기반으로 카테고리 ID를 추천합니다.

    Args:
        memo: 지출 메모
        categories: Category 모델 객체 리스트

    Returns:
        추천 카테고리 ID (없으면 None)
    """
    if not memo or not categories:
        return None

    category_names = [c.name for c in categories]

    # 1순위: AI 분류 (Gemini API)
    ai_result = await suggest_category_by_ai(memo, category_names)
    if ai_result:
        for cat in categories:
            if cat.name == ai_result:
                return cat.id

    # 2순위: 키워드 기반 분류
    keyword_result = classify_by_keyword(memo)
    if keyword_result:
        for cat in categories:
            if cat.name == keyword_result:
                return cat.id

    # 3순위: 기타 카테고리
    for cat in categories:
        if cat.name == "기타":
            return cat.id

    return None
