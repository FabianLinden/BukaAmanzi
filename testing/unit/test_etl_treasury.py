import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.etl.treasury import MunicipalTreasuryETL
from app.db.models import Municipality, FinancialData, DataChangeLog
from app.services.change_detection import calculate_content_hash

@pytest.fixture
def mock_notification_manager():
    """Fixture for a mock DataChangeNotifier."""
    return AsyncMock()

@pytest.fixture
def mock_db_session():
    """Fixture for a mock database session."""
    mock = MagicMock()
    mock.execute = AsyncMock()
    mock.scalar_one_or_none = AsyncMock()
    mock.add = MagicMock()
    mock.commit = AsyncMock()
    return mock

@pytest.fixture
async def treasury_etl(mock_notification_manager):
    """Fixture to create a MunicipalTreasuryETL instance with mocks."""
    etl = MunicipalTreasuryETL(notification_manager=mock_notification_manager)
    # Mock the async client session within the ETL instance
    etl.session = AsyncMock()
    yield etl
    # No need to explicitly close the mock session

# Further tests will be added below

@pytest.mark.asyncio
async def test_store_financial_data_creates_new_record(treasury_etl, mock_db_session):
    """Test that new financial data is stored correctly."""
    # Arrange
    financial_data = {
        'municipality_code': 'CPT', 'financial_year': 2023,
        'total_budget': 100, 'total_actual': 90,
        'total_capex_budget': 50, 'total_capex_actual': 45,
        'water_related_capex': 10, 'infrastructure_budget': 30,
        'surplus_deficit': -10, 'budget_variance': -10
    }

    mock_municipality = Municipality(id='muni-1', code='CPT', name='City of Cape Town')

    # Mock DB to find municipality but no existing financial data
    mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [mock_municipality, None]

    # Act
    with patch('app.etl.treasury.async_session_factory', return_value=mock_db_session):
        record_id = await treasury_etl.store_financial_data(financial_data)

    # Assert
    assert record_id is not None
    # Called for FinancialData and DataChangeLog
    assert mock_db_session.add.call_count == 2
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_store_financial_data_updates_existing_record(treasury_etl, mock_db_session):
    """Test that existing financial data is updated correctly."""
    # Arrange
    updated_financial_data = {
        'municipality_code': 'CPT', 'financial_year': 2023,
        'total_budget': 120, 'total_actual': 110,
        'total_capex_budget': 60, 'total_capex_actual': 55,
        'water_related_capex': 15, 'infrastructure_budget': 40,
        'surplus_deficit': -10, 'budget_variance': -8.33
    }

    mock_municipality = Municipality(id='muni-1', code='CPT', name='City of Cape Town')
    existing_record = FinancialData(id='fd-1', municipality_id='muni-1', financial_year=2023, content_hash='old_hash')

    # Mock DB to find municipality and existing financial data
    mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [mock_municipality, existing_record]

    # Act
    with patch('app.etl.treasury.async_session_factory', return_value=mock_db_session):
        record_id = await treasury_etl.store_financial_data(updated_financial_data)

    # Assert
    assert record_id == 'fd-1'
    # Verify all fields were updated
    for key, value in updated_financial_data.items():
        assert getattr(existing_record, key) == value
    assert existing_record.content_hash != 'old_hash'
    # Called for DataChangeLog
    assert mock_db_session.add.call_count == 1
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_store_financial_data_no_update_if_no_change(treasury_etl, mock_db_session):
    """Test that no update occurs if financial data is unchanged."""
    # Arrange
    financial_data = {
        'municipality_code': 'CPT', 'financial_year': 2023,
        'total_budget': 100, 'total_actual': 90,
        'total_capex_budget': 50, 'total_capex_actual': 45,
        'water_related_capex': 10, 'infrastructure_budget': 30,
        'surplus_deficit': -10, 'budget_variance': -10
    }
    content_hash = calculate_content_hash(financial_data)

    mock_municipality = Municipality(id='muni-1', code='CPT', name='City of Cape Town')
    existing_record = FinancialData(id='fd-1', municipality_id='muni-1', financial_year=2023, content_hash=content_hash)

    # Mock DB to find municipality and existing financial data
    mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [mock_municipality, existing_record]

    # Act
    with patch('app.etl.treasury.async_session_factory', return_value=mock_db_session):
        await treasury_etl.store_financial_data(financial_data)

    # Assert
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_sync_all_financial_data_success(treasury_etl, mock_db_session):
    """Test the successful sync of financial data for all municipalities."""
    # Arrange
    mock_municipalities = [
        Municipality(id='muni-1', code='CPT', name='City of Cape Town'),
        Municipality(id='muni-2', code='JHB', name='City of Johannesburg')
    ]
    
    # Mock the async session's execute and scalars().all()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_municipalities
    mock_db_session.execute.return_value = mock_result

    # Mock the fetch_financial_data to return valid data structure
    mock_financial_data = {
        'total_budget': 100, 'total_actual': 90,
        'total_capex_budget': 50, 'total_capex_actual': 45,
        'water_related_capex': 10, 'infrastructure_budget': 30,
        'surplus_deficit': -10, 'budget_variance': -10
    }

    # Act
    with patch('app.etl.treasury.async_session_factory', return_value=mock_db_session), \
         patch.object(treasury_etl, 'fetch_financial_data', 
                     new_callable=AsyncMock, 
                     return_value=mock_financial_data) as mock_fetch, \
         patch.object(treasury_etl, 'store_financial_data', 
                     new_callable=AsyncMock, 
                     return_value='record-id') as mock_store:

        synced_records = await treasury_etl.sync_all_financial_data(2023)

    # Assert
    assert len(synced_records) == 2
    assert mock_fetch.call_count == 2
    assert mock_store.call_count == 2

@pytest.mark.asyncio
async def test_poll_with_change_detection_success(treasury_etl, mock_notification_manager, mock_db_session):
    """Test the main polling and change detection orchestration."""
    # Arrange
    mock_municipalities_data = [{'code': 'CPT', 'name': 'City of Cape Town'}]
    mock_synced_records = ['record-1', 'record-2']

    # Act
    with patch.object(treasury_etl, 'fetch_municipalities', new_callable=AsyncMock, return_value=mock_municipalities_data), \
         patch.object(treasury_etl, 'sync_all_financial_data', new_callable=AsyncMock, return_value=mock_synced_records), \
         patch('app.etl.treasury.async_session_factory', return_value=mock_db_session):

        await treasury_etl.poll_with_change_detection()

    # Assert
    treasury_etl.fetch_municipalities.assert_called_once()
    treasury_etl.sync_all_financial_data.assert_called_once()
    mock_notification_manager.notify_change.assert_called_once()
    # Check that the notification contains the correct number of updated records
    notification_call_args = mock_notification_manager.notify_change.call_args[0][0]
    assert notification_call_args['changes']['records_updated'] == 2
