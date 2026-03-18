import { createHmac, timingSafeEqual } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';
import { getRequestId } from '../../middleware/request-id';

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

const TOKEN_SECRET = process.env.AUTH_TOKEN_SECRET;
const TOKEN_ISSUER = process.env.AUTH_TOKEN_ISSUER ?? 'sme-hrms.auth-service';
const TOKEN_AUDIENCE = process.env.AUTH_TOKEN_AUDIENCE ?? 'sme-hrms.api';

if (!TOKEN_SECRET || TOKEN_SECRET.length < 32) {
  throw new Error('AUTH_TOKEN_SECRET must be configured with at least 32 characters');
}

function getTraceId(req: Request): string {
  return req.traceId ?? getRequestId(req);
}

function sendError(req: Request, res: Response, status: number, code: string, message: string): void {
  res.status(status).json({
    error: {
      code,
      message,
      details: [],
      traceId: getTraceId(req),
    },
  });
}

function decodeSegment(segment: string): string {
  return Buffer.from(segment, 'base64url').toString('utf8');
}

function validateSignature(headerSegment: string, payloadSegment: string, signatureSegment: string): boolean {
  const signingInput = `${headerSegment}.${payloadSegment}`;
  const expectedSignature = createHmac('sha256', TOKEN_SECRET).update(signingInput).digest();
  const actualSignature = Buffer.from(signatureSegment, 'base64url');

  if (actualSignature.length !== expectedSignature.length) {
    return false;
  }

  return timingSafeEqual(actualSignature, expectedSignature);
}

function parseAuth(req: Request): AuthContext {
  const authorization = req.headers.authorization;
  if (!authorization || !authorization.startsWith('Bearer ')) {
    throw new Error('UNAUTHORIZED');
  }

  const token = authorization.slice(7);
  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('UNAUTHORIZED');
  }

  const [headerSegment, payloadSegment, signatureSegment] = parts;
  if (!validateSignature(headerSegment, payloadSegment, signatureSegment)) {
    throw new Error('UNAUTHORIZED');
  }

  let payload: unknown;
  try {
    const header = JSON.parse(decodeSegment(headerSegment)) as { alg?: string; typ?: string };
    if (header.alg !== 'HS256' || header.typ !== 'JWT') {
      throw new Error('UNAUTHORIZED');
    }
    payload = JSON.parse(decodeSegment(payloadSegment));
  } catch {
    throw new Error('UNAUTHORIZED');
  }

  if (!payload || typeof payload !== 'object' || !('role' in payload)) {
    throw new Error('UNAUTHORIZED');
  }

  const { role, employee_id, department_id, iss, aud, nbf, exp } = payload as Record<string, unknown>;
  if (role !== 'Admin' && role !== 'Manager' && role !== 'Employee') {
    throw new Error('UNAUTHORIZED');
  }

  if (iss !== TOKEN_ISSUER || aud !== TOKEN_AUDIENCE) {
    throw new Error('UNAUTHORIZED');
  }

  const now = Math.floor(Date.now() / 1000);
  if (typeof nbf !== 'number' || typeof exp !== 'number' || now < nbf || now >= exp) {
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
    sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
  }
};

export function authorizeEmployeeAction(action: EmployeeAction): RequestHandler {
  return (req: Request, res: Response, next: NextFunction): void => {
    const auth = req.auth;
    if (!auth) {
      sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
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
