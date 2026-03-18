"""리포트 API 라우터"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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


@router.get("/monthly/pdf")
async def monthly_report_pdf(
    year: int = Query(default=date.today().year, ge=2000, le=2100),
    month: int = Query(default=date.today().month, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """월간 리포트 PDF 다운로드"""
    try:
        from app.services.pdf_report import generate_monthly_pdf
        pdf_bytes = await generate_monthly_pdf(db, year, month)
        filename = f"MoneyLog_{year}년{month}월_리포트.pdf"
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    except Exception as e:
        logger.error(f"PDF 리포트 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="PDF 생성에 실패했습니다.")


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
