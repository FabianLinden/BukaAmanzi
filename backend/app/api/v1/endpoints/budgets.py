from typing import Any, List, Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Budget
from app.db.session import get_db_session
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


class BudgetIn(BaseModel):
    project_id: str
    budget_type: str  # 'allocated', 'revised', 'spent'
    amount: float
    currency: str = "ZAR"
    financial_year: str  # '2023/2024'
    quarter: Optional[int] = None
    source: str
    raw_data: Optional[dict] = None


class BudgetOut(BaseModel):
    id: str
    project_id: str
    budget_type: str
    amount: float
    currency: str
    financial_year: str
    quarter: Optional[int] = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[BudgetOut])
async def list_budgets(
    project_id: Optional[str] = Query(default=None),
    budget_type: Optional[str] = Query(default=None),
    financial_year: Optional[str] = Query(default=None),
    quarter: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """List budgets with filtering and pagination."""
    filters = []
    
    if project_id:
        filters.append(Budget.project_id == project_id)
    if budget_type:
        filters.append(Budget.budget_type == budget_type)
    if financial_year:
        filters.append(Budget.financial_year == financial_year)
    if quarter:
        filters.append(Budget.quarter == quarter)

    stmt = select(Budget).where(and_(*filters)) if filters else select(Budget)
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    
    result = await session.execute(stmt)
    budgets = result.scalars().all()
    
    return [
        BudgetOut(
            id=budget.id,
            project_id=budget.project_id,
            budget_type=budget.budget_type,
            amount=budget.amount,
            currency=budget.currency,
            financial_year=budget.financial_year,
            quarter=budget.quarter,
            source=budget.source,
            created_at=budget.created_at,
        )
        for budget in budgets
    ]


@router.get("/{budget_id}", response_model=BudgetOut)
async def get_budget(
    budget_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Get detailed budget information."""
    stmt = select(Budget).where(Budget.id == budget_id)
    result = await session.execute(stmt)
    budget = result.scalar_one_or_none()
    
    if budget is None:
        raise HTTPException(404, detail="Budget not found")
    
    return BudgetOut(
        id=budget.id,
        project_id=budget.project_id,
        budget_type=budget.budget_type,
        amount=budget.amount,
        currency=budget.currency,
        financial_year=budget.financial_year,
        quarter=budget.quarter,
        source=budget.source,
        created_at=budget.created_at,
    )


@router.post("/", response_model=BudgetOut)
async def create_budget(
    budget_data: BudgetIn,
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Create a new budget record."""
    budget = Budget(
        id=str(uuid4()),
        project_id=budget_data.project_id,
        budget_type=budget_data.budget_type,
        amount=budget_data.amount,
        currency=budget_data.currency,
        financial_year=budget_data.financial_year,
        quarter=budget_data.quarter,
        source=budget_data.source,
        raw_data=budget_data.raw_data,
        created_at=datetime.utcnow(),
    )
    
    session.add(budget)
    await session.commit()
    await session.refresh(budget)
    
    logger.info(f"Created new budget: {budget.id} for project: {budget.project_id}")
    
    return BudgetOut(
        id=budget.id,
        project_id=budget.project_id,
        budget_type=budget.budget_type,
        amount=budget.amount,
        currency=budget.currency,
        financial_year=budget.financial_year,
        quarter=budget.quarter,
        source=budget.source,
        created_at=budget.created_at,
    )


@router.get("/project/{project_id}/summary")
async def get_project_budget_summary(
    project_id: str,
    financial_year: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Get budget summary for a specific project."""
    filters = [Budget.project_id == project_id]
    
    if financial_year:
        filters.append(Budget.financial_year == financial_year)
    
    stmt = select(Budget).where(and_(*filters))
    result = await session.execute(stmt)
    budgets = result.scalars().all()
    
    if not budgets:
        raise HTTPException(404, detail="No budget data found for project")
    
    # Calculate summary
    allocated_total = sum(b.amount for b in budgets if b.budget_type == "allocated")
    revised_total = sum(b.amount for b in budgets if b.budget_type == "revised")
    spent_total = sum(b.amount for b in budgets if b.budget_type == "spent")
    
    # Use revised if available, otherwise allocated
    final_budget = revised_total if revised_total > 0 else allocated_total
    remaining = final_budget - spent_total
    spent_percentage = (spent_total / final_budget * 100) if final_budget > 0 else 0
    
    return {
        "project_id": project_id,
        "financial_year": financial_year,
        "budget_allocated": allocated_total,
        "budget_revised": revised_total,
        "budget_final": final_budget,
        "amount_spent": spent_total,
        "amount_remaining": remaining,
        "spent_percentage": round(spent_percentage, 2),
        "budget_records": len(budgets),
    }
