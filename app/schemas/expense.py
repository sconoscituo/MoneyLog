"""지출 관련 Pydantic 스키마"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── 카테고리 스키마 ──────────────────────────────────────────────────────────

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=50, description="카테고리 이름")
    icon: str = Field(default="💰", description="이모지 아이콘")
    color: str = Field(default="#6366f1", description="색상 코드")


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── 지출 스키마 ──────────────────────────────────────────────────────────────

class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0, description="금액 (원)")
    memo: str = Field(default="", max_length=200, description="메모")
    note: str = Field(default="", description="추가 메모")
    expense_date: date = Field(default_factory=date.today, description="지출 날짜")
    category_id: int = Field(..., description="카테고리 ID")


class ExpenseCreate(ExpenseBase):
    raw_sms: str = Field(default="", description="원본 SMS 문자")


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    memo: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = None
    expense_date: Optional[date] = None
    category_id: Optional[int] = None


class ExpenseRead(ExpenseBase):
    id: int
    raw_sms: str
    created_at: datetime
    category: CategoryRead

    model_config = {"from_attributes": True}


# ── SMS 파싱 스키마 ──────────────────────────────────────────────────────────

class SMSParseRequest(BaseModel):
    sms_text: str = Field(..., description="카드 결제 문자 원문")


class SMSParseResult(BaseModel):
    success: bool
    amount: Optional[float] = None
    memo: Optional[str] = None
    expense_date: Optional[date] = None
    suggested_category_id: Optional[int] = None
    suggested_category_name: Optional[str] = None
    raw_sms: str = ""
    message: str = ""


# ── AI 카테고리 추천 스키마 ──────────────────────────────────────────────────

class CategorySuggestRequest(BaseModel):
    memo: str = Field(..., description="지출 메모")


class CategorySuggestResult(BaseModel):
    category_id: int
    category_name: str
    confidence: float = Field(ge=0.0, le=1.0)


# ── 예산 스키마 ──────────────────────────────────────────────────────────────

class BudgetBase(BaseModel):
    category_id: int
    amount: float = Field(..., gt=0, description="예산 금액 (원)")
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)


class BudgetCreate(BudgetBase):
    pass


class BudgetRead(BudgetBase):
    id: int
    created_at: datetime
    category: CategoryRead

    model_config = {"from_attributes": True}


class BudgetStatus(BaseModel):
    """예산 대비 실제 지출 현황"""
    category_id: int
    category_name: str
    category_icon: str
    category_color: str
    budget_amount: float
    spent_amount: float
    remaining_amount: float
    usage_rate: float  # 0.0 ~ 1.0+
    is_exceeded: bool


# ── 리포트 스키마 ────────────────────────────────────────────────────────────

class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    category_icon: str
    category_color: str
    total_amount: float
    count: int
    percentage: float


class DailyExpense(BaseModel):
    date: date
    total_amount: float
    count: int


class ReportResponse(BaseModel):
    year: int
    month: int
    total_amount: float
    category_summaries: list[CategorySummary]
    daily_expenses: list[DailyExpense]
    budget_statuses: list[BudgetStatus]
