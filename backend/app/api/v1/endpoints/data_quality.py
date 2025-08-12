from typing import Any, List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Municipality
from app.db.session import get_db_session
from app.services.data_quality import DataQualityService
from app.services.geocoding import GeocodingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Pydantic models for request/response
class QualityAssessmentOut(BaseModel):
    project_id: str
    project_name: str
    quality_score: float
    quality_percentage: float
    quality_tier: str
    is_complete: bool
    is_template_data: bool
    component_scores: Dict[str, float]
    issues: List[str]
    strengths: List[str]
    recommendations: List[str]
    assessed_at: str

class QualityStatisticsOut(BaseModel):
    total_projects: int
    by_tier: Dict[str, int]
    template_data_count: int
    complete_projects: int
    avg_quality_score: float
    common_issues: Dict[str, int]
    by_source: Dict[str, Dict[str, Any]]

class QualityReportOut(BaseModel):
    assessments: List[QualityAssessmentOut]
    statistics: QualityStatisticsOut
    assessed_at: str

class GeocodingRequest(BaseModel):
    address: str
    municipality: Optional[str] = None

class GeocodingResult(BaseModel):
    success: bool
    coordinates: Optional[Dict[str, float]]
    confidence: str
    provider: Optional[str] = None
    display_name: Optional[str] = None
    error: Optional[str] = None

class ProjectFilterRequest(BaseModel):
    min_quality_score: Optional[float] = 60.0
    exclude_template: Optional[bool] = True
    quality_tiers: Optional[List[str]] = None


@router.get("/assessment", response_model=QualityReportOut)
async def assess_project_quality(
    project_id: Optional[str] = Query(default=None, description="Assess specific project (if not provided, assess all)"),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Get comprehensive quality assessment for projects"""
    
    quality_service = DataQualityService()
    
    if project_id:
        # Assess single project
        stmt = select(Project).where(Project.id == project_id)
        result = await session.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        assessment = await quality_service.assess_project_quality(project)
        
        return QualityReportOut(
            assessments=[QualityAssessmentOut(**assessment)],
            statistics=QualityStatisticsOut(
                total_projects=1,
                by_tier={assessment['quality_tier']: 1},
                template_data_count=1 if assessment['is_template_data'] else 0,
                complete_projects=1 if assessment['is_complete'] else 0,
                avg_quality_score=assessment['quality_score'],
                common_issues={},
                by_source={}
            ),
            assessed_at=assessment['assessed_at']
        )
    
    else:
        # Assess all projects
        quality_report = await quality_service.assess_all_projects(session)
        
        return QualityReportOut(
            assessments=[QualityAssessmentOut(**assessment) for assessment in quality_report['assessments']],
            statistics=QualityStatisticsOut(**quality_report['statistics']),
            assessed_at=quality_report['assessed_at']
        )


@router.get("/filtered-projects")
async def get_filtered_projects(
    min_quality_score: float = Query(default=60.0, ge=0, le=100, description="Minimum quality score"),
    exclude_template: bool = Query(default=True, description="Exclude template/demo data"),
    quality_tiers: Optional[str] = Query(default=None, description="Comma-separated quality tiers (excellent,good,fair,poor,very_poor)"),
    include_assessment: bool = Query(default=False, description="Include quality assessment details"),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Get projects filtered by data quality criteria"""
    
    quality_service = DataQualityService()
    
    # Get quality assessments
    quality_report = await quality_service.assess_all_projects(session)
    
    # Apply filters
    filtered_assessments = []
    
    tier_filter = None
    if quality_tiers:
        tier_filter = set(tier.strip() for tier in quality_tiers.split(','))
    
    for assessment in quality_report['assessments']:
        # Apply quality score filter
        if assessment['quality_score'] < min_quality_score:
            continue
        
        # Apply template data filter
        if exclude_template and assessment['is_template_data']:
            continue
        
        # Apply quality tier filter
        if tier_filter and assessment['quality_tier'] not in tier_filter:
            continue
        
        filtered_assessments.append(assessment)
    
    # Get full project data if requested
    if not include_assessment:
        # Return only project IDs and basic info
        return {
            'filtered_count': len(filtered_assessments),
            'total_count': quality_report['statistics']['total_projects'],
            'projects': [
                {
                    'id': assessment['project_id'],
                    'name': assessment['project_name'],
                    'quality_score': assessment['quality_score'],
                    'quality_tier': assessment['quality_tier'],
                    'is_complete': assessment['is_complete'],
                    'is_template_data': assessment['is_template_data']
                }
                for assessment in filtered_assessments
            ]
        }
    
    return {
        'filtered_count': len(filtered_assessments),
        'total_count': quality_report['statistics']['total_projects'],
        'filters_applied': {
            'min_quality_score': min_quality_score,
            'exclude_template': exclude_template,
            'quality_tiers': tier_filter
        },
        'projects': filtered_assessments
    }


@router.post("/geocode", response_model=GeocodingResult)
async def geocode_address(
    request: GeocodingRequest,
) -> Any:
    """Geocode an address to geographic coordinates"""
    
    geocoding_service = GeocodingService()
    
    try:
        result = await geocoding_service.geocode_address(
            address=request.address,
            municipality=request.municipality
        )
        
        return GeocodingResult(
            success=result['success'],
            coordinates=result.get('coordinates'),
            confidence=result.get('confidence', 'none'),
            provider=result.get('provider'),
            display_name=result.get('display_name'),
            error=result.get('error')
        )
    
    except Exception as e:
        logger.error(f"Geocoding error: {str(e)}")
        return GeocodingResult(
            success=False,
            coordinates=None,
            confidence='none',
            error=f"Geocoding service error: {str(e)}"
        )


@router.post("/geocode-projects")
async def geocode_projects(
    project_ids: Optional[List[str]] = None,
    update_database: bool = Query(default=False, description="Update project locations in database"),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Batch geocode projects and optionally update their locations"""
    
    geocoding_service = GeocodingService()
    
    # Get projects to geocode
    if project_ids:
        # Specific projects
        stmt = select(Project).where(Project.id.in_(project_ids))
    else:
        # All projects without coordinates
        stmt = select(Project).where(
            Project.location.is_(None) |
            (Project.location == '') |
            (~Project.location.like('POINT(%'))
        )
    
    result = await session.execute(stmt)
    projects = result.scalars().all()
    
    if not projects:
        return {
            'message': 'No projects found for geocoding',
            'total_projects': 0,
            'successful': 0,
            'failed': 0,
            'results': {}
        }
    
    # Perform batch geocoding
    geocoding_results = await geocoding_service.batch_geocode_projects(projects)
    
    # Update database if requested
    updated_projects = 0
    if update_database:
        for project in projects:
            project_result = geocoding_results['results'].get(project.id)
            if project_result and project_result['success'] and 'point_string' in project_result:
                project.location = project_result['point_string']
                updated_projects += 1
        
        await session.commit()
        logger.info(f"Updated {updated_projects} project locations in database")
    
    return {
        'total_projects': geocoding_results['total_projects'],
        'successful': geocoding_results['successful'],
        'failed': geocoding_results['failed'],
        'updated_in_database': updated_projects if update_database else 0,
        'results': geocoding_results['results'],
        'processed_at': geocoding_results['processed_at']
    }


@router.get("/statistics")
async def get_quality_statistics(
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Get overall data quality statistics"""
    
    quality_service = DataQualityService()
    quality_report = await quality_service.assess_all_projects(session)
    
    stats = quality_report['statistics']
    
    # Add additional metrics
    stats['quality_score_distribution'] = {
        '90-100': sum(1 for a in quality_report['assessments'] if a['quality_score'] >= 90),
        '80-89': sum(1 for a in quality_report['assessments'] if 80 <= a['quality_score'] < 90),
        '60-79': sum(1 for a in quality_report['assessments'] if 60 <= a['quality_score'] < 80),
        '40-59': sum(1 for a in quality_report['assessments'] if 40 <= a['quality_score'] < 60),
        '0-39': sum(1 for a in quality_report['assessments'] if a['quality_score'] < 40),
    }
    
    # Location data statistics
    has_coordinates = sum(1 for a in quality_report['assessments'] 
                         if 'Valid geographic coordinates' in str(a.get('strengths', [])))
    
    stats['location_data'] = {
        'has_coordinates': has_coordinates,
        'no_coordinates': stats['total_projects'] - has_coordinates,
        'coordinates_percentage': (has_coordinates / stats['total_projects'] * 100) if stats['total_projects'] > 0 else 0
    }
    
    return {
        'statistics': stats,
        'assessed_at': quality_report['assessed_at']
    }


@router.post("/improve-project/{project_id}")
async def improve_project_data(
    project_id: str,
    geocode_address: bool = Query(default=True, description="Attempt to geocode project address"),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Attempt to improve data quality for a specific project"""
    
    # Get project
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Assess current quality
    quality_service = DataQualityService()
    initial_assessment = await quality_service.assess_project_quality(project)
    
    improvements_made = []
    
    # Attempt geocoding if requested and needed
    if geocode_address and (not project.location or not project.location.startswith('POINT(')):
        geocoding_service = GeocodingService()
        geocoding_result = await geocoding_service.geocode_project(project)
        
        if geocoding_result['success'] and 'point_string' in geocoding_result:
            project.location = geocoding_result['point_string']
            improvements_made.append(f"Added coordinates via {geocoding_result.get('provider', 'geocoding')}")
    
    # Commit changes if any were made
    if improvements_made:
        await session.commit()
    
    # Re-assess quality
    final_assessment = await quality_service.assess_project_quality(project)
    
    return {
        'project_id': project_id,
        'improvements_made': improvements_made,
        'quality_improvement': {
            'initial_score': initial_assessment['quality_score'],
            'final_score': final_assessment['quality_score'],
            'improvement': final_assessment['quality_score'] - initial_assessment['quality_score'],
            'initial_tier': initial_assessment['quality_tier'],
            'final_tier': final_assessment['quality_tier']
        },
        'current_assessment': final_assessment
    }
