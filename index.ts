import cron from 'node-cron';
import { config } from 'dotenv';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import path from 'path';

config();

const execAsync = promisify(exec);
const BACKUP_DIR = './backup';
const MONGO_URI = process.env.MONGODB_URI;

if (!MONGO_URI) {
  console.error('MONGODB_URI environment variable is required');
  process.exit(1);
}

async function backup() {
  try {
    console.log('Starting MongoDB backup...');

    // Ensure backup directory exists
    await fs.promises.mkdir(BACKUP_DIR, { recursive: true });

    // Generate backup filename with ISO timestamp
    const isoString = new Date().toISOString().replace(/[:.]/g, '-');
    const backupName = `mongodb-backup-${isoString}`;
    const backupPath = path.join(BACKUP_DIR, backupName);

    // Create backup using mongodump
    console.log(`Executing backup to: ${backupPath}`);
    const { stdout, stderr } = await execAsync(`mongodump --uri="${MONGO_URI}" --out="${backupPath}"`);

    if (stderr && !stderr.includes('writing')) {
      console.error('Backup stderr:', stderr);
    }
    if (stdout) console.log('Backup stdout:', stdout);

    // Compress and cleanup
    await execAsync(`tar -czf "${backupPath}.tar.gz" -C "${BACKUP_DIR}" "${backupName}"`);
    await fs.promises.rm(backupPath, { recursive: true, force: true });

    console.log(`Backup completed: ${backupPath}.tar.gz`);

  } catch (error) {
    console.error('Backup failed:', error);
    throw error;
  }
}

cron.schedule('0 */6 * * *', () => {
  console.log('Scheduled backup triggered');
  backup().catch(error => console.error('Scheduled backup failed:', error));
});

console.log('Backup system initialized');

console.log('Performing initial backup...');
backup().catch(error => {
  console.error('Initial backup failed:', error);
  process.exit(1);
});
