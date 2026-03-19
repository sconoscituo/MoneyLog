"""결제 라우터"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.payment import verify_payment, cancel_payment

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentVerifyRequest(BaseModel):
    imp_uid: str
    merchant_uid: str
    plan: str  # "premium" - 월 5,900원
    amount: int


class PaymentCancelRequest(BaseModel):
    imp_uid: str
    reason: str = "사용자 요청"


@router.post("/verify")
async def verify_and_upgrade(req: PaymentVerifyRequest):
    """결제 검증 후 구독 업그레이드"""
    # 실제 구현 시 DB에 Payment 레코드 저장 후 user 플랜 업그레이드
    return {"status": "success", "plan": req.plan, "message": "구독이 업그레이드되었습니다."}


@router.post("/cancel")
async def cancel_subscription(req: PaymentCancelRequest):
    """구독 취소 및 환불"""
    return {"status": "cancelled", "message": "구독이 취소되었습니다."}


@router.get("/history")
async def get_payment_history():
    """결제 내역 조회"""
    return {"payments": [], "message": "결제 내역"}
