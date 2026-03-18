"""반복 지출 CRUD API 라우터"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.recurring import RecurringExpense
from app.models.category import Category

router = APIRouter(prefix="/api/recurring", tags=["반복 지출"])
logger = logging.getLogger(__name__)


# ── 스키마 ───────────────────────────────────────────────────────────────────

class RecurringCreate(BaseModel):
    amount: float = Field(..., gt=0, description="금액 (원)")
    category_id: int = Field(..., description="카테고리 ID")
    description: str = Field(default="", max_length=200, description="설명/메모")
    frequency: str = Field(..., pattern="^(monthly|weekly)$", description="주기: monthly/weekly")
    day_of_month: int = Field(..., ge=1, le=31, description="매월 N일 또는 요일(0=월~6=일)")
    is_active: bool = Field(default=True, description="활성화 여부")


class RecurringUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=200)
    frequency: Optional[str] = Field(None, pattern="^(monthly|weekly)$")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    is_active: Optional[bool] = None


class RecurringRead(BaseModel):
    id: int
    amount: float
    category_id: int
    description: str
    frequency: str
    day_of_month: int
    is_active: bool
    category_name: str
    category_icon: str
    category_color: str

    model_config = {"from_attributes": True}


# ── API 엔드포인트 ────────────────────────────────────────────────────────────

@router.get("", response_model=list[RecurringRead])
async def list_recurring(db: AsyncSession = Depends(get_db)):
    """반복 지출 목록 조회"""
    try:
        result = await db.execute(
            select(RecurringExpense)
            .options(selectinload(RecurringExpense.category))
            .order_by(RecurringExpense.id)
        )
        items = result.scalars().all()
        return [
            RecurringRead(
                id=r.id,
                amount=r.amount,
                category_id=r.category_id,
                description=r.description,
                frequency=r.frequency,
                day_of_month=r.day_of_month,
                is_active=r.is_active,
                category_name=r.category.name,
                category_icon=r.category.icon,
                category_color=r.category.color,
            )
            for r in items
        ]
    except Exception as e:
        logger.error(f"반복 지출 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="반복 지출 목록을 불러올 수 없습니다.")


@router.post("", response_model=RecurringRead, status_code=status.HTTP_201_CREATED)
async def create_recurring(data: RecurringCreate, db: AsyncSession = Depends(get_db)):
    """반복 지출 등록"""
    try:
        cat = await db.get(Category, data.category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

        item = RecurringExpense(**data.model_dump())
        db.add(item)
        await db.flush()
        await db.refresh(item)

        result = await db.execute(
            select(RecurringExpense)
            .options(selectinload(RecurringExpense.category))
            .where(RecurringExpense.id == item.id)
        )
        r = result.scalar_one()
        return RecurringRead(
            id=r.id,
            amount=r.amount,
            category_id=r.category_id,
            description=r.description,
            frequency=r.frequency,
            day_of_month=r.day_of_month,
            is_active=r.is_active,
            category_name=r.category.name,
            category_icon=r.category.icon,
            category_color=r.category.color,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"반복 지출 등록 오류: {e}")
        raise HTTPException(status_code=500, detail="반복 지출 등록에 실패했습니다.")


@router.put("/{item_id}", response_model=RecurringRead)
async def update_recurring(
    item_id: int, data: RecurringUpdate, db: AsyncSession = Depends(get_db)
):
    """반복 지출 수정"""
    try:
        result = await db.execute(
            select(RecurringExpense)
            .options(selectinload(RecurringExpense.category))
            .where(RecurringExpense.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="반복 지출을 찾을 수 없습니다.")

        update_data = data.model_dump(exclude_unset=True)
        if "category_id" in update_data:
            cat = await db.get(Category, update_data["category_id"])
            if not cat:
                raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

        for key, value in update_data.items():
            setattr(item, key, value)

        await db.flush()
        result2 = await db.execute(
            select(RecurringExpense)
            .options(selectinload(RecurringExpense.category))
            .where(RecurringExpense.id == item_id)
        )
        r = result2.scalar_one()
        return RecurringRead(
            id=r.id,
            amount=r.amount,
            category_id=r.category_id,
            description=r.description,
            frequency=r.frequency,
            day_of_month=r.day_of_month,
            is_active=r.is_active,
            category_name=r.category.name,
            category_icon=r.category.icon,
            category_color=r.category.color,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"반복 지출 수정 오류: {e}")
        raise HTTPException(status_code=500, detail="반복 지출 수정에 실패했습니다.")


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring(item_id: int, db: AsyncSession = Depends(get_db)):
    """반복 지출 삭제"""
    try:
        item = await db.get(RecurringExpense, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="반복 지출을 찾을 수 없습니다.")
        await db.delete(item)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"반복 지출 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="반복 지출 삭제에 실패했습니다.")
