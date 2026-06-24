export type CacheEntry<T> = {
  value: T;
  expiresAt: number;
  createdAt: number;
};

export type CacheOptions = {
  ttlMs: number;
  maxEntries?: number;
};

function cloneValue<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export class CacheService {
  private readonly store = new Map<string, CacheEntry<unknown>>();
  private readonly maxEntries: number;

  constructor(private readonly defaultOptions: CacheOptions) {
    this.maxEntries = defaultOptions.maxEntries ?? 500;
  }

  get<T>(key: string): T | undefined {
    const entry = this.store.get(key);
    if (!entry) {
      return undefined;
    }

    if (entry.expiresAt <= Date.now()) {
      this.store.delete(key);
      return undefined;
    }

    return cloneValue(entry.value as T);
  }

  set<T>(key: string, value: T, options?: Partial<CacheOptions>): T {
    this.pruneExpired();
    if (this.store.size >= this.maxEntries) {
      const oldestKey = this.store.keys().next().value;
      if (oldestKey) {
        this.store.delete(oldestKey);
      }
    }

    const ttlMs = options?.ttlMs ?? this.defaultOptions.ttlMs;
    const now = Date.now();
    this.store.set(key, {
      value: cloneValue(value),
      createdAt: now,
      expiresAt: now + ttlMs,
    });

    return cloneValue(value);
  }

  invalidate(key: string): void {
    this.store.delete(key);
  }

  invalidateByPrefix(prefix: string): void {
    for (const key of this.store.keys()) {
      if (key.startsWith(prefix)) {
        this.store.delete(key);
      }
    }
  }

  pruneExpired(): void {
    const now = Date.now();
    for (const [key, entry] of this.store.entries()) {
      if (entry.expiresAt <= now) {
        this.store.delete(key);
      }
    }
  }

  snapshot(): { size: number; keys: string[] } {
    this.pruneExpired();
    return {
      size: this.store.size,
      keys: [...this.store.keys()].sort(),
    };
  }
}
