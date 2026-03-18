"""HTML 페이지 라우터 (Jinja2 서버사이드 렌더링)"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, extract, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.expense import Expense
from app.models.category import Category
from app.models.budget import Budget
from app.services.report import get_monthly_report

router = APIRouter(tags=["페이지"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """대시보드 페이지"""
    try:
        today = date.today()
        year, month = today.year, today.month

        report = await get_monthly_report(db, year, month)

        # 최근 지출 5건
        recent_result = await db.execute(
            select(Expense)
            .options(selectinload(Expense.category))
            .order_by(desc(Expense.expense_date), desc(Expense.created_at))
            .limit(5)
        )
        recent_expenses = recent_result.scalars().all()

        # 예산 초과 알림
        exceeded_budgets = [b for b in report.budget_statuses if b.is_exceeded]

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "report": report,
                "recent_expenses": recent_expenses,
                "exceeded_budgets": exceeded_budgets,
                "today": today,
                "current_year": year,
                "current_month": month,
            },
        )
    except Exception as e:
        logger.error(f"대시보드 페이지 오류: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다.")


@router.get("/expenses", response_class=HTMLResponse)
async def expenses_page(
    request: Request,
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db),
):
    """지출 목록/등록 페이지"""
    try:
        today = date.today()
        if not year:
            year = today.year
        if not month:
            month = today.month

        # 지출 목록
        stmt = (
            select(Expense)
            .options(selectinload(Expense.category))
            .where(
                extract("year", Expense.expense_date) == year,
                extract("month", Expense.expense_date) == month,
            )
            .order_by(desc(Expense.expense_date), desc(Expense.created_at))
        )
        expenses_result = await db.execute(stmt)
        expenses = expenses_result.scalars().all()

        # 카테고리 목록 (폼용)
        cats_result = await db.execute(select(Category).order_by(Category.id))
        categories = cats_result.scalars().all()

        total = sum(e.amount for e in expenses)

        return templates.TemplateResponse(
            "expenses.html",
            {
                "request": request,
                "expenses": expenses,
                "categories": categories,
                "total": total,
                "year": year,
                "month": month,
                "today": today,
            },
        )
    except Exception as e:
        logger.error(f"지출 페이지 오류: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다.")


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db),
):
    """리포트 페이지"""
    try:
        today = date.today()
        if not year:
            year = today.year
        if not month:
            month = today.month

        report = await get_monthly_report(db, year, month)

        # 카테고리 목록 (예산 설정용)
        cats_result = await db.execute(select(Category).order_by(Category.id))
        categories = cats_result.scalars().all()

        return templates.TemplateResponse(
            "reports.html",
            {
                "request": request,
                "report": report,
                "categories": categories,
                "year": year,
                "month": month,
                "today": today,
            },
        )
    except Exception as e:
        logger.error(f"리포트 페이지 오류: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다.")
