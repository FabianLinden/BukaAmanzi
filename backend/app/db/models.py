from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class Municipality(Base):
    __tablename__ = "municipalities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    province: Mapped[Optional[str]] = mapped_column(String(100))
    project_count: Mapped[int] = mapped_column(Integer, default=0)
    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    dashboard_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[list[Project]] = relationship("Project", back_populates="municipality")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    municipality_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("municipalities.id"))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    project_type: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(Date)
    end_date: Mapped[Optional[datetime]] = mapped_column(Date)
    location: Mapped[Optional[str]] = mapped_column(Text)  # WKT or JSON string for dev
    address: Mapped[Optional[str]] = mapped_column(Text)
    budget_allocated: Mapped[Optional[float]] = mapped_column(Float)
    budget_spent: Mapped[Optional[float]] = mapped_column(Float)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    contractor: Mapped[Optional[str]] = mapped_column(String(255))
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    municipality: Mapped[Optional[Municipality]] = relationship("Municipality", back_populates="projects")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    budget_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    financial_year: Mapped[str] = mapped_column(String(9))
    quarter: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(50))
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WebSocketSubscription(Base):
    __tablename__ = "websocket_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subscription_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'municipality', 'project', 'all'
    entity_id: Mapped[Optional[str]] = mapped_column(String(36))  # NULL for 'all' subscriptions
    filters: Mapped[Optional[dict]] = mapped_column(JSON)  # Additional filtering criteria
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Contributor(Base):
    __tablename__ = "contributors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))  # Optional display name
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # Optional contact for follow-up
    organization: Mapped[Optional[str]] = mapped_column(String(255))  # Optional organization affiliation
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reports: Mapped[list["Report"]] = relationship("Report", back_populates="contributor")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    contributor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contributors.id"))  # NULL for fully anonymous reports
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(Text)  # WKT or JSON string for dev
    address: Mapped[Optional[str]] = mapped_column(Text)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'progress_update', 'issue', 'completion', 'quality_concern'
    status: Mapped[str] = mapped_column(String(50), default="published", index=True)  # 'published', 'flagged', 'spam'
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    downvotes: Mapped[int] = mapped_column(Integer, default=0)
    photos: Mapped[Optional[dict]] = mapped_column(JSON)  # Array of photo URLs
    contributor_name: Mapped[Optional[str]] = mapped_column(String(255))  # Display name for attribution
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)  # Internal notes for data quality
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    contributor: Mapped[Optional[Contributor]] = relationship("Contributor", back_populates="reports")
    project: Mapped[Project] = relationship("Project")


class AdminAction(Base):
    __tablename__ = "admin_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    admin_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # Admin identifier
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'report', 'project'
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # 'flag', 'unflag', 'link_to_project', 'update_data'
    reason: Mapped[Optional[str]] = mapped_column(Text)
    action_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # Additional action-specific data
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class FinancialData(Base):
    __tablename__ = "financial_data"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    municipality_id: Mapped[str] = mapped_column(String(36), ForeignKey("municipalities.id"), nullable=False)
    financial_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_budget: Mapped[float] = mapped_column(Float, default=0.0)
    total_actual: Mapped[float] = mapped_column(Float, default=0.0)
    total_capex_budget: Mapped[float] = mapped_column(Float, default=0.0)
    total_capex_actual: Mapped[float] = mapped_column(Float, default=0.0)
    water_related_capex: Mapped[float] = mapped_column(Float, default=0.0)
    infrastructure_budget: Mapped[float] = mapped_column(Float, default=0.0)
    service_delivery_budget: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    expenditure: Mapped[float] = mapped_column(Float, default=0.0)
    surplus_deficit: Mapped[float] = mapped_column(Float, default=0.0)
    budget_variance: Mapped[float] = mapped_column(Float, default=0.0)  # Percentage
    cash_available: Mapped[float] = mapped_column(Float, default=0.0)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    municipality: Mapped[Municipality] = relationship("Municipality")


class DataChangeLog(Base):
    __tablename__ = "data_change_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(36))
    change_type: Mapped[str] = mapped_column(String(20))
    field_changes: Mapped[Optional[dict]] = mapped_column(JSON)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(50), default="etl_pipeline")
    notification_sent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

