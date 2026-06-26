from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    item = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    current_stock = Column(Float, nullable=False)
    reorder_threshold = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    date = Column(Date, nullable=False)
    predicted_revenue = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)


class StaffingRecommendation(Base):
    __tablename__ = "staffing_recommendations"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    shift = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    recommended_staff_count = Column(Integer, nullable=False)
    efficiency_score = Column(Float, nullable=True)


class CsvUpload(Base):
    __tablename__ = "csv_uploads"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    filename = Column(String, nullable=False)
    column_mapping = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="pending")
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class AiInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
