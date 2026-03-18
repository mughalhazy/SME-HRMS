import { Request, RequestHandler, Response } from 'express';
import { getTraceId } from './error-handler';

type QueueEntry = {
  released: boolean;
  activate: () => void;
  timer?: NodeJS.Timeout;
};

export type ThrottleOptions = {
  maxConcurrent: number;
  maxQueue: number;
  queueTimeoutMs?: number;
  keyGenerator?: (req: Request) => string;
};

type ThrottleState = {
  active: number;
  queue: QueueEntry[];
};

const states = new Map<string, ThrottleState>();

function getState(key: string): ThrottleState {
  const existing = states.get(key);
  if (existing) {
    return existing;
  }

  const created: ThrottleState = { active: 0, queue: [] };
  states.set(key, created);
  return created;
}

function getThrottleKey(req: Request, keyGenerator?: (req: Request) => string): string {
  return keyGenerator?.(req) ?? `${req.method}:${req.baseUrl || ''}${req.route?.path ?? req.path}`;
}

function sendThrottleError(req: Request, res: Response, reason: string): void {
  res.status(429).json({
    error: {
      code: 'REQUEST_THROTTLED',
      message: 'Request concurrency limit exceeded.',
      details: [{ field: 'request', reason }],
      traceId: getTraceId(req),
    },
  });
}

export function createThrottleMiddleware(options: ThrottleOptions): RequestHandler {
  const queueTimeoutMs = options.queueTimeoutMs ?? 250;

  return (req, res, next): void => {
    const key = getThrottleKey(req, options.keyGenerator);
    const state = getState(key);

    const release = (): void => {
      res.off('finish', release);
      res.off('close', release);
      if (state.active > 0) {
        state.active -= 1;
      }

      while (state.queue.length > 0) {
        const queued = state.queue.shift();
        if (!queued || queued.released) {
          continue;
        }

        queued.released = true;
        if (queued.timer) {
          clearTimeout(queued.timer);
        }
        state.active += 1;
        queued.activate();
        return;
      }

      if (state.active === 0 && state.queue.length === 0) {
        states.delete(key);
      }
    };

    const start = (): void => {
      res.on('finish', release);
      res.on('close', release);
      next();
    };

    if (state.active < options.maxConcurrent) {
      state.active += 1;
      start();
      return;
    }

    if (state.queue.length >= options.maxQueue) {
      sendThrottleError(req, res, 'queue capacity exhausted');
      return;
    }

    const queueEntry: QueueEntry = {
      released: false,
      activate: start,
    };

    queueEntry.timer = setTimeout(() => {
      if (queueEntry.released) {
        return;
      }
      queueEntry.released = true;
      const index = state.queue.indexOf(queueEntry);
      if (index >= 0) {
        state.queue.splice(index, 1);
      }
      if (state.active === 0 && state.queue.length === 0) {
        states.delete(key);
      }
      sendThrottleError(req, res, `request timed out in queue after ${queueTimeoutMs}ms`);
    }, queueTimeoutMs);

    state.queue.push(queueEntry);
  };
}
