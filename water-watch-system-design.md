# 🌊 Buka Amanzi - Water Watch System Design Document

## Executive Summary

**Buka Amanzi** ("Show Water" in Zulu) is a production-ready community transparency web application for tracking local water infrastructure projects in South Africa. This comprehensive system provides real-time project monitoring, interactive data visualizations, budget transparency, and community engagement capabilities through seamless data integration from the Department of Water and Sanitation (DWS) Project Monitoring Dashboard and municipal sources.

### Key Achievements ✅
- **✨ Water-Themed UI/UX**: Immersive aquatic design with 12+ custom animations
- **🔄 Real-time Updates**: WebSocket integration with live data synchronization
- **📊 Interactive Dashboard**: Comprehensive analytics with charts and mapping
- **💧 Enhanced Visualizations**: Custom water-themed components and effects
- **🎨 Modern Frontend**: React 18 with advanced state management and routing
- **⚡ Performance Optimized**: Efficient rendering and data management
- **📱 Responsive Design**: Mobile-first approach with accessibility compliance
- **🛠 Production Ready**: Complete CI/CD pipeline and deployment configuration

## 1. Recommended Tech Stack & Rationale

### Backend Stack
- **Framework**: FastAPI (Python 3.11+)
  - *Rationale*: High performance, automatic OpenAPI generation, excellent async support, type hints, native WebSocket support
- **ORM**: SQLAlchemy 2.0 with Alembic
  - *Rationale*: Mature, supports async operations, excellent migration tools
- **Database**:
  - *Development*: SQLite with aiosqlite
    - *Rationale*: Simple setup, zero-configuration, good for development and testing
  - *Production*: PostgreSQL 15+ with PostGIS extension
    - *Rationale*: Robust geospatial support, JSONB for flexible data storage, excellent performance
- **Cache**: Redis 7+
  - *Rationale*: Fast caching, pub/sub for real-time features, WebSocket session management
- **Background Processing**: Async FastAPI endpoints with in-process ETL + Celery for complex tasks
  - *Rationale*: Simplified architecture with option for scalable background processing
- **Real-time Communication**: FastAPI WebSockets with Redis pub/sub
  - *Rationale*: Native WebSocket support, scalable real-time updates, connection management
- **Authentication**: None (Open source, public access)
  - *Rationale*: Simplified architecture, no user management overhead, fully transparent public access

### Frontend Stack
- **Framework**: React 18 with TypeScript
  - *Rationale*: Component reusability, strong typing, excellent ecosystem
- **State Management**: Zustand
  - *Rationale*: Lightweight, TypeScript-first, less boilerplate than Redux
- **Real-time Communication**: WebSocket API with automatic reconnection
  - *Rationale*: Live updates, improved user experience, real-time project status
- **Mapping**: Leaflet (react-leaflet)
  - *Rationale*: Lighter bundle, open-source tiles, aligns with current frontend dependencies
- **Charts**: Chart.js with react-chartjs-2
  - *Rationale*: Flexible, well-documented, good performance
- **UI Framework**: Tailwind CSS + Headless UI
  - *Rationale*: Utility-first, mobile-responsive, accessible components
- **Animations**: Framer Motion + Lottie React
  - *Rationale*: Smooth micro-interactions, loading animations, enhanced UX
- **Build Tool**: Vite
  - *Rationale*: Fast development, optimized builds, TypeScript support

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **File Storage**: MinIO (S3-compatible) for development, AWS S3 for production
- **Monitoring**: Prometheus + Grafana + Sentry
- **CI/CD**: GitHub Actions

## 2. System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐    ┌─────────────┐
│  DWS PMD Web   │───▶│   ETL Pipeline   │───▶│  Database   │◀──▶│    API      │
│   Scraper      │    │  (Enhanced with  │    │  (SQLite/   │    │  (FastAPI)  │
│  (Enhanced)    │    │ Change Detection)│    │  PostgreSQL)│    └──────┬──────┘
└─────────────────┘    └──────────────────┘    └─────────────┘           │
                                │                                       ▼
┌─────────────────┐             ▼               ┌─────────────┐    ┌─────────────┐
│  WebSocket      │◀────── Redis Pub/Sub ─────▶│  Connection │    │   Users     │
│  Notification   │                             │  Manager    │    │             │
│  System         │                             └─────────────┘    └─────────────┘
└─────────────────┘                                                      │
                                                                        ▼
┌─────────────────┐                                              ┌─────────────┐
│  Frontend App   │◀─────── WebSocket Connection ────────────────┤  Real-time  │
│  (React +       │                                              │  Updates    │
│  WebSockets)    │                                              │             │
└─────────────────┘                                              └─────────────┘

Key Data Flow:
1. ETL Pipeline extracts data from DWS Project Monitoring Dashboard
2. Change detection system identifies data modifications
3. Updates are published to Redis pub/sub channels
4. WebSocket connections receive real-time notifications
5. Frontend updates UI immediately without page refresh
6. Users see live project status and progress updates
```

### Container Layout
1. **web-api**: FastAPI application server with WebSocket support
2. **worker**: Celery workers for background tasks
3. **scheduler**: Celery beat scheduler
4. **database**: PostgreSQL with PostGIS
5. **redis**: Cache, message broker, and pub/sub for real-time features
6. **frontend**: React application (Vite dev server; Nginx in production builds)
7. **minio**: Object storage for development

### Enhanced Data Flow with Real-time Updates
1. **Data Ingestion**:
   - ETL pipeline extracts data from the DWS Project Monitoring Dashboard
   - Enhanced scraper includes content hash comparison for change detection
   - Data is processed in-memory and loaded into the database
   - **NEW**: Change detection triggers real-time notifications

2. **Data Processing**:
   - Data is cleaned and standardized during extraction
   - Municipalities are matched by code and name
   - Project counts and total values are aggregated
   - Dashboard URLs are generated for each municipality
   - **NEW**: Changes are published to Redis pub/sub channels

3. **Real-time Notification System**:
   - **NEW**: WebSocket connections managed through Redis
   - **NEW**: Project updates broadcast to connected clients
   - **NEW**: Automatic reconnection handling for dropped connections
   - **NEW**: Selective subscriptions based on user interests (municipality, project type)

4. **Data Storage**:
   - SQLite used for development and testing
   - PostgreSQL with PostGIS planned for production
   - Database schema designed for easy migration between backends
   - **NEW**: Change log table for tracking data modifications

5. **API Serving**:
   - Async FastAPI endpoints for frontend consumption
   - Automatic OpenAPI documentation
   - Response caching for better performance
   - **NEW**: WebSocket endpoints for real-time communication

6. **Frontend Presentation**:
   - React-based single-page application with animations and micro-interactions
   - Interactive dashboards and data visualizations with charts and maps
   - Responsive design for desktop 
   - **NEW**: Live updates without page refresh through WebSocket integration
   - **NEW**: Real-time status indicators and progress animations
   - Recommend using Vite for development and production builds

## 3. Database Schema

### Core Tables

#### municipalities
```sql
CREATE TABLE municipalities (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    province VARCHAR(100),
    project_count INTEGER DEFAULT 0,
    total_value FLOAT DEFAULT 0.0,
    dashboard_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- For SQLite compatibility
CREATE INDEX IF NOT EXISTS idx_municipalities_code ON municipalities(code);

-- For PostgreSQL (planned)
-- CREATE INDEX idx_municipalities_geom ON municipalities USING GIST(geometry);
-- SELECT create_hypertable('municipalities', 'created_at');
```

#### projects
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255),
    source VARCHAR(50) NOT NULL, -- 'municipal_money', 'dws_water_quality'
    municipality_id UUID REFERENCES municipalities(id),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    project_type VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    location GEOMETRY(POINT, 4326),
    address TEXT,
    budget_allocated DECIMAL(15,2),
    budget_spent DECIMAL(15,2),
    progress_percentage INTEGER DEFAULT 0,
    contractor VARCHAR(255),
    raw_data JSONB, -- Store original API response
    content_hash VARCHAR(64), -- NEW: For change detection
    last_scraped_at TIMESTAMP WITH TIME ZONE, -- NEW: Last successful scrape
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_projects_location ON projects USING GIST (location);
CREATE INDEX idx_projects_municipality ON projects (municipality_id);
CREATE INDEX idx_projects_status ON projects (status);
CREATE INDEX idx_projects_external_id ON projects (external_id, source);
CREATE INDEX idx_projects_content_hash ON projects (content_hash); -- NEW: For change detection
```

#### data_change_log (NEW TABLE)
```sql
-- NEW: Track all data changes for real-time notifications
CREATE TABLE data_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'project', 'municipality', 'budget'
    entity_id UUID NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- 'created', 'updated', 'deleted'
    field_changes JSONB, -- Specific field changes for granular updates
    old_values JSONB, -- Previous values
    new_values JSONB, -- New values
    source VARCHAR(50) NOT NULL, -- 'etl_pipeline', 'admin_action', 'community_report'
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_change_log_entity ON data_change_log (entity_type, entity_id);
CREATE INDEX idx_change_log_created_at ON data_change_log (created_at);
CREATE INDEX idx_change_log_notification ON data_change_log (notification_sent, created_at);
```

#### websocket_subscriptions (NEW TABLE)
```sql
-- NEW: Track WebSocket subscriptions for targeted notifications
CREATE TABLE websocket_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id VARCHAR(255) NOT NULL,
    subscription_type VARCHAR(50) NOT NULL, -- 'municipality', 'project', 'all'
    entity_id UUID, -- NULL for 'all' subscriptions
    filters JSONB, -- Additional filtering criteria
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_websocket_subs_connection ON websocket_subscriptions (connection_id);
CREATE INDEX idx_websocket_subs_entity ON websocket_subscriptions (subscription_type, entity_id);
```

#### budgets
```sql
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    budget_type VARCHAR(50) NOT NULL, -- 'allocated', 'revised', 'spent'
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'ZAR',
    financial_year VARCHAR(9) NOT NULL, -- '2023/2024'
    quarter INTEGER, -- 1-4
    source VARCHAR(50) NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_budgets_project ON budgets (project_id);
CREATE INDEX idx_budgets_financial_year ON budgets (financial_year);
```

#### contributors (optional contact info)
```sql
CREATE TABLE contributors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255), -- Optional display name
    email VARCHAR(255), -- Optional contact for follow-up
    organization VARCHAR(255), -- Optional organization affiliation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_contributors_email ON contributors (email);
```

#### reports
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contributor_id UUID REFERENCES contributors(id), -- NULL for fully anonymous reports
    project_id UUID REFERENCES projects(id),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL,
    address TEXT,
    report_type VARCHAR(50) NOT NULL, -- 'progress_update', 'issue', 'completion', 'quality_concern'
    status VARCHAR(50) DEFAULT 'published', -- 'published', 'flagged', 'spam'
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    photos JSONB, -- Array of photo URLs
    contributor_name VARCHAR(255), -- Display name for attribution
    admin_notes TEXT, -- Internal notes for data quality
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_reports_location ON reports USING GIST (location);
CREATE INDEX idx_reports_project ON reports (project_id);
CREATE INDEX idx_reports_status ON reports (status);
CREATE INDEX idx_reports_created_at ON reports (created_at);
```

#### admin_actions
```sql
CREATE TABLE admin_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_name VARCHAR(255) NOT NULL, -- Admin identifier
    target_type VARCHAR(50) NOT NULL, -- 'report', 'project'
    target_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'flag', 'unflag', 'link_to_project', 'update_data'
    reason TEXT,
    metadata JSONB, -- Additional action-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_admin_actions_admin ON admin_actions (admin_name);
CREATE INDEX idx_admin_actions_target ON admin_actions (target_type, target_id);
```

### Auditing & Versioning Approach
- **Raw Data Storage**: All external API responses stored in `raw_data` JSONB fields
- **Change Tracking**: Use triggers to maintain `updated_at` timestamps and populate `data_change_log`
- **Content Hash Tracking**: SHA-256 hashes for efficient change detection
- **Real-time Notifications**: All changes logged and broadcast via WebSocket
- **Audit Logs**: All moderation actions logged in `admin_actions` table
- **Data Lineage**: Track source and ingestion timestamp for all external data

## 4. ETL / Data Ingestion Plan with Real-time Enhancement

### Enhanced DWS Project Monitoring Dashboard Scraper
```python
# Enhanced configuration with change detection
DWS_PMD_CONFIG = {
    'base_url': 'https://ws.dws.gov.za/pmd/level.aspx',
    'encrypted_params': 'VWReJm+SmGcCYM6pJQAmVBLmM33+9zWef3oVk0rPHvehd5PO8glfwc6rREAYyNxl',
    'timeout': 30,
    'retry_attempts': 3,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'change_detection': {
        'hash_algorithm': 'sha256',
        'poll_interval': 300,  # 5 minutes for change detection
        'full_sync_interval': 3600,  # 1 hour for complete data sync
    }
}

# Enhanced scraper with real-time capabilities
class EnhancedDWSMonitor:
    def __init__(self, notification_manager: 'DataChangeNotifier'):
        self.notification_manager = notification_manager
        self.last_content_hashes = {}
    
    async def poll_with_change_detection(self):
        """Enhanced polling with change detection and real-time notifications"""
        try:
            current_data = await self.fetch_dws_data()
            current_hash = self.calculate_content_hash(current_data)
            
            if current_hash != self.last_content_hashes.get('dws_projects'):
                logger.info("DWS data changes detected, processing updates")
                changes = await self.process_data_changes(current_data)
                
                # Update hash tracking
                self.last_content_hashes['dws_projects'] = current_hash
                
                # Trigger real-time notifications
                for change in changes:
                    await self.notification_manager.notify_change(change)
                    
                logger.info(f"Processed {len(changes)} project changes")
            else:
                logger.debug("No changes detected in DWS data")
                
        except Exception as e:
            logger.error(f"Error in change detection polling: {e}")
            await self.notification_manager.notify_system_error(
                "DWS polling error", str(e)
            )
    
    def calculate_content_hash(self, data: dict) -> str:
        """Calculate SHA-256 hash of content for change detection"""
        import hashlib
        import json
        
        # Sort and serialize data for consistent hashing
        normalized_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(normalized_data.encode()).hexdigest()
    
    async def process_data_changes(self, current_data: dict) -> List[dict]:
        """Process detected changes and return change objects"""
        changes = []
        
        for project in current_data.get('projects', []):
            existing_project = await self.get_project_by_external_id(
                project['external_id']
            )
            
            if existing_project:
                # Check for specific field changes
                field_changes = self.detect_field_changes(
                    existing_project, project
                )
                if field_changes:
                    changes.append({
                        'type': 'project_updated',
                        'project_id': existing_project.id,
                        'changes': field_changes,
                        'timestamp': datetime.utcnow()
                    })
            else:
                # New project detected
                changes.append({
                    'type': 'project_created',
                    'project_data': project,
                    'timestamp': datetime.utcnow()
                })
        
        return changes
```

### Municipal Money Connector
```python
# Polling Configuration
MUNICIPAL_MONEY_CONFIG = {
    'base_url': 'https://municipaldata.treasury.gov.za/api',
    'endpoints': {
        'municipalities': '/municipalities/municipality/_search',
        'capital_projects': '/capital-projects/project/_search',
        'budgets': '/budgets/budget/_search'
    },
    'poll_interval': '0 2 * * *',  # Daily at 2 AM
    'rate_limit': 30,  # requests per minute
    'timeout': 30,
    'retry_attempts': 3,
    'backoff_factor': 2,
    'page_size': 100
}
```

### Real-time Notification System (NEW)
```python
import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

class DataChangeNotifier:
    """Manages real-time notifications for data changes"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # connection_id -> entity_ids
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        
        # Store connection in Redis for multi-instance support
        await self.redis_client.sadd("websocket_connections", connection_id)
        
        logger.info(f"WebSocket connected: {connection_id}")
    
    async def disconnect(self, connection_id: str):
        """Clean up disconnected WebSocket"""
        self.active_connections.pop(connection_id, None)
        self.subscriptions.pop(connection_id, None)
        
        await self.redis_client.srem("websocket_connections", connection_id)
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe_to_entity(self, connection_id: str, entity_type: str, entity_id: str):
        """Subscribe connection to specific entity updates"""
        if connection_id in self.subscriptions:
            subscription_key = f"{entity_type}:{entity_id}"
            self.subscriptions[connection_id].add(subscription_key)
            
            # Store subscription in database
            # (implementation details in service layer)
    
    async def notify_change(self, change: dict):
        """Broadcast change to interested connections"""
        notification = {
            "type": "data_update",
            "timestamp": change.get('timestamp', datetime.utcnow()).isoformat(),
            "data": change
        }
        
        # Publish to Redis pub/sub for multi-instance support
        await self.redis_client.publish(
            "project_changes", 
            json.dumps(notification, default=str)
        )
        
        # Also notify local connections directly
        await self.broadcast_to_subscribers(notification, change)
    
    async def broadcast_to_subscribers(self, notification: dict, change: dict):
        """Send notification to relevant WebSocket connections"""
        entity_key = f"{change.get('entity_type', 'project')}:{change.get('entity_id')}"
        
        disconnected_connections = []
        
        for connection_id, subscriptions in self.subscriptions.items():
            if entity_key in subscriptions or 'all' in subscriptions:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    try:
                        await websocket.send_text(json.dumps(notification, default=str))
                    except WebSocketDisconnect:
                        disconnected_connections.append(connection_id)
                    except Exception as e:
                        logger.error(f"Error sending to {connection_id}: {e}")
                        disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)
    
    async def notify_project_change(self, project_id: str, changes: dict):
        """Notify about specific project changes"""
        await self.notify_change({
            "entity_type": "project",
            "entity_id": project_id,
            "change_type": "updated",
            "changes": changes,
            "timestamp": datetime.utcnow()
        })
    
    async def notify_system_error(self, error_type: str, message: str):
        """Broadcast system errors to all connections"""
        notification = {
            "type": "system_error",
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all active connections
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(notification, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting system error to {connection_id}: {e}")

# Redis pub/sub listener for multi-instance support
class RedisPubSubListener:
    """Listens to Redis pub/sub for cross-instance notifications"""
    
    def __init__(self, redis_client: redis.Redis, notifier: DataChangeNotifier):
        self.redis_client = redis_client
        self.notifier = notifier
    
    async def start_listening(self):
        """Start listening to Redis pub/sub channels"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("project_changes", "system_notifications")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await self.notifier.broadcast_to_subscribers(data, data.get("data", {}))
                except Exception as e:
                    logger.error(f"Error processing pub/sub message: {e}")
```

### Data Normalization Rules
1. **Project Mapping**: Standardize project types and statuses across sources
2. **Location Handling**: Geocode addresses when coordinates missing
3. **Budget Reconciliation**: Handle different budget reporting formats
4. **Conflict Resolution**: Last-updated-wins with admin override capability
5. **Missing Data**: Flag incomplete records for manual review
6. **Change Detection**: Hash-based comparison for efficient change identification
7. **Real-time Updates**: Immediate notification of data changes to connected clients

### Enhanced ETL Workflow
1. **Extract**: Fetch data from external APIs with pagination
2. **Change Detection**: Compare content hashes to identify modifications
3. **Transform**: Normalize fields, validate data types, geocode locations
4. **Load**: Upsert to database with conflict detection
5. **Notify**: Broadcast changes to WebSocket subscribers in real-time

### Error Handling
- **Retry Mechanism**:
  - Exponential backoff for failed requests
  - Configurable retry attempts (default: 3)
  - Circuit breaker pattern to prevent cascading failures

- **Logging**:
  - Structured logging with timestamps and request IDs
  - Different log levels (DEBUG, INFO, WARNING, ERROR)
  - Log rotation and retention policies

- **Monitoring**:
  - Health check endpoints
  - Performance metrics collection
  - WebSocket connection monitoring
  - Real-time notification delivery tracking
  - Alerting for critical failures

- **Recovery**:
  - Transaction management for data consistency
  - Dead letter queue for failed messages
  - Automatic WebSocket reconnection handling
  - Manual intervention procedures for critical failures

## 5. API Design with WebSocket Integration

### Public API Endpoints
All endpoints are publicly accessible without authentication.

#### Municipalities
- `GET /api/v1/municipalities` - List municipalities with filtering and pagination
  - Parameters: 
    - `province`: Filter by province name
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 20, max: 100)
- `GET /api/v1/municipalities/{municipality_id}` - Get municipality details
- `GET /api/v1/municipalities/{municipality_id}/projects` - Get projects for a specific municipality

#### Projects
- `GET /api/v1/projects` - List projects with filtering, pagination, and geographical search
  - Parameters:
    - `status`: Filter by project status
    - `municipality_id`: Filter by municipality
    - `bbox`: Bounding box for geographical filtering (southwest_lng,southwest_lat,northeast_lng,northeast_lat)
    - `center`: Center point with radius search (lng,lat,radius_km)
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 20, max: 100)
- `GET /api/v1/projects/{project_id}` - Get detailed project information

### WebSocket Endpoints (NEW)
```yaml
/ws/projects:
  description: Subscribe to real-time project updates
  parameters:
    - connection_id: Unique identifier for the WebSocket connection
  messages:
    subscribe:
      description: Subscribe to specific updates
      payload:
        type: object
        properties:
          action: { type: string, enum: [subscribe, unsubscribe] }
          entity_type: { type: string, enum: [project, municipality, all] }
          entity_id: { type: string, format: uuid, nullable: true }
          filters: 
            type: object
            properties:
              status: { type: array, items: { type: string } }
              municipality_id: { type: string, format: uuid }
              project_type: { type: array, items: { type: string } }
    
    project_update:
      description: Real-time project data updates
      payload:
        type: object
        properties:
          type: { type: string, value: "data_update" }
          timestamp: { type: string, format: date-time }
          data:
            type: object
            properties:
              entity_type: { type: string }
              entity_id: { type: string, format: uuid }
              change_type: { type: string, enum: [created, updated, deleted] }
              changes: { type: object }
              old_values: { type: object }
              new_values: { type: object }
    
    system_notification:
      description: System-wide notifications
      payload:
        type: object
        properties:
          type: { type: string, value: "system_error" }
          error_type: { type: string }
          message: { type: string }
          timestamp: { type: string, format: date-time }

/ws/municipalities/{municipality_id}:
  description: Subscribe to updates for a specific municipality
  parameters:
    - municipality_id: UUID of the municipality
```

### FastAPI WebSocket Implementation
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uuid

app = FastAPI()

# Initialize notification manager
notification_manager = DataChangeNotifier(redis_client)

@app.websocket("/ws/projects")
async def websocket_projects(websocket: WebSocket):
    connection_id = str(uuid.uuid4())
    
    try:
        await notification_manager.connect(websocket, connection_id)
        
        while True:
            # Listen for subscription messages from client
            data = await websocket.receive_json()
            
            if data.get("action") == "subscribe":
                entity_type = data.get("entity_type", "all")
                entity_id = data.get("entity_id")
                
                await notification_manager.subscribe_to_entity(
                    connection_id, entity_type, entity_id
                )
                
                # Acknowledge subscription
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
    except WebSocketDisconnect:
        await notification_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        await notification_manager.disconnect(connection_id)

@app.websocket("/ws/municipalities/{municipality_id}")
async def websocket_municipality(websocket: WebSocket, municipality_id: str):
    connection_id = str(uuid.uuid4())
    
    try:
        await notification_manager.connect(websocket, connection_id)
        # Auto-subscribe to municipality updates
        await notification_manager.subscribe_to_entity(
            connection_id, "municipality", municipality_id
        )
        
        # Keep connection alive and handle any additional messages
        while True:
            await websocket.receive_text()  # Keep connection open
            
    except WebSocketDisconnect:
        await notification_manager.disconnect(connection_id)
```

### Community Reports Endpoints
```yaml
/reports:
  get:
    summary: List community reports
    parameters:
      - name: project_id
        in: query
        schema: { type: string, format: uuid }
      - name: status
        in: query
        schema: { type: string, enum: [pending, approved, rejected] }
      - name: bbox
        in: query
        schema: { type: string }
    responses:
      200:
        description: Reports retrieved successfully

  post:

## Conclusion

This system design provides a comprehensive blueprint for building Water Watch, a production-ready community transparency platform for water infrastructure projects in South Africa. The architecture emphasizes scalability and user experience while meeting all specified requirements.

The modular design allows for iterative development and future enhancements, while the robust ETL pipeline ensures reliable data integration from multiple government sources. The community reporting system balances transparency with content moderation, creating a trustworthy platform for citizen engagement.

**Next Steps**: Review and approve this design document before proceeding with implementation accordingly. Create the project as if you were a full-stack developer with a focus on the user experience and the best practices of software development.

## 9. Testing Strategy (Updated)

### Unit Testing
- **Coverage**: 90%+ coverage for critical paths
- **Frameworks**: pytest with pytest-asyncio for async tests
- **Mocking**: unittest.mock for external dependencies
- **Fixtures**: Reusable test data and mocks

### Integration Testing
- **Database**: Test with SQLite in-memory database
- **API**: Test API endpoints with TestClient
- **WebSockets**: Test real-time functionality

### Test Directory Structure
```
testing/
├── unit/
│   ├── test_etl_treasury.py     # Treasury ETL tests
│   ├── test_etl_dws.py          # DWS ETL tests
│   └── test_models.py           # Database model tests
├── integration/
│   ├── test_etl_integration.py  # End-to-end ETL tests
│   └── test_api_endpoints.py    # API integration tests
└── conftest.py                 # Test fixtures
```

### Continuous Integration
- **GitHub Actions**: Automated test runs on push/PR
- **Code Quality**: flake8, black, mypy
- **Test Reports**: JUnit XML and coverage reports

## 11. Change Management (Updated)

### Data Change Detection
- **Content Hashing**: MD5 hashing of data payloads
- **Field-level Comparison**: Identify specific changes
- **Versioning**: Track changes over time

### Notification System
- **WebSockets**: Real-time updates to connected clients
- **Redis Pub/Sub**: Cross-instance communication
- **Event Logging**: Audit trail of all changes

### Change Notification Flow
1. ETL process detects data change
2. New data is stored in database
3. Change notification is published to Redis
4. WebSocket connections are updated
5. UI reflects changes in real-time
