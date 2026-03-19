"""구독 플랜"""
from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"       # 월 4,900원
    FAMILY = "family" # 월 9,900원

PLAN_LIMITS = {
    PlanType.FREE:   {"accounts": 1, "ai_insight": False, "export_csv": False, "budget_alert": False},
    PlanType.PRO:    {"accounts": 5, "ai_insight": True,  "export_csv": True,  "budget_alert": True},
    PlanType.FAMILY: {"accounts": 10,"ai_insight": True,  "export_csv": True,  "budget_alert": True},
}

PLAN_PRICES_KRW = {
    PlanType.FREE: 0,
    PlanType.PRO: 4900,
    PlanType.FAMILY: 9900,
}

def get_plan_limits(plan: PlanType) -> dict:
    return PLAN_LIMITS[plan]

def get_plan_price(plan: PlanType) -> int:
    return PLAN_PRICES_KRW[plan]
