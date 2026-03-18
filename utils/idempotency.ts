export type IdempotentResponse<T> = {
  fingerprint: string;
  payload: T;
  status: number;
};

export class IdempotencyConflictError extends Error {
  constructor(message = 'Idempotency key was reused with a different request payload.') {
    super(message);
    this.name = 'IdempotencyConflictError';
  }
}

export class IdempotencyStore<T> {
  private readonly entries = new Map<string, IdempotentResponse<T>>();

  get(key: string): IdempotentResponse<T> | undefined {
    return this.entries.get(key);
  }

  replayOrConflict(key: string, fingerprint: string): IdempotentResponse<T> | undefined {
    const existing = this.entries.get(key);
    if (existing && existing.fingerprint !== fingerprint) {
      throw new IdempotencyConflictError();
    }
    return existing;
  }

  record(key: string, fingerprint: string, status: number, payload: T): IdempotentResponse<T> {
    const entry = { fingerprint, status, payload };
    this.entries.set(key, entry);
    return entry;
  }
}
