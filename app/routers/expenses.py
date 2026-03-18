"""지출 CRUD API 라우터"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, extract, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.expense import Expense
from app.models.category import Category
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseRead,
    SMSParseRequest, SMSParseResult,
    CategorySuggestRequest, CategorySuggestResult,
    CategoryCreate, CategoryRead,
)
from app.services.expense_parser import parse_sms
from app.services.categorizer import suggest_category

router = APIRouter(prefix="/api/expenses", tags=["지출"])
category_router = APIRouter(prefix="/api/categories", tags=["카테고리"])


# ── 카테고리 API ─────────────────────────────────────────────────────────────

@category_router.get("", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """카테고리 목록 조회"""
    try:
        result = await db.execute(select(Category).order_by(Category.id))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"카테고리 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="카테고리 목록을 불러올 수 없습니다.")


@category_router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """카테고리 생성"""
    try:
        cat = Category(**data.model_dump())
        db.add(cat)
        await db.flush()
        await db.refresh(cat)
        return cat
    except Exception as e:
        logger.error(f"카테고리 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="카테고리 생성에 실패했습니다.")


# ── 지출 API ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ExpenseRead])
async def list_expenses(
    year: Optional[int] = Query(None, description="연도 필터"),
    month: Optional[int] = Query(None, description="월 필터 (1-12)"),
    category_id: Optional[int] = Query(None, description="카테고리 필터"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """지출 목록 조회"""
    try:
        stmt = (
            select(Expense)
            .options(selectinload(Expense.category))
            .order_by(desc(Expense.expense_date), desc(Expense.created_at))
        )
        if year:
            stmt = stmt.where(extract("year", Expense.expense_date) == year)
        if month:
            stmt = stmt.where(extract("month", Expense.expense_date) == month)
        if category_id:
            stmt = stmt.where(Expense.category_id == category_id)

        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"지출 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="지출 목록을 불러올 수 없습니다.")


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(data: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    """지출 등록"""
    try:
        cat = await db.get(Category, data.category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

        expense = Expense(**data.model_dump())
        db.add(expense)
        await db.flush()

        result = await db.execute(
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.id == expense.id)
        )
        return result.scalar_one()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지출 등록 오류: {e}")
        raise HTTPException(status_code=500, detail="지출 등록에 실패했습니다.")


@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """지출 상세 조회"""
    try:
        result = await db.execute(
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()
        if not expense:
            raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다.")
        return expense
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지출 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="지출 내역을 불러올 수 없습니다.")


@router.put("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: int, data: ExpenseUpdate, db: AsyncSession = Depends(get_db)
):
    """지출 수정"""
    try:
        result = await db.execute(
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()
        if not expense:
            raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다.")

        update_data = data.model_dump(exclude_unset=True)
        if "category_id" in update_data:
            cat = await db.get(Category, update_data["category_id"])
            if not cat:
                raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

        for key, value in update_data.items():
            setattr(expense, key, value)

        await db.flush()
        await db.refresh(expense)
        # 관계 재로드
        result = await db.execute(
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.id == expense_id)
        )
        return result.scalar_one()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지출 수정 오류: {e}")
        raise HTTPException(status_code=500, detail="지출 수정에 실패했습니다.")


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """지출 삭제"""
    try:
        expense = await db.get(Expense, expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다.")
        await db.delete(expense)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지출 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="지출 삭제에 실패했습니다.")


# ── SMS 파싱 API ─────────────────────────────────────────────────────────────

@router.post("/parse-sms", response_model=SMSParseResult)
async def parse_sms_text(
    request: SMSParseRequest, db: AsyncSession = Depends(get_db)
):
    """카드 결제 문자를 파싱하여 지출 정보를 추출합니다."""
    try:
        parsed = parse_sms(request.sms_text)
    except Exception as e:
        logger.error(f"SMS 파싱 오류: {e}")
        return SMSParseResult(
            success=False,
            amount=None,
            memo=None,
            expense_date=None,
            suggested_category_id=None,
            suggested_category_name=None,
            raw_sms=request.sms_text,
            message="SMS 파싱 중 오류가 발생했습니다.",
        )

    suggested_category_id = None
    suggested_category_name = None

    if parsed["success"] and parsed.get("memo"):
        try:
            cats_result = await db.execute(select(Category).order_by(Category.id))
            categories = cats_result.scalars().all()
            suggested_id = await suggest_category(parsed["memo"], categories)
            if suggested_id:
                cat = await db.get(Category, suggested_id)
                suggested_category_id = suggested_id
                suggested_category_name = cat.name if cat else None
        except Exception as e:
            logger.error(f"카테고리 추천 오류: {e}")

    return SMSParseResult(
        success=parsed["success"],
        amount=parsed.get("amount"),
        memo=parsed.get("memo"),
        expense_date=parsed.get("expense_date"),
        suggested_category_id=suggested_category_id,
        suggested_category_name=suggested_category_name,
        raw_sms=request.sms_text,
        message=parsed["message"],
    )


# ── AI 카테고리 추천 API ──────────────────────────────────────────────────────

@router.post("/suggest-category", response_model=CategorySuggestResult)
async def suggest_category_api(
    request: CategorySuggestRequest, db: AsyncSession = Depends(get_db)
):
    """메모를 기반으로 카테고리를 AI가 추천합니다."""
    try:
        cats_result = await db.execute(select(Category).order_by(Category.id))
        categories = cats_result.scalars().all()

        if not categories:
            raise HTTPException(status_code=404, detail="등록된 카테고리가 없습니다.")

        suggested_id = await suggest_category(request.memo, categories)
        if not suggested_id:
            suggested_id = categories[0].id

        cat = await db.get(Category, suggested_id)
        return CategorySuggestResult(
            category_id=cat.id,
            category_name=cat.name,
            confidence=0.8 if suggested_id else 0.3,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"카테고리 추천 API 오류: {e}")
        raise HTTPException(status_code=500, detail="카테고리 추천에 실패했습니다.")
