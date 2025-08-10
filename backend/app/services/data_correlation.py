from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Municipality, FinancialData, DataChangeLog
from app.db.session import async_session_factory
from app.realtime.notifier import DataChangeNotifier
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCorrelationService:
    """Service to correlate DWS project data with municipal financial data"""
    
    def __init__(self, notification_manager: DataChangeNotifier):
        self.notification_manager = notification_manager
        self.correlation_cache: Dict[str, Any] = {}
    
    async def correlate_project_financial_data(self, project_id: str) -> Dict[str, Any]:
        """Correlate a specific project with municipal financial data"""
        try:
            async with async_session_factory() as session:
                # Get project details
                project_stmt = select(Project).where(Project.id == project_id)
                project_result = await session.execute(project_stmt)
                project = project_result.scalar_one_or_none()
                
                if not project:
                    logger.warning(f"Project {project_id} not found for correlation")
                    return {}
                
                if not project.municipality_id:
                    logger.warning(f"Project {project.name} has no municipality assigned")
                    return {'project': project.name, 'correlation': 'no_municipality'}
                
                # Get municipality financial data
                financial_stmt = select(FinancialData).where(
                    FinancialData.municipality_id == project.municipality_id
                ).order_by(FinancialData.financial_year.desc())
                financial_result = await session.execute(financial_stmt)
                financial_data = financial_result.scalars().all()
                
                # Build correlation analysis
                correlation = await self._build_project_financial_correlation(
                    project, financial_data, session
                )
                
                return correlation
                
        except Exception as e:
            logger.error(f"Error correlating project {project_id}: {str(e)}")
            raise
    
    async def _build_project_financial_correlation(
        self, 
        project: Project, 
        financial_data: List[FinancialData],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Build detailed correlation between project and financial data"""
        
        correlation = {
            'project_id': project.id,
            'project_name': project.name,
            'municipality_id': project.municipality_id,
            'project_budget': {
                'allocated': project.budget_allocated or 0,
                'spent': project.budget_spent or 0,
                'progress_percentage': project.progress_percentage,
            },
            'municipal_context': {},
            'correlations': {},
            'insights': [],
            'risk_indicators': []
        }
        
        if not financial_data:
            correlation['insights'].append("No municipal financial data available for correlation")
            return correlation
        
        # Get municipality info
        municipality_stmt = select(Municipality).where(Municipality.id == project.municipality_id)
        municipality_result = await session.execute(municipality_stmt)
        municipality = municipality_result.scalar_one_or_none()
        
        if municipality:
            correlation['municipality_name'] = municipality.name
            correlation['municipality_code'] = municipality.code
            correlation['province'] = municipality.province
        
        # Analyze financial data across years
        latest_financial = financial_data[0] if financial_data else None
        
        if latest_financial:
            correlation['municipal_context'] = {
                'latest_year': latest_financial.financial_year,
                'total_budget': latest_financial.total_budget,
                'total_actual': latest_financial.total_actual,
                'water_related_capex': latest_financial.water_related_capex,
                'infrastructure_budget': latest_financial.infrastructure_budget,
                'surplus_deficit': latest_financial.surplus_deficit,
                'budget_variance': latest_financial.budget_variance
            }
        
        # Calculate correlations and insights
        await self._analyze_budget_correlations(project, financial_data, correlation)
        await self._analyze_capacity_indicators(project, financial_data, correlation)
        await self._analyze_risk_factors(project, financial_data, correlation)
        
        return correlation
    
    async def _analyze_budget_correlations(
        self, 
        project: Project, 
        financial_data: List[FinancialData],
        correlation: Dict[str, Any]
    ) -> None:
        """Analyze budget-related correlations"""
        
        if not financial_data or not project.budget_allocated:
            return
        
        latest_financial = financial_data[0]
        project_budget = project.budget_allocated
        
        # Calculate project budget as percentage of municipal infrastructure budget
        if latest_financial.infrastructure_budget > 0:
            project_infra_percentage = (project_budget / latest_financial.infrastructure_budget) * 100
            correlation['correlations']['project_vs_infrastructure_budget'] = {
                'percentage': round(project_infra_percentage, 2),
                'significance': 'high' if project_infra_percentage > 20 else 'medium' if project_infra_percentage > 5 else 'low'
            }
            
            if project_infra_percentage > 30:
                correlation['insights'].append(f"Project represents {project_infra_percentage:.1f}% of municipal infrastructure budget - major investment")
            elif project_infra_percentage > 10:
                correlation['insights'].append(f"Project represents {project_infra_percentage:.1f}% of municipal infrastructure budget - significant investment")
        
        # Calculate project budget vs water-related capex
        if latest_financial.water_related_capex > 0:
            project_water_percentage = (project_budget / latest_financial.water_related_capex) * 100
            correlation['correlations']['project_vs_water_capex'] = {
                'percentage': round(project_water_percentage, 2),
                'significance': 'high' if project_water_percentage > 50 else 'medium' if project_water_percentage > 20 else 'low'
            }
            
            if project_water_percentage > 100:
                correlation['insights'].append(f"Project budget exceeds municipal water capex by {project_water_percentage - 100:.1f}% - external funding likely")
            elif project_water_percentage > 50:
                correlation['insights'].append(f"Project represents {project_water_percentage:.1f}% of municipal water capex - major water investment")
        
        # Calculate project budget vs total municipal budget
        if latest_financial.total_budget > 0:
            project_total_percentage = (project_budget / latest_financial.total_budget) * 100
            correlation['correlations']['project_vs_total_budget'] = {
                'percentage': round(project_total_percentage, 2),
                'significance': 'high' if project_total_percentage > 5 else 'medium' if project_total_percentage > 1 else 'low'
            }
    
    async def _analyze_capacity_indicators(
        self, 
        project: Project, 
        financial_data: List[FinancialData],
        correlation: Dict[str, Any]
    ) -> None:
        """Analyze municipal capacity indicators"""
        
        if len(financial_data) < 2:
            return
        
        latest_financial = financial_data[0]
        previous_financial = financial_data[1]
        
        # Financial health indicators
        correlation['correlations']['financial_health'] = {}
        
        # Budget variance trend
        budget_variance_change = latest_financial.budget_variance - previous_financial.budget_variance
        correlation['correlations']['financial_health']['budget_variance_trend'] = {
            'current': latest_financial.budget_variance,
            'previous': previous_financial.budget_variance,
            'change': round(budget_variance_change, 2),
            'improving': budget_variance_change > 0
        }
        
        # Infrastructure investment trend
        infra_budget_change = latest_financial.infrastructure_budget - previous_financial.infrastructure_budget
        infra_growth_rate = (infra_budget_change / previous_financial.infrastructure_budget * 100) if previous_financial.infrastructure_budget > 0 else 0
        
        correlation['correlations']['financial_health']['infrastructure_trend'] = {
            'growth_rate': round(infra_growth_rate, 2),
            'growing': infra_growth_rate > 0
        }
        
        if infra_growth_rate > 20:
            correlation['insights'].append(f"Infrastructure budget increased by {infra_growth_rate:.1f}% - strong investment capacity")
        elif infra_growth_rate < -10:
            correlation['insights'].append(f"Infrastructure budget decreased by {abs(infra_growth_rate):.1f}% - potential capacity constraints")
        
        # Water capex trend
        water_capex_change = latest_financial.water_related_capex - previous_financial.water_related_capex
        water_growth_rate = (water_capex_change / previous_financial.water_related_capex * 100) if previous_financial.water_related_capex > 0 else 0
        
        correlation['correlations']['financial_health']['water_investment_trend'] = {
            'growth_rate': round(water_growth_rate, 2),
            'growing': water_growth_rate > 0
        }
    
    async def _analyze_risk_factors(
        self, 
        project: Project, 
        financial_data: List[FinancialData],
        correlation: Dict[str, Any]
    ) -> None:
        """Analyze risk factors for project delivery"""
        
        if not financial_data:
            return
        
        latest_financial = financial_data[0]
        
        # Budget deficit risk
        if latest_financial.surplus_deficit < 0:
            deficit_severity = abs(latest_financial.surplus_deficit / latest_financial.total_budget * 100) if latest_financial.total_budget > 0 else 0
            
            if deficit_severity > 10:
                correlation['risk_indicators'].append({
                    'type': 'financial_deficit',
                    'severity': 'high',
                    'message': f"Municipality has {deficit_severity:.1f}% budget deficit - project funding at risk"
                })
            elif deficit_severity > 5:
                correlation['risk_indicators'].append({
                    'type': 'financial_deficit',
                    'severity': 'medium',
                    'message': f"Municipality has {deficit_severity:.1f}% budget deficit - monitor project funding"
                })
        
        # Low water investment risk
        if latest_financial.water_related_capex > 0 and latest_financial.infrastructure_budget > 0:
            water_investment_ratio = latest_financial.water_related_capex / latest_financial.infrastructure_budget * 100
            
            if water_investment_ratio < 10:
                correlation['risk_indicators'].append({
                    'type': 'low_water_investment',
                    'severity': 'medium',
                    'message': f"Water investment is only {water_investment_ratio:.1f}% of infrastructure budget - may indicate low priority"
                })
        
        # Budget variance risk
        if abs(latest_financial.budget_variance) > 15:
            correlation['risk_indicators'].append({
                'type': 'budget_variance',
                'severity': 'medium' if abs(latest_financial.budget_variance) < 25 else 'high',
                'message': f"High budget variance ({latest_financial.budget_variance:.1f}%) indicates poor financial planning"
            })
        
        # Project size vs municipal capacity
        if project.budget_allocated and latest_financial.total_budget > 0:
            project_size_ratio = project.budget_allocated / latest_financial.total_budget * 100
            
            if project_size_ratio > 50:
                correlation['risk_indicators'].append({
                    'type': 'project_size_risk',
                    'severity': 'high',
                    'message': f"Project is {project_size_ratio:.1f}% of municipal budget - may strain capacity"
                })
            elif project_size_ratio > 25:
                correlation['risk_indicators'].append({
                    'type': 'project_size_risk',
                    'severity': 'medium',
                    'message': f"Project is {project_size_ratio:.1f}% of municipal budget - significant undertaking"
                })
    
    async def correlate_all_projects(self) -> Dict[str, Any]:
        """Correlate all projects with financial data"""
        try:
            async with async_session_factory() as session:
                # Get all projects
                projects_stmt = select(Project).where(Project.municipality_id.isnot(None))
                projects_result = await session.execute(projects_stmt)
                projects = projects_result.scalars().all()
                
                correlations = []
                summary_stats = {
                    'total_projects': len(projects),
                    'projects_with_financial_data': 0,
                    'high_risk_projects': 0,
                    'major_investments': 0,
                    'total_project_value': 0,
                    'provinces': {},
                    'correlation_timestamp': datetime.utcnow().isoformat()
                }
                
                for project in projects:
                    try:
                        correlation = await self.correlate_project_financial_data(project.id)
                        if correlation:
                            correlations.append(correlation)
                            
                            # Check if project has meaningful financial data
                            has_financial_data = (
                                'municipal_context' in correlation and 
                                correlation['municipal_context'] and
                                'No municipal financial data available' not in str(correlation.get('insights', []))
                            )
                            
                            if has_financial_data:
                                summary_stats['projects_with_financial_data'] += 1
                            
                            # Update summary statistics
                            if project.budget_allocated:
                                summary_stats['total_project_value'] += project.budget_allocated
                            
                            # Count high risk projects
                            if correlation.get('risk_indicators') and len(correlation['risk_indicators']) > 1:
                                summary_stats['high_risk_projects'] += 1
                            
                            # Count major investments
                            project_correlations = correlation.get('correlations', {})
                            if (project_correlations.get('project_vs_infrastructure_budget', {}).get('significance') == 'high' or
                                project_correlations.get('project_vs_water_capex', {}).get('significance') == 'high'):
                                summary_stats['major_investments'] += 1
                            
                            # Province statistics
                            province = correlation.get('province', 'Unknown')
                            if province not in summary_stats['provinces']:
                                summary_stats['provinces'][province] = {
                                    'projects': 0,
                                    'total_value': 0,
                                    'high_risk': 0
                                }
                            
                            summary_stats['provinces'][province]['projects'] += 1
                            if project.budget_allocated:
                                summary_stats['provinces'][province]['total_value'] += project.budget_allocated
                            if correlation.get('risk_indicators') and len(correlation['risk_indicators']) > 1:
                                summary_stats['provinces'][province]['high_risk'] += 1
                        
                        # Add small delay to prevent overwhelming the system
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error correlating project {project.id}: {str(e)}")
                        continue
                
                return {
                    'summary': summary_stats,
                    'correlations': correlations
                }
                
        except Exception as e:
            logger.error(f"Error in bulk correlation analysis: {str(e)}")
            raise
    
    async def get_municipal_investment_overview(self, municipality_id: str) -> Dict[str, Any]:
        """Get investment overview for a specific municipality"""
        try:
            async with async_session_factory() as session:
                # Get municipality details
                municipality_stmt = select(Municipality).where(Municipality.id == municipality_id)
                municipality_result = await session.execute(municipality_stmt)
                municipality = municipality_result.scalar_one_or_none()
                
                if not municipality:
                    return {}
                
                # Get municipality projects
                projects_stmt = select(Project).where(Project.municipality_id == municipality_id)
                projects_result = await session.execute(projects_stmt)
                projects = projects_result.scalars().all()
                
                # Get financial data
                financial_stmt = select(FinancialData).where(
                    FinancialData.municipality_id == municipality_id
                ).order_by(FinancialData.financial_year.desc())
                financial_result = await session.execute(financial_stmt)
                financial_data = financial_result.scalars().all()
                
                # Build overview
                overview = {
                    'municipality': {
                        'id': municipality.id,
                        'name': municipality.name,
                        'code': municipality.code,
                        'province': municipality.province
                    },
                    'projects_summary': {
                        'total_projects': len(projects),
                        'total_allocated': sum(p.budget_allocated or 0 for p in projects),
                        'total_spent': sum(p.budget_spent or 0 for p in projects),
                        'average_progress': sum(p.progress_percentage for p in projects) / len(projects) if projects else 0,
                        'status_breakdown': {}
                    },
                    'financial_summary': {},
                    'investment_efficiency': {},
                    'recommendations': []
                }
                
                # Project status breakdown
                status_counts = {}
                for project in projects:
                    status = project.status
                    status_counts[status] = status_counts.get(status, 0) + 1
                overview['projects_summary']['status_breakdown'] = status_counts
                
                # Financial summary
                if financial_data:
                    latest_financial = financial_data[0]
                    overview['financial_summary'] = {
                        'latest_year': latest_financial.financial_year,
                        'total_budget': latest_financial.total_budget,
                        'water_related_capex': latest_financial.water_related_capex,
                        'infrastructure_budget': latest_financial.infrastructure_budget,
                        'surplus_deficit': latest_financial.surplus_deficit,
                        'years_available': len(financial_data)
                    }
                    
                    # Investment efficiency analysis
                    if latest_financial.water_related_capex > 0 and overview['projects_summary']['total_allocated'] > 0:
                        efficiency_ratio = overview['projects_summary']['total_allocated'] / latest_financial.water_related_capex
                        overview['investment_efficiency'] = {
                            'project_to_capex_ratio': round(efficiency_ratio, 2),
                            'assessment': 'high' if efficiency_ratio > 2 else 'balanced' if efficiency_ratio > 0.5 else 'low'
                        }
                
                # Generate recommendations
                await self._generate_municipal_recommendations(overview, projects, financial_data)
                
                return overview
                
        except Exception as e:
            logger.error(f"Error getting municipal investment overview for {municipality_id}: {str(e)}")
            raise
    
    async def _generate_municipal_recommendations(
        self, 
        overview: Dict[str, Any], 
        projects: List[Project],
        financial_data: List[FinancialData]
    ) -> None:
        """Generate recommendations for municipal investment strategy"""
        
        recommendations = []
        
        # Project portfolio recommendations
        total_projects = len(projects)
        if total_projects == 0:
            recommendations.append({
                'type': 'project_portfolio',
                'priority': 'high',
                'message': 'No water infrastructure projects found - consider developing a water infrastructure plan'
            })
        elif total_projects < 3:
            recommendations.append({
                'type': 'project_portfolio',
                'priority': 'medium',
                'message': 'Limited water infrastructure projects - consider expanding the project portfolio'
            })
        
        # Budget utilization recommendations
        if projects:
            total_allocated = sum(p.budget_allocated or 0 for p in projects)
            total_spent = sum(p.budget_spent or 0 for p in projects)
            
            if total_allocated > 0:
                utilization_rate = total_spent / total_allocated * 100
                
                if utilization_rate < 50:
                    recommendations.append({
                        'type': 'budget_utilization',
                        'priority': 'high',
                        'message': f'Low budget utilization ({utilization_rate:.1f}%) - review project implementation capacity'
                    })
                elif utilization_rate > 95:
                    recommendations.append({
                        'type': 'budget_utilization',
                        'priority': 'medium',
                        'message': f'Very high budget utilization ({utilization_rate:.1f}%) - monitor for potential overruns'
                    })
        
        # Financial health recommendations
        if financial_data:
            latest_financial = financial_data[0]
            
            if latest_financial.surplus_deficit < 0:
                deficit_percentage = abs(latest_financial.surplus_deficit / latest_financial.total_budget * 100) if latest_financial.total_budget > 0 else 0
                
                if deficit_percentage > 10:
                    recommendations.append({
                        'type': 'financial_health',
                        'priority': 'high',
                        'message': f'Significant budget deficit ({deficit_percentage:.1f}%) - review project funding sustainability'
                    })
            
            # Water investment recommendations
            if latest_financial.infrastructure_budget > 0:
                water_investment_ratio = latest_financial.water_related_capex / latest_financial.infrastructure_budget * 100
                
                if water_investment_ratio < 15:
                    recommendations.append({
                        'type': 'water_investment',
                        'priority': 'medium',
                        'message': f'Water investment is {water_investment_ratio:.1f}% of infrastructure budget - consider increasing water infrastructure priority'
                    })
        
        overview['recommendations'] = recommendations
