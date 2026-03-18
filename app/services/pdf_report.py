"""월간 리포트 PDF 생성 서비스"""
import logging
from datetime import date

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession
from weasyprint import HTML

from app.services.report import get_monthly_report

logger = logging.getLogger(__name__)


async def generate_monthly_pdf(db: AsyncSession, year: int, month: int) -> bytes:
    """월간 리포트를 PDF 바이트로 반환한다."""
    # 리포트 데이터 조회
    report = await get_monthly_report(db, year, month)

    # 예산 사용률에 따른 상태 라벨
    for b in report.budget_statuses:
        if b.is_exceeded:
            b.__dict__["status_label"] = "초과"
        elif b.usage_rate >= 0.8:
            b.__dict__["status_label"] = "주의"
        else:
            b.__dict__["status_label"] = "양호"

    # Jinja2 환경 (PDF 전용 템플릿 디렉터리)
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("pdf/monthly_report.html")

    # 카테고리별 지출 비율 바 너비 계산 (최대 100%)
    max_amount = max((c.total_amount for c in report.category_summaries), default=1)

    html_str = template.render(
        report=report,
        year=year,
        month=month,
        today=date.today(),
        max_amount=max_amount,
    )

    # WeasyPrint로 HTML → PDF 변환
    pdf_bytes = HTML(string=html_str, base_url="app/templates").write_pdf()
    logger.info(f"{year}년 {month}월 PDF 리포트 생성 완료 ({len(pdf_bytes)} bytes)")
    return pdf_bytes
