"""예산 API 라우터"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.budget import Budget
from app.models.category import Category
from app.schemas.expense import BudgetCreate, BudgetRead

router = APIRouter(prefix="/api/budgets", tags=["예산"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[BudgetRead])
async def list_budgets(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """예산 목록 조회"""
    try:
        stmt = select(Budget).options(selectinload(Budget.category))
        if year:
            stmt = stmt.where(Budget.year == year)
        if month:
            stmt = stmt.where(Budget.month == month)
        result = await db.execute(stmt.order_by(Budget.year.desc(), Budget.month.desc()))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"예산 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="예산 목록을 불러올 수 없습니다.")


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_budget(
    data: BudgetCreate, db: AsyncSession = Depends(get_db)
):
    """예산 설정 (같은 연월+카테고리면 업데이트)"""
    try:
        cat = await db.get(Category, data.category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

        # 기존 예산 조회
        result = await db.execute(
            select(Budget).where(
                Budget.category_id == data.category_id,
                Budget.year == data.year,
                Budget.month == data.month,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.amount = data.amount
            await db.flush()
            budget = existing
        else:
            budget = Budget(**data.model_dump())
            db.add(budget)
            await db.flush()

        result = await db.execute(
            select(Budget)
            .options(selectinload(Budget.category))
            .where(Budget.id == budget.id)
        )
        return result.scalar_one()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예산 설정 오류: {e}")
        raise HTTPException(status_code=500, detail="예산 설정에 실패했습니다.")


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: int, db: AsyncSession = Depends(get_db)):
    """예산 삭제"""
    try:
        budget = await db.get(Budget, budget_id)
        if not budget:
            raise HTTPException(status_code=404, detail="예산을 찾을 수 없습니다.")
        await db.delete(budget)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예산 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="예산 삭제에 실패했습니다.")
