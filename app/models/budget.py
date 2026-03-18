"""예산 모델"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Budget(Base):
    """월별 카테고리 예산 모델"""
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # 예산 금액 (원)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 관계
    category: Mapped["Category"] = relationship("Category", back_populates="budgets")

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, category_id={self.category_id}, amount={self.amount})>"
