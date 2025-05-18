# Point Giving System

A comprehensive point management system built with Next.js, FastAPI, MongoDB, and Telegram Bot integration.

## Features

- View points list
- Admin interface for point management
- Telegram bot for point checking
- MongoDB database for data persistence

## Project Structure

```
.
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend application
└── telegram-bot/      # Telegram bot integration
```

## Prerequisites

- Node.js (v18 or later)
- Python (v3.8 or later)
- MongoDB
- Telegram Bot Token

## Setup Instructions

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with:
   ```
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=points_db
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```

5. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

### Telegram Bot Setup

1. Create a new bot with BotFather on Telegram
2. Get the bot token and add it to the backend `.env` file
3. The bot will automatically start when running the backend server

## Usage

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## License

MIT