"""리포트 생성 서비스"""
from collections import defaultdict
from datetime import date

from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expense import Expense
from app.models.budget import Budget
from app.models.category import Category
from app.schemas.expense import (
    CategorySummary,
    DailyExpense,
    ReportResponse,
    BudgetStatus,
)


async def get_monthly_report(
    db: AsyncSession, year: int, month: int
) -> ReportResponse:
    """월간 리포트 생성"""

    # 해당 월 지출 조회
    expenses_result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(
            extract("year", Expense.expense_date) == year,
            extract("month", Expense.expense_date) == month,
        )
        .order_by(Expense.expense_date)
    )
    expenses = expenses_result.scalars().all()

    # 전체 합계
    total_amount = sum(e.amount for e in expenses)

    # 카테고리별 집계
    cat_totals: dict[int, dict] = {}
    for exp in expenses:
        cid = exp.category_id
        if cid not in cat_totals:
            cat_totals[cid] = {
                "category_id": cid,
                "category_name": exp.category.name,
                "category_icon": exp.category.icon,
                "category_color": exp.category.color,
                "total_amount": 0.0,
                "count": 0,
            }
        cat_totals[cid]["total_amount"] += exp.amount
        cat_totals[cid]["count"] += 1

    category_summaries = [
        CategorySummary(
            **data,
            percentage=round(data["total_amount"] / total_amount * 100, 1)
            if total_amount > 0 else 0.0,
        )
        for data in sorted(
            cat_totals.values(), key=lambda x: x["total_amount"], reverse=True
        )
    ]

    # 일별 집계
    daily: dict[date, dict] = {}
    for exp in expenses:
        d = exp.expense_date
        if d not in daily:
            daily[d] = {"date": d, "total_amount": 0.0, "count": 0}
        daily[d]["total_amount"] += exp.amount
        daily[d]["count"] += 1

    daily_expenses = [
        DailyExpense(**data) for data in sorted(daily.values(), key=lambda x: x["date"])
    ]

    # 예산 현황
    budgets_result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.category))
        .where(Budget.year == year, Budget.month == month)
    )
    budgets = budgets_result.scalars().all()

    budget_statuses = []
    for budget in budgets:
        spent = cat_totals.get(budget.category_id, {}).get("total_amount", 0.0)
        remaining = budget.amount - spent
        usage_rate = spent / budget.amount if budget.amount > 0 else 0.0
        budget_statuses.append(
            BudgetStatus(
                category_id=budget.category_id,
                category_name=budget.category.name,
                category_icon=budget.category.icon,
                category_color=budget.category.color,
                budget_amount=budget.amount,
                spent_amount=spent,
                remaining_amount=remaining,
                usage_rate=round(usage_rate, 3),
                is_exceeded=spent > budget.amount,
            )
        )

    return ReportResponse(
        year=year,
        month=month,
        total_amount=total_amount,
        category_summaries=category_summaries,
        daily_expenses=daily_expenses,
        budget_statuses=budget_statuses,
    )


async def get_weekly_report(
    db: AsyncSession, year: int, week: int
) -> dict:
    """주간 리포트 생성"""
    expenses_result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(
            extract("year", Expense.expense_date) == year,
            extract("week", Expense.expense_date) == week,
        )
        .order_by(Expense.expense_date)
    )
    expenses = expenses_result.scalars().all()

    total_amount = sum(e.amount for e in expenses)

    cat_totals: dict[int, dict] = {}
    for exp in expenses:
        cid = exp.category_id
        if cid not in cat_totals:
            cat_totals[cid] = {
                "category_id": cid,
                "category_name": exp.category.name,
                "category_icon": exp.category.icon,
                "category_color": exp.category.color,
                "total_amount": 0.0,
                "count": 0,
            }
        cat_totals[cid]["total_amount"] += exp.amount
        cat_totals[cid]["count"] += 1

    daily: dict[date, dict] = {}
    for exp in expenses:
        d = exp.expense_date
        if d not in daily:
            daily[d] = {"date": str(d), "total_amount": 0.0, "count": 0}
        daily[d]["total_amount"] += exp.amount
        daily[d]["count"] += 1

    return {
        "year": year,
        "week": week,
        "total_amount": total_amount,
        "category_summaries": list(
            sorted(cat_totals.values(), key=lambda x: x["total_amount"], reverse=True)
        ),
        "daily_expenses": list(sorted(daily.values(), key=lambda x: x["date"])),
    }
