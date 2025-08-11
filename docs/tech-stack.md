# Buka Amanzi - Tech Stack

This document outlines the technology stack used in the Buka Amanzi project.

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
