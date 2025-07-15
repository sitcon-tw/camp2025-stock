# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SITCON Camp 2025 點數系統 (Stock Trading System) is a full-stack web application for managing a virtual stock trading game during SITCON Camp. The system includes a web interface, Telegram bot, and admin dashboard.

### Key Architecture Components

```
├── frontend/     # Next.js web interface
├── backend/      # FastAPI REST API server  
└── bot/          # Telegram bot with separate API
```

## Common Development Commands

### Backend (FastAPI)
```bash
cd backend

# Install dependencies with uv
uv sync

# Start development server
uv run ./main.py

# Alternative start method
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Generate environment template
python scripts/env_config.py --generate

# API documentation available at:
# - http://localhost:8000/docs (Swagger)
# - http://localhost:8000/redoc
```

### Frontend (Next.js)
```bash
cd frontend

# Install dependencies
pnpm install

# Start development server (with turbopack)
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint
```

### Bot (Telegram)
```bash
cd bot

# Install dependencies
uv sync

# Start bot server
uv run main.py
```

## Architecture Overview

### Backend Structure
- **Services Layer**: Modular business logic in `app/services/` organized by domain (user_management/, trading/, market/, admin/, etc.)
- **Routers Layer**: API endpoints in `app/routers/` organized by domain
- **RBAC System**: Role-based access control with permissions in `app/core/rbac.py`
- **Database**: MongoDB with async Motor driver, collections defined in `app/core/database.py`
- **Domain Architecture**: Clean architecture with domain/, infrastructure/, and application/ layers

### Frontend Architecture
- **App Router**: Next.js 15 with app directory structure
- **Components**: Organized by domain (`/admin`, `/trading`, `/ui`)
- **Context**: Permission management via React Context (`PermissionContext`, `DataCacheContext`)
- **API Integration**: Centralized in `src/lib/api.js`
- **Package Manager**: Uses pnpm with workspace configuration
- **Styling**: Tailwind CSS with custom components

### Bot Architecture
- **Telegram Bot**: Uses python-telegram-bot library
- **API Server**: FastAPI server for webhooks and notifications
- **Handlers**: Organized by feature (commands, buttons, conversation flows)
- **Integration**: Communicates with backend via HTTP APIs
- **PVP Manager**: Handles player vs player challenges and games

### Key Systems

**Permission System**: 
- Backend: Enum-based roles (STUDENT, QRCODE_MANAGER, POINT_MANAGER, QR_POINT_MANAGER, ANNOUNCER, ADMIN) with granular permissions
- Frontend: Permission guards and context providers for UI access control
- Consistent permission constants between frontend/backend
- Use `@require_permission()` decorator or `RBACService.has_permission()` for access control

**Market Trading**:
- Real-time price updates and order matching
- Manual and scheduled market open/close functionality  
- Trading hours validation with timezone handling (Asia/Taipei)

**Admin Dashboard**:
- User management with detailed member lists
- System configuration (trading limits, market hours)
- Announcement management with Telegram broadcast

## Important Implementation Details

### Time Zone Handling
All time displays must use Taiwan timezone (UTC+8). Use:
```javascript
new Date(timestamp).toLocaleString('zh-TW', {
    timeZone: 'Asia/Taipei',
    // ... other options
})
```

### Market Control Logic
The system has dual market control:
1. **Manual Override**: `manual_control` collection (highest priority)
2. **Scheduled Hours**: `market_hours` collection (fallback)

The `_is_market_open()` function in both `user_service.py` and `application/services.py` must check manual control first.

### Database Collections
Key MongoDB collections:
- `USERS`: User accounts and points
- `STOCKS`: Stock holdings per user
- `STOCK_ORDERS`: All trading orders
- `MARKET_CONFIG`: Market settings (hours, limits, manual control)
- `ANNOUNCEMENTS`: System announcements

### API Authentication
- Admin APIs: JWT token with role-based permissions
- User APIs: Telegram-based authentication
- Public APIs: No authentication required

## Development Notes

### Running Tests
Backend tests are in `/test` directory:
```bash
cd backend

# Run integration tests
python test/integration/test_system_api.py

# Run specific test suites
python test/integration/test_refactored_system.py
python test/integration/complete_refactor_test.py

# Run test scripts
bash test/scripts/test_admin_api.sh
python test/scripts/quick_setup.py
```

### Configuration
Backend uses `.env` files. Generate template:
```bash
cd backend
python scripts/env_config.py --generate
```

Frontend configuration is in Next.js config files and environment variables.

### MongoDB Setup
Ensure MongoDB is running on localhost:27017 or configure connection string in backend config.

### Service Architecture
The backend uses a modular service architecture with dependency injection:

```python
# Import services from domain modules
from app.services.user_management import get_user_service
from app.services.trading import get_trading_service
from app.services.market import get_market_service
from app.services.admin import get_admin_service
from app.services.core import get_public_service, get_cache_service
```

Key service modules:
- `user_management/`: User accounts, transfers, base service
- `trading/`: Stock trading execution
- `market/`: Market state management, IPO
- `matching/`: Order matching engine
- `admin/`: Administrative functions
- `core/`: Cache, public APIs, RBAC
- `system/`: Student management, debt service
- `infrastructure/`: Event bus, sharding, queues

### Common Issues
- **Manual market control**: Ensure `_is_market_open()` checks manual override first
- **Time zones**: Always specify `Asia/Taipei` for consistent display
- **Permissions**: Use RBAC system consistently between frontend and backend
- **Service dependencies**: Use dependency injection functions from `app.services` modules