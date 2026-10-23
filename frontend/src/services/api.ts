import { validationError } from '../i18n';

let accessToken: string | null = null;
let refreshing: Promise<any> | null = null;

export function setToken(token: string | null) { accessToken = token; }

async function request(url: string, options: RequestInit) {
  try { return await fetch(url, options); }
  catch (error) { throw new Error(error instanceof DOMException && error.name === 'TimeoutError' ? 'errors.timeout' : 'errors.network'); }
}

export async function refreshSession() {
  if (!refreshing) {
    refreshing = request('/api/auth/refresh', { method: 'POST', credentials: 'include', signal: AbortSignal.timeout(30000) })
      .then(async response => {
        if (!response.ok) throw new Error('errors.signIn');
        const data = await response.json();
        accessToken = data.access_token;
        return data;
      }).finally(() => { refreshing = null; });
  }
  return refreshing;
}

export async function api<T = any>(path: string, options: { method?: string; body?: unknown; timeoutMs?: number } = {}, retry = true): Promise<T> {
  const response = await request('/api' + path, {
    method: options.method || 'GET', credentials: 'include', signal: AbortSignal.timeout(options.timeoutMs ?? 30000),
    headers: { 'Content-Type': 'application/json', ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (response.status === 401 && retry && !path.startsWith('/auth/')) {
    try { await refreshSession(); } catch {
      accessToken = null;
      window.dispatchEvent(new Event('session-expired'));
      throw new Error('errors.sessionExpired');
    }
    return api<T>(path, options, false);
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = data.detail;
    throw new Error(Array.isArray(detail) ? validationError(detail) : typeof detail === 'string' ? detail : 'errors.request');
  }
  return response.status === 204 ? null as T : response.json();
}
