"""카테고리 모델"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    """지출 카테고리 모델"""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="💰")
    color: Mapped[str] = mapped_column(String(20), default="#6366f1")  # Tailwind indigo-500
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 관계
    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship("Budget", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"
