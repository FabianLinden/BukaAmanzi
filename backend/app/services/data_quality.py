from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Municipality
from app.db.session import async_session_factory
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataQualityService:
    """Service for assessing and improving data quality across projects"""
    
    def __init__(self):
        self.quality_cache: Dict[str, Any] = {}
        self.municipality_patterns = self._build_municipality_patterns()
    
    def _build_municipality_patterns(self) -> Dict[str, Set[str]]:
        """Build patterns to detect generic/template project names"""
        return {
            'generic_patterns': {
                r'^Water Infrastructure Project \d+ - ',
                r'^Project \d+$',
                r'^Test Project',
                r'^Sample Project',
                r'^Placeholder',
                r'^Default Project',
                r'^Unnamed Project',
                r'^District Municipality Project',
                r'^\s*$',  # Empty or whitespace only
            },
            'template_indicators': {
                'Water Infrastructure Project',
                'Template Project',
                'Example Project',
                'Demo Project',
                'All!ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            }
        }
    
    async def assess_project_quality(self, project: Project) -> Dict[str, Any]:
        """Comprehensive quality assessment for a single project"""
        
        quality_score = 0
        max_score = 100
        issues = []
        strengths = []
        recommendations = []
        
        # 1. Name Quality (20 points)
        name_score, name_issues, name_strengths = self._assess_name_quality(project.name)
        quality_score += name_score
        issues.extend(name_issues)
        strengths.extend(name_strengths)
        
        # 2. Location Data Quality (25 points)
        location_score, location_issues, location_strengths, location_recs = self._assess_location_quality(
            project.location, project.address
        )
        quality_score += location_score
        issues.extend(location_issues)
        strengths.extend(location_strengths)
        recommendations.extend(location_recs)
        
        # 3. Financial Data Quality (20 points)
        financial_score, financial_issues, financial_strengths = self._assess_financial_quality(
            project.budget_allocated, project.budget_spent
        )
        quality_score += financial_score
        issues.extend(financial_issues)
        strengths.extend(financial_strengths)
        
        # 4. Temporal Data Quality (15 points)
        temporal_score, temporal_issues, temporal_strengths = self._assess_temporal_quality(
            project.start_date, project.end_date
        )
        quality_score += temporal_score
        issues.extend(temporal_issues)
        strengths.extend(temporal_strengths)
        
        # 5. Descriptive Data Quality (10 points)
        desc_score, desc_issues, desc_strengths = self._assess_descriptive_quality(
            project.description, project.contractor
        )
        quality_score += desc_score
        issues.extend(desc_issues)
        strengths.extend(desc_strengths)
        
        # 6. Status and Progress Quality (10 points)
        status_score, status_issues, status_strengths = self._assess_status_quality(
            project.status, project.progress_percentage, project.start_date, project.end_date
        )
        quality_score += status_score
        issues.extend(status_issues)
        strengths.extend(status_strengths)
        
        # Calculate quality tier
        quality_tier = self._calculate_quality_tier(quality_score)
        
        # Generate improvement recommendations
        if quality_score < 80:
            recommendations.extend(self._generate_improvement_recommendations(project, issues))
        
        return {
            'project_id': project.id,
            'project_name': project.name,
            'quality_score': round(quality_score, 1),
            'max_score': max_score,
            'quality_percentage': round((quality_score / max_score) * 100, 1),
            'quality_tier': quality_tier,
            'is_complete': quality_score >= 80,
            'is_template_data': self._is_template_data(project),
            'component_scores': {
                'name': name_score,
                'location': location_score,
                'financial': financial_score,
                'temporal': temporal_score,
                'descriptive': desc_score,
                'status': status_score
            },
            'issues': issues,
            'strengths': strengths,
            'recommendations': recommendations,
            'assessed_at': datetime.utcnow().isoformat()
        }
    
    def _assess_name_quality(self, name: Optional[str]) -> Tuple[float, List[str], List[str]]:
        """Assess quality of project name"""
        if not name or name.strip() == '':
            return 0, ['Project name is missing'], []
        
        name = name.strip()
        issues = []
        strengths = []
        score = 20  # Start with full score
        
        # Check for generic patterns
        for pattern in self.municipality_patterns['generic_patterns']:
            if re.match(pattern, name, re.IGNORECASE):
                issues.append(f'Generic project name detected: "{name}"')
                score -= 15
                break
        
        # Check for template indicators
        for indicator in self.municipality_patterns['template_indicators']:
            if indicator.lower() in name.lower():
                issues.append(f'Template name indicator found: "{indicator}"')
                score -= 10
                break
        
        # Positive indicators
        if len(name) > 10:
            strengths.append('Project name is descriptive')
        
        if any(keyword in name.lower() for keyword in ['dam', 'treatment', 'pipeline', 'supply', 'scheme', 'plant']):
            strengths.append('Project name contains water infrastructure keywords')
            score += 5
        
        if re.search(r'\b(upgrade|construction|rehabilitation|augmentation)\b', name.lower()):
            strengths.append('Project name indicates specific activity type')
        
        return max(0, score), issues, strengths
    
    def _assess_location_quality(self, location: Optional[str], address: Optional[str]) -> Tuple[float, List[str], List[str], List[str]]:
        """Assess quality of location data"""
        issues = []
        strengths = []
        recommendations = []
        score = 25  # Start with full score
        
        has_coordinates = location and location.startswith('POINT(')
        has_address = address and address.strip() and address.strip().lower() not in ['', 'null', 'none']
        
        if has_coordinates:
            # Validate coordinate format
            coord_match = re.match(r'POINT\(([^)]+)\)', location)
            if coord_match:
                try:
                    coords = coord_match.group(1).split()
                    if len(coords) == 2:
                        lng, lat = float(coords[0]), float(coords[1])
                        # Check if coordinates are within South Africa bounds (roughly)
                        if -35 <= lat <= -22 and 16 <= lng <= 33:
                            strengths.append('Valid geographic coordinates within South Africa')
                        else:
                            issues.append('Coordinates appear to be outside South Africa')
                            score -= 5
                    else:
                        issues.append('Invalid coordinate format')
                        score -= 10
                except (ValueError, IndexError):
                    issues.append('Coordinates contain invalid values')
                    score -= 10
            else:
                issues.append('Invalid POINT format in location field')
                score -= 10
        else:
            issues.append('No geographic coordinates available')
            score -= 15
            recommendations.append('Add precise GPS coordinates for project location')
        
        if has_address:
            if len(address.strip()) > 10:
                strengths.append('Detailed address information available')
            else:
                issues.append('Address is too brief or generic')
                score -= 5
        else:
            issues.append('No address information available')
            score -= 10
            recommendations.append('Add descriptive address or location description')
        
        if not has_coordinates and not has_address:
            issues.append('No location data available - project cannot be mapped accurately')
            recommendations.append('Location data is critical for mapping - add either coordinates or detailed address')
        
        return max(0, score), issues, strengths, recommendations
    
    def _assess_financial_quality(self, budget_allocated: Optional[float], budget_spent: Optional[float]) -> Tuple[float, List[str], List[str]]:
        """Assess quality of financial data"""
        issues = []
        strengths = []
        score = 20  # Start with full score
        
        has_budget = budget_allocated is not None and budget_allocated > 0
        has_spent = budget_spent is not None and budget_spent >= 0
        
        if not has_budget:
            issues.append('No budget allocation information')
            score -= 12
        else:
            strengths.append('Budget allocation data available')
            
            # Check for reasonable budget values
            if budget_allocated > 1000000000:  # > 1B
                strengths.append('Major infrastructure project (>R1B budget)')
            elif budget_allocated < 100000:  # < 100K
                issues.append('Budget seems unusually low for infrastructure project')
                score -= 3
        
        if not has_spent:
            issues.append('No spending/expenditure information')
            score -= 8
        else:
            strengths.append('Spending data available')
            
            # Validate spending vs budget
            if has_budget and budget_spent > budget_allocated:
                issues.append('Spending exceeds allocated budget')
                score -= 5
        
        return max(0, score), issues, strengths
    
    def _assess_temporal_quality(self, start_date: Optional[datetime], end_date: Optional[datetime]) -> Tuple[float, List[str], List[str]]:
        """Assess quality of temporal data"""
        issues = []
        strengths = []
        score = 15  # Start with full score
        
        has_start = start_date is not None
        has_end = end_date is not None
        
        if not has_start:
            issues.append('No project start date')
            score -= 8
        
        if not has_end:
            issues.append('No project end date')
            score -= 7
        
        if has_start and has_end:
            if start_date < end_date:
                strengths.append('Valid project timeline (start before end)')
                
                # Check project duration reasonableness
                duration = (end_date - start_date).days
                if duration < 30:
                    issues.append('Project duration seems very short (< 1 month)')
                    score -= 2
                elif duration > 3650:  # > 10 years
                    issues.append('Project duration seems very long (> 10 years)')
                    score -= 2
                else:
                    strengths.append('Reasonable project duration')
            else:
                issues.append('End date is before start date')
                score -= 5
        
        return max(0, score), issues, strengths
    
    def _assess_descriptive_quality(self, description: Optional[str], contractor: Optional[str]) -> Tuple[float, List[str], List[str]]:
        """Assess quality of descriptive data"""
        issues = []
        strengths = []
        score = 10  # Start with full score
        
        has_desc = description and description.strip() and description.strip().lower() not in ['', 'null', 'none', 'no description available']
        has_contractor = contractor and contractor.strip() and contractor.strip().lower() not in ['', 'null', 'none', 'not specified']
        
        if not has_desc:
            issues.append('No project description available')
            score -= 6
        else:
            if len(description.strip()) > 50:
                strengths.append('Detailed project description available')
            else:
                issues.append('Project description is too brief')
                score -= 2
        
        if not has_contractor:
            issues.append('No contractor information available')
            score -= 4
        else:
            strengths.append('Contractor information available')
        
        return max(0, score), issues, strengths
    
    def _assess_status_quality(self, status: str, progress: int, start_date: Optional[datetime], end_date: Optional[datetime]) -> Tuple[float, List[str], List[str]]:
        """Assess quality of status and progress data"""
        issues = []
        strengths = []
        score = 10  # Start with full score
        
        valid_statuses = ['planned', 'in_progress', 'completed', 'delayed', 'cancelled']
        
        if status not in valid_statuses:
            issues.append(f'Invalid status: {status}')
            score -= 3
        else:
            strengths.append('Valid project status')
        
        if progress < 0 or progress > 100:
            issues.append(f'Invalid progress percentage: {progress}')
            score -= 3
        
        # Check status-progress consistency
        if status == 'completed' and progress < 100:
            issues.append('Project marked as completed but progress < 100%')
            score -= 2
        elif status == 'planned' and progress > 10:
            issues.append('Project marked as planned but has significant progress')
            score -= 2
        elif status == 'in_progress' and progress == 0:
            issues.append('Project marked as in progress but no progress recorded')
            score -= 2
        else:
            strengths.append('Status and progress appear consistent')
        
        # Check temporal consistency
        current_date = datetime.now()
        if end_date and end_date < current_date and status != 'completed' and status != 'cancelled':
            issues.append('Project end date has passed but status is not completed/cancelled')
            score -= 2
        
        return max(0, score), issues, strengths
    
    def _calculate_quality_tier(self, score: float) -> str:
        """Calculate quality tier based on score"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'very_poor'
    
    def _is_template_data(self, project: Project) -> bool:
        """Determine if project appears to be template/demo data"""
        if not project.name:
            return True
        
        name = project.name.lower().strip()
        
        # Check for obvious template patterns
        template_patterns = [
            r'^water infrastructure project \d+',
            r'^project \d+$',
            r'^test project',
            r'^sample project',
            r'^demo project',
            r'^placeholder',
            r'^template',
            r'all!abcdefghijklmnopqrstuvwxyz'
        ]
        
        for pattern in template_patterns:
            if re.match(pattern, name):
                return True
        
        # Check for template indicators in description
        if project.description:
            desc = project.description.lower()
            if any(indicator in desc for indicator in ['template', 'placeholder', 'demo', 'test project']):
                return True
        
        return False
    
    def _generate_improvement_recommendations(self, project: Project, issues: List[str]) -> List[str]:
        """Generate specific improvement recommendations based on issues"""
        recommendations = []
        
        issue_text = ' '.join(issues).lower()
        
        if 'no geographic coordinates' in issue_text:
            recommendations.append('Use GPS device or mapping service to obtain precise coordinates')
        
        if 'generic project name' in issue_text or 'template name' in issue_text:
            recommendations.append('Replace generic name with descriptive project title including location and type')
        
        if 'no budget' in issue_text:
            recommendations.append('Add budget information from project documentation or municipal records')
        
        if 'no address' in issue_text:
            recommendations.append('Add detailed address or location description for better mapping')
        
        if 'no description' in issue_text:
            recommendations.append('Add project description explaining scope, objectives, and expected outcomes')
        
        if 'no contractor' in issue_text:
            recommendations.append('Add contractor or implementing agency information')
        
        if 'no project start date' in issue_text or 'no project end date' in issue_text:
            recommendations.append('Add complete project timeline information')
        
        return recommendations
    
    async def assess_all_projects(self, session: AsyncSession) -> Dict[str, Any]:
        """Assess quality of all projects in database"""
        
        logger.info("Starting comprehensive project quality assessment")
        
        # Get all projects
        stmt = select(Project)
        result = await session.execute(stmt)
        projects = result.scalars().all()
        
        if not projects:
            logger.warning("No projects found for assessment")
            return {'message': 'No projects found', 'assessments': []}
        
        assessments = []
        quality_stats = {
            'total_projects': len(projects),
            'by_tier': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'very_poor': 0},
            'template_data_count': 0,
            'complete_projects': 0,
            'avg_quality_score': 0,
            'common_issues': {},
            'by_source': {}
        }
        
        total_score = 0
        
        for project in projects:
            assessment = await self.assess_project_quality(project)
            assessments.append(assessment)
            
            # Update statistics
            quality_stats['by_tier'][assessment['quality_tier']] += 1
            
            if assessment['is_template_data']:
                quality_stats['template_data_count'] += 1
            
            if assessment['is_complete']:
                quality_stats['complete_projects'] += 1
            
            total_score += assessment['quality_score']
            
            # Track common issues
            for issue in assessment['issues']:
                issue_key = issue.split(':')[0] if ':' in issue else issue
                quality_stats['common_issues'][issue_key] = quality_stats['common_issues'].get(issue_key, 0) + 1
            
            # Track by source
            source = project.source
            if source not in quality_stats['by_source']:
                quality_stats['by_source'][source] = {'count': 0, 'avg_score': 0, 'total_score': 0}
            
            quality_stats['by_source'][source]['count'] += 1
            quality_stats['by_source'][source]['total_score'] += assessment['quality_score']
            quality_stats['by_source'][source]['avg_score'] = quality_stats['by_source'][source]['total_score'] / quality_stats['by_source'][source]['count']
        
        quality_stats['avg_quality_score'] = total_score / len(projects) if projects else 0
        
        logger.info(f"Quality assessment completed for {len(projects)} projects. Average score: {quality_stats['avg_quality_score']:.1f}")
        
        return {
            'assessments': assessments,
            'statistics': quality_stats,
            'assessed_at': datetime.utcnow().isoformat()
        }
    
    async def get_filterable_projects(self, session: AsyncSession, min_quality_score: float = 60.0, exclude_template: bool = True) -> List[Dict[str, Any]]:
        """Get projects filtered by quality criteria"""
        
        quality_report = await self.assess_all_projects(session)
        
        filtered_projects = []
        for assessment in quality_report['assessments']:
            if assessment['quality_score'] >= min_quality_score:
                if not exclude_template or not assessment['is_template_data']:
                    filtered_projects.append(assessment)
        
        logger.info(f"Filtered {len(filtered_projects)} projects from {quality_report['statistics']['total_projects']} total (min_score: {min_quality_score}, exclude_template: {exclude_template})")
        
        return filtered_projects
