import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from pathlib import Path
import sys
from datetime import datetime, timezone

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.etl.dws import EnhancedDWSMonitor
from app.models.models import Project, Municipality, DataChangeLog
from app.services.change_detection import calculate_content_hash

@pytest.fixture
def mock_notification_manager():
    """Fixture for a mock DataChangeNotifier."""
    mock = AsyncMock()
    mock.notify_change = AsyncMock()
    mock.notify_system_error = AsyncMock()
    return mock

@pytest.fixture
def mock_db_session():
    """Fixture for a mock database session."""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.scalar_one_or_none = AsyncMock()
    mock.add = MagicMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    return mock

@pytest.fixture
def dws_monitor(mock_notification_manager):
    """Fixture to create an EnhancedDWSMonitor instance with a mock notifier."""
    return EnhancedDWSMonitor(notification_manager=mock_notification_manager)

@pytest.mark.asyncio
async def test_poll_with_changes(dws_monitor, mock_notification_manager, mock_db_session):
    """Test the main polling logic when data has changed."""
    # Arrange
    sample_data = {
        'projects': [{
            'external_id': 'DWS-WC-001',
            'name': 'Test Project',
            'description': 'A test project.',
            'municipality': 'Test Municipality',
            'province': 'Test Province',
            'status': 'in_progress',
            'progress_percentage': 50,
            'budget_allocated': 10000.0,
            'budget_spent': 5000.0,
            'contractor': 'Test Contractor',
            'start_date': '2023-01-01',
            'end_date': '2024-01-01',
            'project_type': 'water_supply',
            'location': 'POINT(0 0)',
            'address': '123 Test Street',
            'last_updated': '2023-01-01T00:00:00'
        }],
        'municipalities': [{
            'name': 'Test Municipality',
            'code': 'TM',
            'province': 'Test Province'
        }]
    }

    # Mock the database to return no existing project or municipality
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    # Patch the dependencies
    with patch('app.etl.dws.async_session_factory', return_value=mock_db_session), \
         patch.object(dws_monitor, 'fetch_dws_data', new_callable=AsyncMock, return_value=sample_data) as mock_fetch:

        # Act
        await dws_monitor.poll_with_change_detection()

        # Assert
        # Verify that data was fetched
        mock_fetch.assert_awaited_once()

        # Verify a new project and municipality were processed and added to the DB
        assert mock_db_session.add.call_count >= 2  # At least one for muni, one for project
        mock_db_session.commit.assert_awaited_once()

        # Verify that a notification was sent
        mock_notification_manager.notify_change.assert_awaited_once()

@pytest.mark.asyncio
async def test_process_project_no_update_if_no_change(dws_monitor, mock_db_session):
    """Test that an existing project is not updated if its data has not changed."""
    # Arrange
    project_data = {
        'external_id': 'DWS-NOCHANGE-001',
        'name': 'No Change Project',
        'description': 'Description',
        'municipality': 'Some Municipality',
        'status': 'in_progress',
        'progress_percentage': 50,
        'budget_allocated': 10000.0,
        'budget_spent': 5000.0,
        'contractor': 'Contractor',
        'start_date': '2023-01-01',
        'end_date': '2024-01-01',
        'project_type': 'water_supply',
        'location': 'POINT(0 0)',
        'address': '123 Test Street',
        'last_updated': '2024-01-01T00:00:00'
    }

    # Create a mock project with the same content hash
    content_hash = calculate_content_hash({k: v for k, v in project_data.items() if k != 'last_updated'})
    existing_project = MagicMock()
    existing_project.content_hash = content_hash
    existing_project.id = 'test-id-123'

    # Mock DB to return the existing project
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_project

    # Act
    change = await dws_monitor._process_project(mock_db_session, project_data)

    # Assert
    assert change is None
    # No DataChangeLog should be added
    mock_db_session.add.assert_not_called()

@pytest.mark.asyncio
async def test_poll_with_no_changes(dws_monitor, mock_db_session, mock_notification_manager):
    """Test the main polling logic when data has not changed on a second poll."""
    # Arrange
    sample_data = {'projects': [], 'municipalities': []}

    # Patch the dependencies
    with patch('app.etl.dws.async_session_factory', return_value=mock_db_session), \
         patch.object(dws_monitor, 'fetch_dws_data', new_callable=AsyncMock, return_value=sample_data) as mock_fetch, \
         patch.object(dws_monitor, '_process_data_changes', new_callable=AsyncMock) as mock_process_changes:

        # Mock the content hash to be the same on both polls
        original_hash = dws_monitor.calculate_content_hash(sample_data)
        dws_monitor.last_content_hashes['dws_projects'] = original_hash

        # Act: Poll twice with the same data
        await dws_monitor.poll_with_change_detection()
        await dws_monitor.poll_with_change_detection()

        # Assert
        # fetch_dws_data should be called twice
        assert mock_fetch.await_count == 2
        
        # _process_data_changes should only be called on the first poll
        mock_process_changes.assert_awaited_once()
        
        # No notifications should be sent on the second poll
        assert mock_notification_manager.notify_change.await_count == 0
