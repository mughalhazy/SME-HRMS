import { createHmac, timingSafeEqual } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';
import { getRequestId } from '../../middleware/request-id';
import { normalizeTenantId } from '../../middleware/tenant-context';

export type AuthRole = 'Admin' | 'Manager' | 'Employee' | 'PayrollAdmin' | 'Recruiter' | 'Service';

export type AuthContext = {
  role: AuthRole;
  employee_id?: string;
  department_id?: string;
  tenant_id?: string;
  capabilities: string[];
  scopes: string[];
  subject_type: 'user' | 'service';
};

type ResourceAction =
  | 'create'
  | 'read'
  | 'list'
  | 'updateProfile'
  | 'manageDepartment'
  | 'manageStatus'
  | 'delete'
  | 'createRole'
  | 'readRole'
  | 'listRoles'
  | 'updateRole'
  | 'deleteRole'
  | 'createReview'
  | 'readReview'
  | 'listReviews'
  | 'updateReview'
  | 'submitReview'
  | 'finalizeReview'
  | 'readOrgStructure'
  | 'listOrgStructure'
  | 'manageOrgStructure';

const ROLE_ACTIONS: Record<AuthRole, ResourceAction[]> = {
  Admin: ['create', 'read', 'list', 'updateProfile', 'manageDepartment', 'manageStatus', 'delete', 'createRole', 'readRole', 'listRoles', 'updateRole', 'deleteRole', 'createReview', 'readReview', 'listReviews', 'updateReview', 'submitReview', 'finalizeReview', 'readOrgStructure', 'listOrgStructure', 'manageOrgStructure'],
  Manager: ['create', 'read', 'list', 'updateProfile', 'manageDepartment', 'manageStatus', 'readRole', 'listRoles', 'createReview', 'readReview', 'listReviews', 'updateReview', 'submitReview', 'finalizeReview', 'readOrgStructure', 'listOrgStructure', 'manageOrgStructure'],
  Employee: ['read', 'list', 'updateProfile', 'readReview', 'listReviews', 'readOrgStructure', 'listOrgStructure'],
  PayrollAdmin: ['read', 'list', 'readRole', 'listRoles', 'readOrgStructure', 'listOrgStructure'],
  Recruiter: [],
  Service: ['create', 'read', 'list', 'updateProfile', 'manageDepartment', 'manageStatus', 'createRole', 'readRole', 'listRoles', 'updateRole', 'deleteRole', 'createReview', 'readReview', 'listReviews', 'updateReview', 'submitReview', 'finalizeReview', 'readOrgStructure', 'listOrgStructure', 'manageOrgStructure'],
};

const ACTION_CAPABILITIES: Record<ResourceAction, string> = {
  create: 'CAP-EMP-001',
  read: 'CAP-EMP-001',
  list: 'CAP-EMP-001',
  updateProfile: 'CAP-EMP-002',
  manageDepartment: 'CAP-EMP-002',
  manageStatus: 'CAP-EMP-002',
  delete: 'CAP-EMP-001',
  createRole: 'CAP-EMP-002',
  readRole: 'CAP-EMP-001',
  listRoles: 'CAP-EMP-001',
  updateRole: 'CAP-EMP-002',
  deleteRole: 'CAP-EMP-002',
  createReview: 'CAP-PRF-001',
  readReview: 'CAP-PRF-001',
  listReviews: 'CAP-PRF-001',
  updateReview: 'CAP-PRF-001',
  submitReview: 'CAP-PRF-001',
  finalizeReview: 'CAP-PRF-001',
  readOrgStructure: 'CAP-EMP-001',
  listOrgStructure: 'CAP-EMP-001',
  manageOrgStructure: 'CAP-EMP-002',
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

  const { role, employee_id, department_id, tenant_id, iss, aud, nbf, exp, capabilities, scopes, subject_type } = payload as Record<string, unknown>;
  if (role !== 'Admin' && role !== 'Manager' && role !== 'Employee' && role !== 'PayrollAdmin' && role !== 'Recruiter' && role !== 'Service') {
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
    tenant_id: normalizeTenantId(typeof tenant_id === 'string' ? tenant_id : undefined),
    capabilities: Array.isArray(capabilities) ? capabilities.filter((item): item is string => typeof item === 'string') : [],
    scopes: Array.isArray(scopes) ? scopes.filter((item): item is string => typeof item === 'string') : [],
    subject_type: subject_type === 'service' ? 'service' : 'user',
  };
}

function isScopedToSelf(req: Request, auth: AuthContext): boolean {
  const targetEmployeeId = req.params.employeeId;
  return Boolean(targetEmployeeId && auth.employee_id === targetEmployeeId);
}

function ensureTenantConsistency(req: Request, auth: AuthContext): void {
  const requestedTenant = normalizeTenantId(
    typeof req.headers['x-tenant-id'] === 'string'
      ? req.headers['x-tenant-id']
      : typeof req.headers['x-tenant'] === 'string'
        ? req.headers['x-tenant']
        : req.tenantId,
  );

  if (requestedTenant !== auth.tenant_id) {
    throw new Error('TENANT_SCOPE_VIOLATION');
  }

  req.tenantId = auth.tenant_id;
  req.headers['x-tenant-id'] = auth.tenant_id;
}

function hasRequiredCapability(auth: AuthContext, action: ResourceAction): boolean {
  if (auth.role === 'Admin') {
    return true;
  }

  const requiredCapability = ACTION_CAPABILITIES[action];
  return auth.capabilities.includes(requiredCapability);
}

function hasServiceScope(auth: AuthContext): boolean {
  return auth.role !== 'Service' || auth.scopes.includes('resource:employee-service') || auth.scopes.includes('service:internal');
}

export const authenticate: RequestHandler = (req: Request, res: Response, next: NextFunction): void => {
  try {
    req.auth = parseAuth(req);
    ensureTenantConsistency(req, req.auth);
    next();
  } catch (error) {
    if (error instanceof Error && error.message === 'TENANT_SCOPE_VIOLATION') {
      sendError(req, res, 403, 'FORBIDDEN', 'Tenant scope mismatch');
      return;
    }
    sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
  }
};

export function authorizeEmployeeAction(action: ResourceAction): RequestHandler {
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

    if (!hasRequiredCapability(auth, action) || !hasServiceScope(auth)) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
      return;
    }

    if (auth.role === 'Employee' && (action === 'read' || action === 'updateProfile') && !isScopedToSelf(req, auth)) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
      return;
    }

    if (auth.role === 'PayrollAdmin' && action !== 'read' && action !== 'list' && action !== 'readRole' && action !== 'listRoles' && action !== 'readOrgStructure' && action !== 'listOrgStructure') {
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
