# Buka-Amanzi 3.0 - Enhanced Data Integration System

## Overview

The Buka-Amanzi 3.0 Enhanced Data Integration System provides comprehensive monitoring and analysis of South African water infrastructure projects by integrating multiple data sources and providing intelligent correlation analysis.

## Architecture

### Data Sources

1. **DWS Project Monitoring Dashboard**
   - URL: `https://ws.dws.gov.za/pmd/level.aspx`
   - Source: Department of Water and Sanitation (DWS)
   - Data: Water infrastructure projects, budgets, progress, contractors
   - Update frequency: Every 30 minutes

2. **Municipal Money Treasury API**
   - URL: `https://municipaldata.treasury.gov.za/api`
   - Source: National Treasury
   - Data: Municipal financial data, budget allocations, expenditures
   - Update frequency: Every hour

### Core Components

#### 1. ETL Modules (`app/etl/`)

**DWS Monitor (`dws.py`)**
- **Enhanced Web Scraping**: Intelligent scraping with fallback to mock data
- **Real-time Change Detection**: Content hashing for detecting updates
- **Multi-method Extraction**: Tables, divs, AJAX endpoints, and JSON parsing
- **Rate Limiting**: Respectful scraping with configurable delays

**Treasury ETL (`treasury.py`)**
- **Municipal Data Integration**: Comprehensive financial data extraction
- **Budget Analysis**: Capital expenditure, water-related spending analysis
- **Financial Health Metrics**: Surplus/deficit calculation, budget variance
- **Municipality Synchronization**: Automatic municipality creation and updates

#### 2. Data Correlation Service (`app/services/data_correlation.py`)

**Project-Financial Correlation**
- **Budget Analysis**: Project budget vs municipal capacity
- **Risk Assessment**: Financial deficit, low investment, project size risks
- **Capacity Indicators**: Municipal financial health trends
- **Investment Efficiency**: Project value vs municipal water spending

**Municipal Investment Overview**
- **Portfolio Analysis**: Project distribution and status breakdown
- **Financial Health Assessment**: Budget utilization and trends
- **Recommendations Engine**: AI-driven investment strategy suggestions

#### 3. Automated Scheduler (`app/services/data_scheduler.py`)

**Multi-Task Coordination**
- **DWS Polling**: Every 30 minutes with error handling
- **Treasury Sync**: Hourly financial data updates
- **Correlation Analysis**: Bi-hourly cross-data analysis
- **Health Monitoring**: Real-time system health checks

**Error Management**
- **Exponential Backoff**: Smart retry logic for failed operations
- **Task Recovery**: Automatic restart of failed polling tasks
- **Health Status**: Comprehensive system monitoring

#### 4. Enhanced Database Models (`app/db/models.py`)

**New FinancialData Model**
```python
class FinancialData(Base):
    municipality_id: str
    financial_year: int
    total_budget: float
    total_actual: float
    water_related_capex: float
    infrastructure_budget: float
    surplus_deficit: float
    budget_variance: float
    raw_data: dict
```

## API Endpoints

### Data Synchronization (`/api/v1/data/`)

#### Scheduler Management
- `POST /scheduler/start` - Start automated data polling
- `POST /scheduler/stop` - Stop automated data polling
- `GET /scheduler/status` - Get scheduler health and statistics
- `PUT /scheduler/config` - Update polling intervals and settings

#### Manual Synchronization
- `POST /sync/trigger` - Trigger immediate data sync
  ```json
  {
    "source": "all|dws|treasury|correlation"
  }
  ```

#### Data Correlation
- `GET /correlation/projects` - Get correlation analysis for all projects
- `GET /correlation/projects/{project_id}` - Detailed project correlation
- `GET /correlation/municipalities/{municipality_id}` - Municipal investment overview

#### Health & Quality Monitoring
- `GET /health/data-sources` - Data source health status
- `GET /stats/data-quality` - Data completeness and quality metrics

## Data Flow

```
┌─────────────────┐    ┌─────────────────┐
│   DWS Website   │    │  Treasury API   │
│                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          v                      v
┌─────────────────┐    ┌─────────────────┐
│   DWS Monitor   │    │  Treasury ETL   │
│                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          v                      v
    ┌─────────────────────────────────┐
    │        Database Models          │
    │  ┌─────────────┐ ┌─────────────┐│
    │  │  Projects   │ │ Financial   ││
    │  │             │ │    Data     ││
    │  └─────────────┘ └─────────────┘│
    └─────────────┬───────────────────┘
                  │
                  v
    ┌─────────────────────────────────┐
    │    Data Correlation Service     │
    │                                 │
    │  • Project-Financial Analysis   │
    │  • Risk Assessment             │
    │  • Investment Recommendations  │
    └─────────────┬───────────────────┘
                  │
                  v
    ┌─────────────────────────────────┐
    │     Real-time Notifications     │
    │                                 │
    │  • WebSocket Updates           │
    │  • Change Detection Alerts     │
    │  • System Health Monitoring    │
    └─────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Database Configuration (matches backend/app/core/config.py)
DATABASE_URL="sqlite+aiosqlite:///./waterwatch.db"

# DWS Integration
DWS_POLLING_INTERVAL=1800  # 30 minutes
DWS_BASE_URL="https://ws.dws.gov.za/pmd/level.aspx"

# Treasury Integration
TREASURY_POLLING_INTERVAL=3600  # 1 hour
TREASURY_BASE_URL="https://municipaldata.treasury.gov.za/api"

# Correlation Analysis
CORRELATION_INTERVAL=7200  # 2 hours

# Rate Limiting
RATE_LIMIT_DELAY=2.0
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
```

### Scheduler Configuration

```json
{
  "dws_polling_interval": 1800,
  "treasury_polling_interval": 3600,
  "correlation_interval": 7200,
  "health_check_interval": 300,
  "retry_attempts": 3,
  "retry_delay": 300
}
```

## Sample Data Integration

### DWS Project Data
```json
{
  "external_id": "DWS-WC-001",
  "name": "Berg River-Voëlvlei Augmentation Scheme",
  "municipality": "City of Cape Town",
  "province": "Western Cape",
  "status": "in_progress",
  "progress_percentage": 78,
  "budget_allocated": 4200000000.0,
  "budget_spent": 3276000000.0,
  "contractor": "Aurecon-SMEC Joint Venture"
}
```

### Treasury Financial Data
```json
{
  "municipality_code": "CPT",
  "financial_year": 2024,
  "total_budget": 50000000000.0,
  "water_related_capex": 2500000000.0,
  "infrastructure_budget": 8000000000.0,
  "surplus_deficit": -500000000.0,
  "budget_variance": -2.5
}
```

### Correlation Analysis Output
```json
{
  "project_id": "uuid",
  "project_name": "Berg River-Voëlvlei Augmentation",
  "municipality_name": "City of Cape Town",
  "correlations": {
    "project_vs_infrastructure_budget": {
      "percentage": 52.5,
      "significance": "high"
    },
    "project_vs_water_capex": {
      "percentage": 168.0,
      "significance": "high"
    }
  },
  "insights": [
    "Project represents 52.5% of municipal infrastructure budget - major investment",
    "Project budget exceeds municipal water capex by 68% - external funding likely"
  ],
  "risk_indicators": [
    {
      "type": "financial_deficit",
      "severity": "medium",
      "message": "Municipality has 1.0% budget deficit - monitor project funding"
    }
  ]
}
```

## Deployment

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Migration
```bash
python -m alembic upgrade head
```

### 3. Initialize Services
```python
from app.api.v1.endpoints.data_sync import initialize_data_sync_services
from app.realtime.notifier import DataChangeNotifier

notification_manager = DataChangeNotifier()
initialize_data_sync_services(notification_manager)
```

### 4. Start Scheduler
```bash
curl -X POST http://localhost:8000/api/v1/data/scheduler/start
```

## Monitoring & Alerts

### Health Checks
- **Data Freshness**: Alerts when data is older than expected intervals
- **API Availability**: Monitors external data source availability
- **System Performance**: Database connection pooling and query performance
- **Error Rates**: Tracks and alerts on error thresholds

### Real-time Notifications
- **WebSocket Events**: Live updates for new projects and financial data
- **Change Detection**: Alerts on significant budget or status changes
- **Risk Alerts**: Notifications for high-risk projects or financial issues

## Performance Optimization

### Database Optimization
- **Indexed Queries**: Strategic indexes on frequently queried fields
- **Batch Operations**: Bulk inserts and updates for efficiency
- **Connection Pooling**: Optimized database connection management

### API Rate Limiting
- **Respectful Scraping**: Configurable delays between requests
- **Circuit Breaker**: Automatic fallback when external APIs are unavailable
- **Caching Strategy**: In-memory caching for frequently accessed correlations

## Troubleshooting

### Common Issues

**1. DWS Scraping Fails**
- Check website structure changes
- Verify network connectivity
- Review rate limiting settings
- Fallback to mock data is automatic

**2. Treasury API Issues**
- Validate API endpoints and authentication
- Check municipal code mappings
- Verify financial year parameters

**3. Correlation Analysis Errors**
- Ensure financial data is available for municipalities
- Check project-municipality linkages
- Verify data completeness

### Logging
```python
# View detailed logs
tail -f logs/buka_amanzi.log

# Filter for specific components
grep "DWS" logs/buka_amanzi.log
grep "Treasury" logs/buka_amanzi.log
grep "Correlation" logs/buka_amanzi.log
```

## Future Enhancements

### Planned Features
1. **Machine Learning Models** - Predictive project completion and budget overrun models
2. **Geographic Analysis** - Spatial correlation of projects and municipal boundaries  
3. **Tender Integration** - Integration with government tender systems
4. **Performance Benchmarking** - Municipal performance comparison metrics
5. **Mobile Notifications** - Push notifications for critical project updates

### Integration Opportunities
- **SCOA Classification** - Standard Chart of Accounts mapping
- **Stats SA Integration** - Population and demographic data correlation
- **Weather Data** - Climate impact analysis on project progress
- **Social Media Monitoring** - Community sentiment analysis

---

## Support

For technical support or questions about the data integration system:

- **Documentation**: `/docs/`
- **API Reference**: `/api/v1/docs` (Swagger UI)
- **Health Dashboard**: `/api/v1/data/health/data-sources`
- **System Status**: `/api/v1/data/scheduler/status`
