import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const DEFAULT_DB_PATH = resolve(process.cwd(), '.data/hrms-repository.sqlite');

function getDatabase(dbPath?: string): DatabaseSync {
  const filename = resolve(dbPath ?? process.env.HRMS_SQLITE_PATH ?? DEFAULT_DB_PATH);
  mkdirSync(dirname(filename), { recursive: true });
  const db = new DatabaseSync(filename);
  db.exec(`
    CREATE TABLE IF NOT EXISTS repository_store (
      namespace TEXT NOT NULL,
      entry_key TEXT NOT NULL,
      entry_value TEXT NOT NULL,
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(namespace, entry_key)
    );
  `);
  return db;
}

export class PersistentMap<V> {
  private readonly db: DatabaseSync;

  constructor(private readonly namespace: string, dbPath?: string) {
    this.db = getDatabase(dbPath);
  }

  set(key: string, value: V): this {
    this.db.prepare(`
      INSERT INTO repository_store(namespace, entry_key, entry_value)
      VALUES (?, ?, ?)
      ON CONFLICT(namespace, entry_key)
      DO UPDATE SET entry_value = excluded.entry_value, updated_at = CURRENT_TIMESTAMP
    `).run(this.namespace, key, JSON.stringify(value));
    return this;
  }

  get(key: string): V | undefined {
    const row = this.db.prepare(
      'SELECT entry_value FROM repository_store WHERE namespace = ? AND entry_key = ?',
    ).get(this.namespace, key) as { entry_value: string } | undefined;
    return row ? JSON.parse(row.entry_value) as V : undefined;
  }

  has(key: string): boolean {
    const row = this.db.prepare(
      'SELECT 1 FROM repository_store WHERE namespace = ? AND entry_key = ? LIMIT 1',
    ).get(this.namespace, key);
    return Boolean(row);
  }

  delete(key: string): boolean {
    const result = this.db.prepare('DELETE FROM repository_store WHERE namespace = ? AND entry_key = ?').run(this.namespace, key);
    return result.changes > 0;
  }

  keys(): string[] {
    const rows = this.db.prepare('SELECT entry_key FROM repository_store WHERE namespace = ? ORDER BY entry_key').all(this.namespace) as Array<{ entry_key: string }>;
    return rows.map((row) => row.entry_key);
  }

  values(): V[] {
    const rows = this.db.prepare('SELECT entry_value FROM repository_store WHERE namespace = ? ORDER BY entry_key').all(this.namespace) as Array<{ entry_value: string }>;
    return rows.map((row) => JSON.parse(row.entry_value) as V);
  }
}
