import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path
import sys
from datetime import datetime
from sqlalchemy import select

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.session import async_session_factory, engine
from app.db.models import Base, Municipality, FinancialData, Project, DataChangeLog
from app.etl.treasury import MunicipalTreasuryETL
from app.etl.dws import EnhancedDWSMonitor
from app.realtime.notifier import DataChangeNotifier

@pytest.fixture(scope="module")
async def test_db():
    """Fixture to create and tear down a test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_treasury_etl_full_sync(test_db):
    """Integration test for the full Treasury ETL sync process."""
    # Arrange
    mock_notifier = AsyncMock(spec=DataChangeNotifier)
    treasury_etl = MunicipalTreasuryETL(notification_manager=mock_notifier)

    # Mock the external API calls
    mock_municipalities_response = {
        'cells': [{
            'municipality': {
                'code': 'BUF', 'name': 'Buffalo City',
                'province_name': 'Eastern Cape', 'category': 'A'
            }
        }]
    }
    mock_financial_response = {'_mock_data': True, 'total_budget': 1000}

    # Act
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock the two responses needed: one for municipalities, one for financials
        mock_get.side_effect = [
            AsyncMock(json=lambda: mock_municipalities_response, raise_for_status=lambda: None),
            AsyncMock(json=lambda: mock_financial_response, raise_for_status=lambda: None)
        ]

        await treasury_etl.poll_with_change_detection()

    # Assert
    async with async_session_factory() as session:
        # Check if municipality was created
        muni_result = await session.execute(select(Municipality).where(Municipality.code == 'BUF'))
        municipality = muni_result.scalar_one_or_none()
        assert municipality is not None
        assert municipality.name == 'Buffalo City'

        # Check if financial data was created
        financial_result = await session.execute(select(FinancialData).where(FinancialData.municipality_id == municipality.id))
        financial_data = financial_result.scalar_one_or_none()
        assert financial_data is not None
        assert financial_data.total_budget == 1000

    # Check if notifier was called
    mock_notifier.notify_change.assert_called_once()

@pytest.mark.asyncio
async def test_dws_etl_full_sync(test_db):
    """Integration test for the full DWS ETL sync process."""
    # Arrange
    mock_notifier = AsyncMock(spec=DataChangeNotifier)
    dws_monitor = EnhancedDWSMonitor(notification_manager=mock_notifier)

    # Mock the fetched HTML data
    mock_html_content = """
    <html><body>
        <div class='province-heading'>Gauteng</div>
        <table>
            <tr><td>Project Name</td><td>Test DWS Project</td></tr>
            <tr><td>Description</td><td>A project for testing.</td></tr>
            <tr><td>Municipality</td><td>Ekurhuleni</td></tr>
            <tr><td>Province</td><td>Gauteng</td></tr>
        </table>
    </body></html>
    """

    # Act
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = AsyncMock(text=mock_html_content, status_code=200)
        await dws_monitor.poll_with_change_detection()

    # Assert
    async with async_session_factory() as session:
        # Check if project was created
        proj_result = await session.execute(select(Project).where(Project.name == 'Test DWS Project'))
        project = proj_result.scalar_one_or_none()
        assert project is not None
        assert project.description == 'A project for testing.'

        # Check if municipality was created
        muni_result = await session.execute(select(Municipality).where(Municipality.name == 'Ekurhuleni'))
        municipality = muni_result.scalar_one_or_none()
        assert municipality is not None

    # Check if notifier was called
    mock_notifier.notify_change.assert_called_once()

@pytest.mark.asyncio
async def test_dws_etl_change_detection(test_db):
    """Integration test for the DWS ETL change detection and update logic."""
    # Arrange
    mock_notifier = AsyncMock(spec=DataChangeNotifier)
    dws_monitor = EnhancedDWSMonitor(notification_manager=mock_notifier)

    initial_html_content = """
    <html><body>
        <table><tr><td>Project Name</td><td>Change Detection Project</td></tr>
               <tr><td>Description</td><td>Initial Description</td></tr></table>
    </body></html>
    """
    updated_html_content = """
    <html><body>
        <table><tr><td>Project Name</td><td>Change Detection Project</td></tr>
               <tr><td>Description</td><td>Updated Description</td></tr></table>
    </body></html>
    """

    # Act: First run to create the initial record
    with patch('httpx.AsyncClient.get') as mock_get_initial:
        mock_get_initial.return_value = AsyncMock(text=initial_html_content, status_code=200)
        await dws_monitor.poll_with_change_detection()

    # Act: Second run to detect and apply changes
    with patch('httpx.AsyncClient.get') as mock_get_updated:
        mock_get_updated.return_value = AsyncMock(text=updated_html_content, status_code=200)
        await dws_monitor.poll_with_change_detection()

    # Assert
    async with async_session_factory() as session:
        # Check that the project was updated, not duplicated
        proj_result = await session.execute(select(Project).where(Project.name == 'Change Detection Project'))
        projects = proj_result.scalars().all()
        assert len(projects) == 1
        assert projects[0].description == 'Updated Description'

        # Check that a change log was created for the update
        log_result = await session.execute(select(DataChangeLog).where(DataChangeLog.entity_id == projects[0].id))
        change_logs = log_result.scalars().all()
        # One for creation, one for update
        assert len(change_logs) == 2
        assert change_logs[1].change_type == 'updated'

    # Notifier should be called twice
    assert mock_notifier.notify_change.call_count == 2
