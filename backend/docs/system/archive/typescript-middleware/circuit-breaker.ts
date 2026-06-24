export class CircuitBreakerOpenError extends Error {
  constructor(message = 'Circuit breaker is open.') {
    super(message);
    this.name = 'CircuitBreakerOpenError';
  }
}

export type CircuitBreakerOptions = {
  failureThreshold?: number;
  recoveryTimeoutMs?: number;
};

export class CircuitBreaker {
  private failureCount = 0;
  private openedAt: number | null = null;

  constructor(private readonly options: CircuitBreakerOptions = {}) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.openedAt !== null) {
      const elapsed = Date.now() - this.openedAt;
      if (elapsed < (this.options.recoveryTimeoutMs ?? 5_000)) {
        throw new CircuitBreakerOpenError();
      }
      this.openedAt = null;
      this.failureCount = 0;
    }

    try {
      const result = await operation();
      this.failureCount = 0;
      this.openedAt = null;
      return result;
    } catch (error) {
      this.failureCount += 1;
      if (this.failureCount >= (this.options.failureThreshold ?? 3)) {
        this.openedAt = Date.now();
      }
      throw error;
    }
  }
}
