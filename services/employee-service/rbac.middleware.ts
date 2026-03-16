import { randomUUID } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';

export type AuthRole = 'Admin' | 'Manager' | 'Employee';

export type AuthContext = {
  role: AuthRole;
  employee_id?: string;
  department_id?: string;
};

type EmployeeAction =
  | 'create'
  | 'read'
  | 'list'
  | 'updateProfile'
  | 'manageDepartment'
  | 'manageStatus'
  | 'delete';

const ROLE_ACTIONS: Record<AuthRole, EmployeeAction[]> = {
  Admin: ['create', 'read', 'list', 'updateProfile', 'manageDepartment', 'manageStatus', 'delete'],
  Manager: ['create', 'read', 'list', 'updateProfile', 'manageDepartment', 'manageStatus'],
  Employee: ['read', 'list', 'updateProfile'],
};

function getTraceId(req: Request): string {
  const incomingTraceId = req.headers['x-trace-id'];
  if (typeof incomingTraceId === 'string' && incomingTraceId.length > 0) {
    return incomingTraceId;
  }
  return randomUUID().replace(/-/g, '').slice(0, 16);
}

function sendError(req: Request, res: Response, status: number, code: string, message: string): void {
  res.status(status).json({
    error: {
      code,
      message,
      traceId: getTraceId(req),
    },
  });
}

function parseAuth(req: Request): AuthContext {
  const authorization = req.headers.authorization;
  if (!authorization || !authorization.startsWith('Bearer ')) {
    throw new Error('UNAUTHORIZED');
  }

  let payload: unknown;
  try {
    payload = JSON.parse(Buffer.from(authorization.slice(7), 'base64url').toString('utf8'));
  } catch {
    throw new Error('UNAUTHORIZED');
  }

  if (!payload || typeof payload !== 'object' || !('role' in payload)) {
    throw new Error('UNAUTHORIZED');
  }

  const { role, employee_id, department_id } = payload as Record<string, unknown>;
  if (role !== 'Admin' && role !== 'Manager' && role !== 'Employee') {
    throw new Error('UNAUTHORIZED');
  }

  return {
    role,
    employee_id: typeof employee_id === 'string' ? employee_id : undefined,
    department_id: typeof department_id === 'string' ? department_id : undefined,
  };
}

function isScopedToSelf(req: Request, auth: AuthContext): boolean {
  const targetEmployeeId = req.params.employeeId;
  return Boolean(targetEmployeeId && auth.employee_id === targetEmployeeId);
}

export const authenticate: RequestHandler = (req: Request, res: Response, next: NextFunction): void => {
  try {
    req.auth = parseAuth(req);
    next();
  } catch {
    sendError(req, res, 401, 'UNAUTHORIZED', 'Missing or invalid bearer token');
  }
};

export function authorizeEmployeeAction(action: EmployeeAction): RequestHandler {
  return (req: Request, res: Response, next: NextFunction): void => {
    const auth = req.auth;
    if (!auth) {
      sendError(req, res, 401, 'UNAUTHORIZED', 'Missing or invalid bearer token');
      return;
    }

    const allowedActions = ROLE_ACTIONS[auth.role] ?? [];
    if (!allowedActions.includes(action)) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
      return;
    }

    if (auth.role === 'Employee' && (action === 'read' || action === 'updateProfile') && !isScopedToSelf(req, auth)) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
      return;
    }

    next();
  };
}

declare global {
  namespace Express {
    interface Request {
      auth?: AuthContext;
    }
  }
}
