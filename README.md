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
- **Project Management** - Detailed project tracking with progress indicators
- **Community Reporting** - Public engagement and feedback system
- **Geographic Mapping** - Interactive maps with project locations
- **Budget Transparency** - Financial tracking and spending visualization

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
- **Data Integration** - ETL pipeline for DWS and municipal data sources
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

### **Dashboard Analytics**
- 📈 **Budget Charts** - Doughnut and bar charts for financial tracking
- 📉 **Progress Tracking** - Timeline visualization with milestone markers
- 🗺️ **Project Mapping** - Geographic distribution with status indicators
- 📋 **Status Overview** - Real-time project status distribution
- 🎯 **KPI Metrics** - Key performance indicators and statistics

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
│   │   ├── services/                     # change_detection, data_correlation, data_scheduler
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
- GET /api/v1/projects — List projects with filtering, pagination
- GET /api/v1/municipalities — List municipalities and stats
- POST /api/v1/reports — Submit community reports
- POST /api/v1/data/sync/trigger — Trigger manual data sync
- GET /api/v1/data/scheduler/status — Scheduler health and stats
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

