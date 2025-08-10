"""Add FinancialData table for municipal treasury integration

Revision ID: 001_financial_data
Revises: base
Create Date: 2024-08-10 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '001_financial_data'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add FinancialData table and related indexes"""
    
    # Create financial_data table
    op.create_table(
        'financial_data',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('municipality_id', sa.String(36), nullable=False),
        sa.Column('financial_year', sa.Integer(), nullable=False),
        sa.Column('total_budget', sa.Float(), nullable=True, default=0.0),
        sa.Column('total_actual', sa.Float(), nullable=True, default=0.0),
        sa.Column('total_capex_budget', sa.Float(), nullable=True, default=0.0),
        sa.Column('total_capex_actual', sa.Float(), nullable=True, default=0.0),
        sa.Column('water_related_capex', sa.Float(), nullable=True, default=0.0),
        sa.Column('infrastructure_budget', sa.Float(), nullable=True, default=0.0),
        sa.Column('service_delivery_budget', sa.Float(), nullable=True, default=0.0),
        sa.Column('revenue', sa.Float(), nullable=True, default=0.0),
        sa.Column('expenditure', sa.Float(), nullable=True, default=0.0),
        sa.Column('surplus_deficit', sa.Float(), nullable=True, default=0.0),
        sa.Column('budget_variance', sa.Float(), nullable=True, default=0.0),
        sa.Column('cash_available', sa.Float(), nullable=True, default=0.0),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipality_id'], ['municipalities.id'])
    )
    
    # Create indexes for performance
    op.create_index('ix_financial_data_municipality_id', 'financial_data', ['municipality_id'])
    op.create_index('ix_financial_data_financial_year', 'financial_data', ['financial_year'])
    op.create_index('ix_financial_data_content_hash', 'financial_data', ['content_hash'])
    op.create_index('ix_financial_data_municipality_year', 'financial_data', ['municipality_id', 'financial_year'], unique=True)


def downgrade() -> None:
    """Drop FinancialData table and indexes"""
    
    # Drop indexes
    op.drop_index('ix_financial_data_municipality_year', table_name='financial_data')
    op.drop_index('ix_financial_data_content_hash', table_name='financial_data')
    op.drop_index('ix_financial_data_financial_year', table_name='financial_data')
    op.drop_index('ix_financial_data_municipality_id', table_name='financial_data')
    
    # Drop table
    op.drop_table('financial_data')
