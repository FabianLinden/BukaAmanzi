#!/usr/bin/env python3
"""
Clean existing municipality data in the database
"""
import asyncio
import re
from sqlalchemy import select, update
from app.db.session import async_session_factory
from app.db.models import Municipality, Project

def clean_municipality_name(raw_name: str) -> str:
    """Clean municipality name by removing unwanted text and characters"""
    if not raw_name:
        return ""
    
    # Remove common unwanted patterns
    unwanted_patterns = [
        r'All!ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        r'Project Dashboards - Local Municipaly',
        r'Project Dashboards',
        r'Local Municipaly',
        r'[!@#$%^&*()]+',
        r'\n+',
        r'\r+',
        r'\t+',
    ]
    
    cleaned_name = raw_name
    for pattern in unwanted_patterns:
        cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
    
    # Clean up whitespace
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    
    # If the name is too short or empty after cleaning, return a fallback
    if len(cleaned_name) < 3:
        # Try to extract the last meaningful part
        parts = raw_name.split()
        meaningful_parts = [part for part in parts if len(part) > 2 and part.isalpha()]
        if meaningful_parts:
            cleaned_name = meaningful_parts[-1]
        else:
            cleaned_name = "Unknown Municipality"
    
    return cleaned_name

async def clean_database_municipality_names():
    """Clean municipality names in the database"""
    async with async_session_factory() as session:
        try:
            # Get all municipalities
            stmt = select(Municipality)
            result = await session.execute(stmt)
            municipalities = result.scalars().all()
            
            print(f"Found {len(municipalities)} municipalities to clean")
            
            cleaned_count = 0
            for municipality in municipalities:
                original_name = municipality.name
                cleaned_name = clean_municipality_name(original_name)
                
                if cleaned_name != original_name:
                    print(f"Cleaning: '{original_name}' -> '{cleaned_name}'")
                    municipality.name = cleaned_name
                    cleaned_count += 1
            
            # Also clean project names that reference municipalities
            stmt = select(Project)
            result = await session.execute(stmt)
            projects = result.scalars().all()
            
            print(f"Found {len(projects)} projects to check")
            
            for project in projects:
                if project.name:
                    original_name = project.name
                    # Clean project names that contain municipality references
                    cleaned_project_name = original_name
                    for pattern in [
                        r'All!ABCDEFGHIJKLMNOPQRSTUVWXYZ\s*\n+\s*Project Dashboards - Local Municipaly\s*\n+',
                        r'All!ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        r'Project Dashboards - Local Municipaly',
                        r'\n+',
                        r'\r+',
                        r'\t+',
                    ]:
                        cleaned_project_name = re.sub(pattern, '', cleaned_project_name, flags=re.IGNORECASE)
                    
                    cleaned_project_name = re.sub(r'\s+', ' ', cleaned_project_name).strip()
                    
                    if cleaned_project_name != original_name:
                        print(f"Cleaning project: '{original_name}' -> '{cleaned_project_name}'")
                        project.name = cleaned_project_name
                        cleaned_count += 1
            
            await session.commit()
            print(f"Successfully cleaned {cleaned_count} records")
            
        except Exception as e:
            await session.rollback()
            print(f"Error cleaning data: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(clean_database_municipality_names())
