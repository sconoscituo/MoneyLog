"""반복 지출 모델"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecurringExpense(Base):
    """반복 지출 모델 — 매월/매주 자동으로 지출을 등록한다."""
    __tablename__ = "recurring_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)              # 금액 (원)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(200), default="")        # 설명/메모
    frequency: Mapped[str] = mapped_column(String(10), nullable=False)       # monthly / weekly
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False)       # 매월 N일 (weekly는 요일 0=월)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)           # 활성화 여부
    last_applied: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 마지막 자동 등록 시각
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 관계
    category: Mapped["Category"] = relationship("Category")

    def __repr__(self) -> str:
        return f"<RecurringExpense(id={self.id}, amount={self.amount}, freq={self.frequency})>"
