"""MoneyLog FastAPI 메인 앱"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import init_db
from app.routers import expenses as expenses_router
from app.routers import budgets as budgets_router
from app.routers import reports as reports_router
from app.routers import pages as pages_router
from app.routers import recurring as recurring_router
from app.routers import exports as exports_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── 기본 카테고리 시드 데이터 ─────────────────────────────────────────────────
DEFAULT_CATEGORIES = [
    {"name": "식비", "icon": "🍽️", "color": "#ef4444"},
    {"name": "배달", "icon": "🛵", "color": "#f97316"},
    {"name": "교통", "icon": "🚌", "color": "#3b82f6"},
    {"name": "쇼핑", "icon": "🛍️", "color": "#8b5cf6"},
    {"name": "의료/건강", "icon": "💊", "color": "#10b981"},
    {"name": "문화/여가", "icon": "🎬", "color": "#f59e0b"},
    {"name": "통신", "icon": "📱", "color": "#06b6d4"},
    {"name": "공과금", "icon": "🏠", "color": "#64748b"},
    {"name": "구독", "icon": "🔔", "color": "#a855f7"},
    {"name": "여행", "icon": "✈️", "color": "#0ea5e9"},
    {"name": "기타", "icon": "💰", "color": "#6b7280"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트 핸들러"""
    logger.info("MoneyLog 앱 시작 중...")

    # DB 초기화
    await init_db()
    logger.info("데이터베이스 초기화 완료")

    # 기본 카테고리 시드
    await seed_default_categories()
    logger.info("기본 카테고리 시드 완료")

    # 반복 지출 자동 등록 체크 (앱 시작 시 오늘 날짜 기준)
    await apply_recurring_expenses()
    logger.info("반복 지출 자동 등록 체크 완료")

    yield

    logger.info("MoneyLog 앱 종료")


async def apply_recurring_expenses():
    """오늘 날짜 기준으로 반복 지출을 자동 등록한다.

    - monthly: day_of_month == 오늘 일(day)
    - weekly:  day_of_month == 오늘 요일(0=월~6=일)
    이미 오늘 등록된 항목은 중복 등록하지 않는다 (last_applied 날짜 비교).
    """
    from datetime import date, datetime
    from app.database import AsyncSessionLocal
    from app.models.recurring import RecurringExpense
    from app.models.expense import Expense
    from sqlalchemy import select

    today = date.today()
    today_weekday = today.weekday()  # 0=월요일

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RecurringExpense).where(RecurringExpense.is_active == True)  # noqa: E712
        )
        items = result.scalars().all()

        registered = 0
        for item in items:
            # 이미 오늘 등록했으면 건너뜀
            if item.last_applied and item.last_applied.date() == today:
                continue

            # 주기 조건 확인
            should_apply = False
            if item.frequency == "monthly" and item.day_of_month == today.day:
                should_apply = True
            elif item.frequency == "weekly" and item.day_of_month == today_weekday:
                should_apply = True

            if should_apply:
                expense = Expense(
                    amount=item.amount,
                    category_id=item.category_id,
                    memo=item.description or "반복 지출",
                    expense_date=today,
                )
                db.add(expense)
                item.last_applied = datetime.now()
                registered += 1

        if registered:
            await db.commit()
            logger.info(f"반복 지출 {registered}건 자동 등록됨")


async def seed_default_categories():
    """기본 카테고리가 없으면 생성"""
    from app.database import AsyncSessionLocal
    from app.models.category import Category
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Category))
        existing = result.scalars().all()

        if not existing:
            for cat_data in DEFAULT_CATEGORIES:
                cat = Category(**cat_data, is_default=True)
                db.add(cat)
            await db.commit()
            logger.info(f"{len(DEFAULT_CATEGORIES)}개 기본 카테고리 생성됨")


# ── FastAPI 앱 인스턴스 ──────────────────────────────────────────────────────
app = FastAPI(
    title="MoneyLog",
    description="개인 가계부 & 지출 추적 앱",
    version="1.0.0",
    lifespan=lifespan,
)

# 정적 파일
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 라우터 등록
app.include_router(pages_router.router)
app.include_router(expenses_router.router)
app.include_router(expenses_router.category_router)
app.include_router(budgets_router.router)
app.include_router(reports_router.router)
app.include_router(recurring_router.router)
app.include_router(exports_router.router)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "base.html",
        {"request": request, "error": "페이지를 찾을 수 없습니다."},
        status_code=404,
    )
