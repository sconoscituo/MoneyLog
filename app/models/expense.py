"""지출 모델"""
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Expense(Base):
    """지출 내역 모델"""
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # 금액 (원)
    memo: Mapped[str] = mapped_column(String(200), default="")    # 메모
    note: Mapped[str] = mapped_column(Text, default="")           # 추가 메모
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    # 문자 파싱으로 생성된 경우 원본 문자 저장
    raw_sms: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 관계
    category: Mapped["Category"] = relationship("Category", back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense(id={self.id}, amount={self.amount}, memo={self.memo})>"
