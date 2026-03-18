export type CursorPayload = {
  employeeId: string;
  createdAt: string;
};

export type PaginationRequest = {
  limit?: number;
  cursor?: string;
};

export type PaginationMetadata = {
  nextCursor: string | null;
  hasNext: boolean;
  limit: number;
};

export type PaginatedResult<T> = {
  data: T[];
  page: PaginationMetadata;
};

export type QueryExecutionOptions = {
  operation: string;
  expectedIndex?: string;
};

export type QueryExecutionRecord = {
  operation: string;
  expectedIndex?: string;
  durationMs: number;
  executedAt: string;
  slow: boolean;
};

export class ConnectionPool {
  private activeConnections = 0;

  constructor(private readonly maxConnections: number) {}

  runWithConnection<T>(work: () => T): T {
    if (this.activeConnections >= this.maxConnections) {
      throw new Error('DB_CONNECTION_POOL_EXHAUSTED');
    }

    this.activeConnections += 1;
    try {
      return work();
    } finally {
      this.activeConnections -= 1;
    }
  }

  snapshot(): { maxConnections: number; activeConnections: number } {
    return {
      maxConnections: this.maxConnections,
      activeConnections: this.activeConnections,
    };
  }
}

export class QueryOptimizer {
  private readonly history: QueryExecutionRecord[] = [];

  constructor(private readonly slowQueryThresholdMs = 25) {}

  execute<T>(options: QueryExecutionOptions, work: () => T): T {
    const startedAt = process.hrtime.bigint();
    const result = work();
    const durationMs = Number(process.hrtime.bigint() - startedAt) / 1_000_000;

    this.history.push({
      operation: options.operation,
      expectedIndex: options.expectedIndex,
      durationMs: Number(durationMs.toFixed(3)),
      executedAt: new Date().toISOString(),
      slow: durationMs >= this.slowQueryThresholdMs,
    });

    if (this.history.length > 100) {
      this.history.shift();
    }

    return result;
  }

  snapshot(): QueryExecutionRecord[] {
    return [...this.history];
  }
}

export function normalizeLimit(limit?: number): number {
  if (limit === undefined) {
    return 25;
  }

  if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw new Error('INVALID_PAGINATION_LIMIT');
  }

  return limit;
}

export function encodeCursor(payload: CursorPayload): string {
  return Buffer.from(JSON.stringify(payload), 'utf8').toString('base64url');
}

export function decodeCursor(cursor?: string): CursorPayload | undefined {
  if (!cursor) {
    return undefined;
  }

  try {
    const parsed = JSON.parse(Buffer.from(cursor, 'base64url').toString('utf8')) as CursorPayload;
    if (typeof parsed.employeeId !== 'string' || typeof parsed.createdAt !== 'string') {
      throw new Error('INVALID_CURSOR');
    }
    return parsed;
  } catch {
    throw new Error('INVALID_CURSOR');
  }
}

export function applyCursorPagination<T extends { employee_id: string; created_at: string }>(
  rows: T[],
  request: PaginationRequest,
): PaginatedResult<T> {
  const limit = normalizeLimit(request.limit);
  const cursor = decodeCursor(request.cursor);

  const sortedRows = [...rows].sort((left, right) => {
    if (left.created_at === right.created_at) {
      return left.employee_id.localeCompare(right.employee_id);
    }
    return left.created_at.localeCompare(right.created_at);
  });

  const matchedCursorIndex = cursor
    ? sortedRows.findIndex((row) => row.employee_id === cursor.employeeId && row.created_at === cursor.createdAt)
    : -1;

  if (cursor && matchedCursorIndex < 0) {
    throw new Error('INVALID_CURSOR');
  }

  const effectiveStartIndex = matchedCursorIndex >= 0 ? matchedCursorIndex + 1 : 0;
  const slice = sortedRows.slice(effectiveStartIndex, effectiveStartIndex + limit + 1);
  const hasNext = slice.length > limit;
  const data = hasNext ? slice.slice(0, limit) : slice;
  const last = data[data.length - 1];

  return {
    data,
    page: {
      nextCursor: hasNext && last ? encodeCursor({ employeeId: last.employee_id, createdAt: last.created_at }) : null,
      hasNext,
      limit,
    },
  };
}
