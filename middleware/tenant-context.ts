import { NextFunction, Request, RequestHandler, Response } from 'express';

export const DEFAULT_TENANT_ID = 'tenant-default';

export function normalizeTenantId(value?: string | null): string {
  const tenantId = value?.trim();
  return tenantId && tenantId.length > 0 ? tenantId : DEFAULT_TENANT_ID;
}

export function resolveTenantId(req: Request): string {
  const headerTenantId = typeof req.headers['x-tenant-id'] === 'string'
    ? req.headers['x-tenant-id']
    : typeof req.headers['x-tenant'] === 'string'
      ? req.headers['x-tenant']
      : undefined;
  const authTenantId = req.auth?.tenant_id;
  const bodyTenantId = req.body && typeof req.body === 'object' && typeof req.body.tenant_id === 'string'
    ? req.body.tenant_id
    : undefined;
  return normalizeTenantId(headerTenantId ?? authTenantId ?? bodyTenantId);
}

export const tenantContextMiddleware: RequestHandler = (req: Request, res: Response, next: NextFunction): void => {
  const tenantId = resolveTenantId(req);
  req.tenantId = tenantId;
  req.headers['x-tenant-id'] = tenantId;
  res.setHeader('X-Tenant-Id', tenantId);
  next();
};

export function assertTenantMatch(req: Request, tenantId?: string | null): void {
  const expected = normalizeTenantId(req.tenantId);
  const actual = normalizeTenantId(tenantId);
  if (expected !== actual) {
    const error = new Error('TENANT_SCOPE_VIOLATION');
    error.name = 'TenantScopeError';
    throw error;
  }
}

declare global {
  namespace Express {
    interface Request {
      tenantId?: string;
    }
  }
}
