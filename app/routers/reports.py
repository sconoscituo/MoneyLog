"""리포트 API 라우터"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.expense import ReportResponse
from app.services.report import get_monthly_report, get_weekly_report

router = APIRouter(prefix="/api/reports", tags=["리포트"])
logger = logging.getLogger(__name__)


@router.get("/monthly", response_model=ReportResponse)
async def monthly_report(
    year: int = Query(default=date.today().year, ge=2000, le=2100),
    month: int = Query(default=date.today().month, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """월간 리포트 조회"""
    try:
        return await get_monthly_report(db, year, month)
    except Exception as e:
        logger.error(f"월간 리포트 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="리포트를 불러올 수 없습니다.")


@router.get("/weekly")
async def weekly_report(
    year: int = Query(default=date.today().year, ge=2000, le=2100),
    week: int = Query(default=date.today().isocalendar()[1], ge=1, le=53),
    db: AsyncSession = Depends(get_db),
):
    """주간 리포트 조회"""
    try:
        return await get_weekly_report(db, year, week)
    except Exception as e:
        logger.error(f"주간 리포트 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="주간 리포트를 불러올 수 없습니다.")
