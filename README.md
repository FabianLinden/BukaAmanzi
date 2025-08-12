# 🌊 Buka Amanzi - Water Watch

**Monitoring water infrastructure projects across South Africa with transparency and community engagement**

*Buka Amanzi* ("Show Water" in Zulu) is a comprehensive community transparency web application for tracking local water infrastructure projects in South Africa. It provides real-time project monitoring, interactive visualizations, budget tracking, and community reporting capabilities.

![Water Theme](https://img.shields.io/badge/Theme-Water%20🌊-06bcf0)
![React](https://img.shields.io/badge/Frontend-React%2018-61dafb)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![WebSockets](https://img.shields.io/badge/Real--time-WebSockets-ff6b6b)
![Status](https://img.shields.io/badge/Status-Production%20Ready-4caf50)

## ✨ Key Features

### 🎯 **Core Functionality**
- **Real-time Project Monitoring** - Live updates via WebSocket connections
- **Interactive Dashboard** - Comprehensive analytics with charts and visualizations
- **Enhanced Project Selection** - User-selectable project progress tracking with intelligent filtering
- **Project Management** - Detailed project tracking with progress indicators
- **Community Reporting** - Public engagement and feedback system
- **Geographic Mapping** - Interactive maps with clustering and data quality indicators
- **Budget Transparency** - Financial tracking and spending visualization
- **Data Quality Management** - Comprehensive data assessment and improvement tools

### 🎨 **Enhanced User Experience**
- **Water-Themed Design** - Beautiful aquatic color palette and animations
- **Immersive Animations** - 12+ custom water-themed CSS animations
- **Interactive Elements** - Floating droplets, water waves, and bubble effects
- **Responsive Design** - Mobile-first approach with Tailwind CSS
- **Accessibility** - WCAG compliant with screen reader support

### 🛠 **Technical Features**
- **Modern Tech Stack** - React 18, FastAPI, WebSockets, Zustand
- **Real-time Updates** - Live data synchronization across all clients
- **Advanced Visualizations** - Chart.js integration with custom themes
- **Geospatial Support** - Leaflet maps with custom markers
- **Advanced ETL Manager** - Production-ready ETL system with job queuing, retry logic, and health monitoring
- **Data Integration** - Comprehensive pipeline for DWS and Treasury data with correlation analysis
- **Comprehensive Testing** - Unit and integration tests with proper mocking
- **Performance Optimized** - Efficient rendering and state management

## 🏗 System Architecture

For the full architecture, data flows, and deployment topology, see system-architecture.md.

Summary:
- Frontend: React 18 + TypeScript, Tailwind CSS, react-chartjs-2, react-leaflet, Zustand state, custom water-themed animations (WaterWave, WaterDroplet, WaterBubbles), and a resilient WebSocket client.
- Backend: FastAPI with async SQLAlchemy 2.0, OpenAPI docs, WebSocket endpoints, ETL services for DWS and Treasury, Redis pub/sub for real-time updates (with safe local fallback), and Alembic migrations.
- Data: SQLite for development (aiosqlite driver) and PostgreSQL recommended for production; Redis for cache/pubsub; comprehensive models for projects, municipalities, reports, budgets, financial data, subscriptions, and change logs.
- Realtime: DataChangeNotifier coordinating Redis pub/sub, broadcasting updates to WebSocket clients with subscription filtering and auto-reconnect behavior.

## 🚀 Getting Started

### Prerequisites
- **Docker & Docker Compose** (recommended)
- **Node.js 18+** and **Python 3.11+** (for local development)

### 🐳 Quick Start (Docker)
```bash
# Clone the repository
git clone https://github.com/your-org/buka-amanzi.git
cd buka-amanzi

# Start all services
docker compose up --build
```

Access Points:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/projects

### 💻 Local Development (Windows PowerShell)

#### Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Option 1: convenience launcher
python run_server.py
# Option 2: uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

API will be available at http://localhost:8000; Vite dev server at http://localhost:5173.

## 🧪 Testing

### Unit Tests
Run the test suite with:
```bash
# Run all tests
pytest

# Run specific test file
pytest testing/unit/test_etl_treasury.py -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

### Test Coverage
- **ETL Pipeline**: Comprehensive tests for data extraction, transformation, and loading
- **Change Detection**: Tests for detecting and notifying about data changes
- **API Endpoints**: Tests for all critical API endpoints
- **Frontend Components**: React component tests with React Testing Library

### Mocking Strategy
- **Database**: SQLite in-memory database for fast, isolated tests
- **External Services**: Mocked HTTP responses and WebSocket connections
- **Async Operations**: Properly handled with `pytest-asyncio`

## 🔄 ETL Pipeline

### **Production-Ready ETL Manager**
The new ETL Manager provides enterprise-grade data processing with:

- **Job Queue Management** - Async job processing with priority queues
- **Worker Pool System** - Concurrent job execution with configurable worker count
- **Retry Logic** - Automatic retry for failed jobs with exponential backoff
- **Health Monitoring** - Real-time status tracking and performance metrics
- **Error Handling** - Comprehensive error logging and notification system
- **Job Status API** - REST endpoints for job monitoring and control

### **ETL Data Sources**

1. **Extracting** data from:
   - Department of Water and Sanitation (DWS) Project Monitoring Dashboard
   - Municipal Money API (National Treasury) - Financial and budget data
   - Cross-referenced correlation analysis between projects and municipal finances

2. **Transforming** data with:
   - Data validation and cleaning
   - Change detection using content hashing
   - Financial correlation analysis (project costs vs municipal budgets)
   - Data enrichment with geospatial and contextual information

3. **Loading** data into the application database with:
   - Transactional batch operations
   - Upsert operations to handle updates
   - Real-time change notifications via WebSocket
   - Data quality metrics and completeness tracking

### **ETL Job Types**
- **DWS Sync** - Water infrastructure project data extraction and processing
- **Treasury Sync** - Municipal financial data extraction with fallback to mock data
- **Correlation Analysis** - Cross-reference project costs with municipal financial capacity

### **Key Components**
- **ETLManager**: Production job orchestration with worker pools and queuing
- **EnhancedDWSMonitor**: Advanced DWS data extraction with change detection
- **MunicipalTreasuryETL**: Municipal financial data processing with API fallbacks
- **DataCorrelationService**: Project-finance correlation analysis and insights
- **DataChangeNotifier**: Real-time notification system for data updates

### **ETL Monitoring & Control**
Access the ETL system via the frontend "Data Sync" tab or API endpoints:
- **Manager Status**: Real-time ETL worker status and job metrics
- **Manual Triggers**: On-demand job execution for specific data sources
- **Data Quality Dashboard**: Live metrics on data completeness and source health
- **Job History**: Track successful syncs and error details

## 🎨 Design System

### **Water Color Palette**
```css
/* Primary Water Blues */
--water-blue-500: #06bcf0;  /* Primary brand color */
--water-blue-600: #0098d1;  /* Darker interactions */

/* Ocean Depths */
--ocean-500: #08b6e9;       /* Deep water */
--ocean-600: #0093c7;       /* Ocean depths */

/* Aqua Accents */
--aqua-400: #0ee0f5;        /* Bright highlights */
--aqua-500: #00c4d7;        /* Aqua primary */

/* Teal Nature */
--teal-400: #2dd4bf;        /* Natural water */
--teal-500: #14b8a6;        /* Fresh water */
```

### **Animation Library**
- `animate-water-ripple` - Expanding ripple effects
- `animate-droplet` - Morphing water droplet shapes
- `animate-float` - Gentle floating motion
- `animate-bubble` - Rising bubble animation
- `animate-wave` - Flowing wave movements
- `animate-glow-pulse` - Ambient glow effects
- `animate-card-float` - Subtle card animations

## 📊 Features Overview

### **Enhanced Dashboard Analytics**
- 📈 **Budget Charts** - Doughnut and bar charts for financial tracking
- 📉 **Interactive Progress Tracking** - User-selectable project progress with timeline visualization and milestone markers
- 🎯 **Smart Project Selection** - Intelligent filtering of trackable projects (excludes template/demo data)
- 📊 **Dynamic Progress Charts** - Real-time updates based on user project selection
- 🗺️ **Advanced Project Mapping** - Geographic distribution with clustering, data quality indicators, and status-based styling
- 📋 **Comprehensive Status Overview** - Real-time project status distribution with enhanced categorization
- 🎯 **KPI Metrics** - Key performance indicators and statistics with enhanced calculations
- 🎨 **Data Quality Integration** - Visual indicators for project data completeness and accuracy

### **Project Management**
- 📋 **Project Cards** - Detailed project information with progress bars
- 🔍 **Advanced Search** - Multi-field search and filtering
- 📱 **Responsive Design** - Optimized for all device sizes
- 🔄 **Real-time Updates** - Live project status changes
- 📊 **Progress Visualization** - Visual progress indicators

### **Community Engagement**
- 📝 **Community Reports** - Public feedback and reporting system
- 🗳️ **Feedback Collection** - Structured community input
- 📷 **Photo Uploads** - Visual documentation support
- 🏷️ **Report Categories** - Organized feedback types
- ✅ **Validation System** - Form validation and error handling

### **Real-time Features**
- 🔄 **Live Updates** - WebSocket-powered real-time data
- 📡 **Connection Management** - Automatic reconnection handling
- 🔔 **Notifications** - In-app notification system
- 👥 **Multi-user Support** - Concurrent user sessions
- ⚡ **Performance Optimized** - Efficient update propagation

## 🗂 Project Structure

```
Buka-Amanzi-3.0/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/                   # Chart components (BudgetChart, ProgressChart)
│   │   │   ├── maps/                     # Mapping components (ProjectMap)
│   │   │   ├── ui/                       # Reusable UI components (Button, Card, ProgressBar)
│   │   │   ├── WaterWave.tsx             # Canvas-based wave/ripple/flow animations
│   │   │   ├── WaterDroplet.tsx          # Droplet animation component
│   │   │   ├── WaterBubbles.tsx          # Bubble effects component
│   │   │   ├── Dashboard.tsx             # Analytics dashboard (charts + map)
│   │   │   ├── ProjectCard.tsx           # Project card UI
│   │   │   ├── CommunityReportForm.tsx   # Community reporting UI
│   │   │   └── ...
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts           # Reusable WebSocket hook (auto-reconnect)
│   │   ├── App.tsx                       # App shell, tabs, notifications, WS wiring
│   │   └── main.tsx                      # Vite entrypoint
│   └── tailwind.config.js                # Water color palette + animation keyframes
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/            # budgets.py, data_sync.py, etl.py, municipalities.py, projects.py, reports.py
│   │   ├── core/                         # config.py (env settings)
│   │   ├── db/                           # session.py, models.py, seed.py
│   │   ├── etl/                          # dws.py, treasury.py (data ingestion)
│   │   ├── realtime/                     # notifier.py (Redis pub/sub + WS)
│   │   ├── services/                     # change_detection, data_correlation, data_scheduler, etl_manager
│   │   ├── utils/                         # logger, helpers
│   │   ├── main.py                        # FastAPI app factory + startup/shutdown
│   │   └── websocket.py                   # WebSocket routes
│   ├── migrations/                        # Alembic migrations (incl. financial_data)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── run_server.py                      # Uvicorn launcher for local dev
│
├── docs/
│   └── DATA_INTEGRATION_SYSTEM.md
├── system-architecture.md                 # Updated architecture diagrams + status
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend (matches backend/app/core/config.py)
DATABASE_URL=sqlite+aiosqlite:///./waterwatch.db
REDIS_URL=redis://localhost:6379/0
API_PREFIX=/api/v1
DEBUG=true

# ETL Configuration
DWS_API_URL=https://ws.dws.gov.za/pmd/level.aspx
TREASURY_API_BASE=https://municipaldata.treasury.gov.za/api
ETL_SYNC_INTERVAL=300

# Frontend (Vite)
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

Notes:
- For Docker Compose, Redis is typically available at redis://redis:6379/0. For local dev without Docker, use redis://localhost:6379/0.
- SQLite is the default dev database; for production use PostgreSQL and update DATABASE_URL accordingly.

## 📈 Performance Features

- ⚡ **Optimized Rendering** - React.memo and useMemo optimizations
- 🎯 **Efficient State Management** - Zustand with selective subscriptions
- 📦 **Code Splitting** - Dynamic imports for better loading
- 🗜️ **Asset Optimization** - Optimized images and fonts
- 🔄 **Caching Strategy** - Redis caching for API responses
- 📊 **Database Indexing** - Optimized database queries

## 🛡 Security & Privacy

- 🔒 **Public Access** - No authentication required (by design)
- 🛡️ **Input Validation** - Comprehensive form validation
- 🧹 **Data Sanitization** - XSS protection and input sanitization
- 📋 **Content Moderation** - Community report moderation system
- 🔐 **Rate Limiting** - API rate limiting and abuse prevention

## 📚 API Documentation

The API is fully documented with OpenAPI/Swagger:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints (v1)

#### Core Data Endpoints
- GET /api/v1/projects — List projects with filtering, pagination
- GET /api/v1/municipalities — List municipalities and stats
- POST /api/v1/reports — Submit community reports

#### ETL Management
- POST /api/v1/etl/sync — Trigger ETL sync jobs (DWS, Treasury, Correlation)
- GET /api/v1/etl/manager/status — ETL Manager status and metrics
- POST /api/v1/etl/manager/start — Start ETL Manager
- POST /api/v1/etl/manager/stop — Stop ETL Manager

#### Data Quality & Analytics
- GET /api/v1/data-quality/projects/{id}/assessment — Get project quality assessment
- GET /api/v1/data-quality/projects/all — Get all projects quality assessments
- GET /api/v1/data-quality/projects/filtered — Fetch projects by quality criteria
- POST /api/v1/data-quality/geocoding/address — Geocode single address
- POST /api/v1/data-quality/geocoding/projects/batch — Batch geocode projects
- GET /api/v1/data-quality/stats — Overall data quality statistics
- POST /api/v1/data-quality/improve/{id} — Improve project data quality
- GET /api/v1/data/stats/data-quality — Data quality and completeness metrics
- GET /api/v1/data/correlation/projects/{id} — Project financial correlation analysis
- GET /api/v1/data/correlation/municipalities/{id} — Municipal investment overview

#### Real-time Communication
- WS /ws/projects — Real-time project updates (subscribe per entity or all)

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Department of Water and Sanitation (DWS) for data access
- Municipal Money project for municipal data
- Open source community for excellent tools and libraries
- South African communities for transparency advocacy

---

**Built with 💙 for water transparency in South Africa**
