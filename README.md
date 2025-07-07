# camp2025-stock

To install dependencies:

```bash
bun install
```

To run:

```bash
bun run index.ts
```

This project was created using `bun init` in bun v1.2.18. [Bun](https://bun.sh) is a fast all-in-one JavaScript runtime.

# MongoDB Backup Script

A TypeScript-based MongoDB backup utility that automatically creates backups every 6 hours using node-cron.

## Features

- ✅ Automated backups every 6 hours
- ✅ ISO timestamp naming format
- ✅ Compressed backup files (.tar.gz)
- ✅ Environment variable configuration
- ✅ Graceful error handling and logging
- ✅ Initial backup on startup

## Prerequisites

- MongoDB tools (`mongodump`) must be installed on the system
- Node.js or Bun runtime
- Access to MongoDB instance

## Installation

1. Install dependencies:
   ```bash
   bun install
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Configure your MongoDB connection in `.env`:
   ```
   MONGODB_URI=mongodb://username:password@localhost:27017/database-name
   ```

## Usage

Start the backup service:
```bash
bun run index.ts
```

The script will:
- Create the `/backup` directory if it doesn't exist
- Perform an initial backup immediately
- Schedule automatic backups every 6 hours
- Name backups with ISO timestamps (e.g., `mongodb-backup-2025-07-07T12-00-00-000Z.tar.gz`)

## Backup Schedule

Backups run automatically at:
- 00:00 (midnight)
- 06:00 (6 AM)
- 12:00 (noon)
- 18:00 (6 PM)

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/mydb` |

## Backup Location

All backups are stored in `/backup/` and compressed as `.tar.gz` files.

## Monitoring

The script provides detailed logging including:
- Backup start/completion times
- File paths and sizes
- Error messages if backups fail
- Cron schedule confirmations
