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
uv run main_refactored.py  # Start refactored version (Clean Architecture)

# Environment setup
python scripts/env_config.py --generate  # Generate .env.example
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
cd backend

# Backend integration tests
python test/integration/test_system_api.py

# Admin API tests
bash test/scripts/test_admin_api.sh

# Run specific integration tests
python test/integration/test_refactored_system.py
python test/integration/complete_refactor_test.py

# Trading simulation tests
python test/simulation/market_simulation.py
```

## Key Files to Understand

### Backend Core Files
- `backend/app/main_refactored.py` - Main FastAPI application (Clean Architecture)
- `backend/app/main.py` - Legacy main application
- `backend/app/core/database.py` - MongoDB connection and setup
- `backend/app/core/rbac.py` - Role-based access control implementation
- `backend/app/core/security.py` - JWT authentication and security
- `backend/app/application/dependencies.py` - Dependency injection container
- `backend/scripts/env_config.py` - Environment configuration utility

### Frontend Core Files
- `frontend/src/lib/api.js` - Centralized API client with error handling and retry logic
- `frontend/src/contexts/PermissionContext.js` - RBAC permission system for frontend
- `frontend/src/components/PermissionGuard.js` - Permission-based component rendering
- `frontend/package.json` - Uses pnpm with Turbopack for fast development

### Bot Files
- `bot/main.py` - Telegram bot entry point
- `bot/bot/handlers/` - Command and message handlers
- `bot/api/` - FastAPI server for webhook and notifications

## Important Implementation Details

### Permission System
- Backend uses MongoDB-based role checking for admin endpoints
- Frontend uses React Context to minimize permission API calls
- Permission checks are centralized through `PermissionGuard` components

### Soft Delete Pattern
- Announcements use soft delete (mark as `is_deleted: true`) instead of hard delete
- Deleted items remain in database for audit purposes
- Frontend displays deleted items with visual indicators

### Error Handling
- API client includes retry mechanisms for network errors
- Comprehensive error categorization and user feedback
- ObjectId validation for MongoDB document operations