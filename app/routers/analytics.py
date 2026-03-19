"""
가계부 지출 분석 라우터
"""
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["지출 분석"])

try:
    from app.models.expense import Expense
    HAS_EXPENSE = True
except ImportError:
    HAS_EXPENSE = False

try:
    from app.config import config
    GEMINI_KEY = config.GEMINI_API_KEY
except Exception:
    GEMINI_KEY = ""


@router.get("/summary")
async def get_spending_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """기간별 지출 요약 및 카테고리 분석"""
    if not HAS_EXPENSE:
        return {"message": "지출 모델이 없습니다"}

    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            Expense.category,
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count"),
        )
        .where(Expense.user_id == current_user.id, Expense.created_at >= since)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    )
    rows = result.all()

    categories = [
        {"category": r.category or "기타", "total": float(r.total), "count": r.count}
        for r in rows
    ]
    grand_total = sum(c["total"] for c in categories)

    return {
        "period_days": days,
        "total_spent": grand_total,
        "categories": categories,
        "top_category": categories[0]["category"] if categories else None,
    }


@router.get("/ai-advice")
async def get_ai_spending_advice(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 지출 패턴 분석 및 절약 조언"""
    if not HAS_EXPENSE or not GEMINI_KEY:
        return {"advice": "AI 분석을 사용할 수 없습니다"}

    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.user_id == current_user.id, Expense.created_at >= since)
        .group_by(Expense.category)
    )
    rows = result.all()
    if not rows:
        return {"advice": "분석할 지출 데이터가 없습니다"}

    summary = ", ".join([f"{r.category}: {r.total:,.0f}원" for r in rows])
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"최근 {days}일 지출 내역: {summary}\n"
        "이 지출 패턴을 분석하고 절약 팁 3가지를 한국어로 간결하게 알려줘."
    )
    return {"advice": response.text, "period_days": days}
