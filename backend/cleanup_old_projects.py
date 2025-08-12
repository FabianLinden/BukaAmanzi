#!/usr/bin/env python3
"""
Direct cleanup script to remove old format DWS projects ending with -003
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, delete
from app.db.session import async_session_factory
from app.db.models import Project
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def cleanup_old_format_projects():
    """Remove all old format projects ending with -003"""
    try:
        async with async_session_factory() as session:
            logger.info("Starting cleanup of old format projects...")
            
            # Find all projects ending with -003
            stmt = select(Project).where(
                Project.source == 'dws_pmd',
                Project.external_id.like('%-003')
            )
            result = await session.execute(stmt)
            old_projects = result.scalars().all()
            
            logger.info(f"Found {len(old_projects)} old format projects to delete")
            
            if old_projects:
                # Get their IDs
                project_ids = [p.id for p in old_projects]
                
                # Log what we're deleting
                for project in old_projects:
                    logger.info(f"Deleting: {project.name} ({project.external_id})")
                
                # Delete them
                delete_stmt = delete(Project).where(Project.id.in_(project_ids))
                result = await session.execute(delete_stmt)
                deleted_count = result.rowcount
                
                # Commit the changes
                await session.commit()
                
                logger.info(f"Successfully deleted {deleted_count} old format projects")
                print(f"✅ Successfully deleted {deleted_count} old format projects")
            else:
                logger.info("No old format projects found")
                print("✅ No old format projects found")
                
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        print(f"❌ Error during cleanup: {str(e)}")
        raise

async def main():
    """Main cleanup function"""
    print("🧹 Starting cleanup of old format DWS projects...")
    await cleanup_old_format_projects()
    print("🎉 Cleanup completed!")

if __name__ == "__main__":
    asyncio.run(main())
