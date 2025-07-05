# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SITCON Camp 2025 點數系統 (Stock Trading System) - A multi-service application with:
- **Frontend**: Next.js web interface for viewing stock prices and admin management
- **Backend**: FastAPI server implementing the trading system API
- **Bot**: Telegram bot for user interactions and trading

## Common Development Commands

### Frontend (Next.js)
```bash
cd frontend
pnpm dev          # Development server with turbopack
pnpm build        # Production build
pnpm start        # Production server
pnpm lint         # Linting
```

### Backend (FastAPI)
```bash
cd backend
uv venv           # Create virtual environment
uv sync           # Install dependencies
uv run ./main.py  # Start development server
```

### Bot (Telegram)
```bash
cd bot
uv venv           # Create virtual environment
uv sync           # Install dependencies
uv run main.py    # Start bot
```

## Architecture Overview

### Backend Architecture
- **Clean Architecture**: Domain-driven design with separation of concerns
- **Layers**: 
  - `app/routers/` - API endpoints and request handling
  - `app/services/` - Business logic and application services
  - `app/domain/` - Core business entities and domain logic
  - `app/infrastructure/` - External dependencies (MongoDB repositories)
  - `app/core/` - Shared utilities (database, security, RBAC)
- **Database**: MongoDB with Motor async driver
- **Authentication**: JWT-based admin authentication

### Frontend Architecture
- **Next.js 15** with App Router
- **State Management**: React Context (DataCacheContext, PermissionContext)
- **Styling**: Tailwind CSS with custom components
- **Charts**: Chart.js and react-chartjs-2 for stock visualizations
- **API Integration**: Custom API client in `src/lib/api.js`

### Key Components
- **RBAC System**: Role-based access control implemented across backend
- **Real-time Data**: Stock price updates and market data
- **Admin Dashboard**: User management, announcements, market controls
- **Trading Interface**: Stock trading, leaderboard, market status

## Environment Setup

### Backend Environment Variables
Create `.env` file in backend directory:
```bash
python scripts/env_config.py --generate  # Generate .env.example
mv .env.example .env                      # Rename and configure
```

### Database
- MongoDB required for backend
- Connection configured via `CAMP_MONGO_URI` environment variable

### API Documentation
- Backend API docs available at `/docs` (Swagger UI)
- Implements [SITCON Camp 2025 RESTful API specification](https://hackmd.io/@SITCON/ryuqDN7zex)

## Testing

### Backend Testing
- Test files in `backend/test/`
- Integration tests: `test/integration/`
- Unit tests: `test/unit/`
- Simulation tests: `test/simulation/`

### Test Scripts
```bash
# Backend integration tests
python test/integration/test_system_api.py

# Admin API tests
bash test/scripts/test_admin_api.sh
```

## Key Files to Understand

- `backend/app/main_refactored.py` - Main FastAPI application
- `backend/app/core/database.py` - MongoDB connection and setup
- `backend/app/core/rbac.py` - Role-based access control implementation
- `frontend/src/lib/api.js` - API client with error handling
- `frontend/src/contexts/` - React context providers for state management
- `bot/main.py` - Telegram bot entry point