"""결제 내역 모델"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    imp_uid = Column(String, unique=True, nullable=False)  # 포트원 고유 결제번호
    merchant_uid = Column(String, unique=True, nullable=False)  # 주문번호
    amount = Column(Integer, nullable=False)  # 결제금액 (원) - FREE/PREMIUM 월 5,900원
    plan = Column(String, nullable=False)  # 구독 플랜
    status = Column(String, default="paid")  # paid/cancelled/failed
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
