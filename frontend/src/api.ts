import {
  type BackendUser,
  type JobCreatePayload,
  type BackendJob,
  type ExecutionHistoryResponse,
  type Role,
  type TokenResponse,
  type User
} from './types/types';

export const API_BASE_URL = '/api';

export const roleFromBackend = (role: string): Role => {
  const normalized = role.toLowerCase();
  if (normalized === 'admin') return 'admin';
  if (normalized === 'operator') return 'operator';
  return 'developer';
};

export const roleToBackend = (role: Role): 'Admin' | 'Developer' | 'Operator' => {
  if (role === 'admin') return 'Admin';
  if (role === 'operator') return 'Operator';
  return 'Developer';
};

export const toStoredUser = (tokenResponse: TokenResponse): User => {
  const backendUser: BackendUser = tokenResponse.user;
  return {
    id: backendUser.employee_id,
    userId: backendUser.user_id,
    username: backendUser.username,
    employeeId: backendUser.employee_id,
    role: roleFromBackend(backendUser.role),
    token: tokenResponse.access_token
  };
};

export const getStoredUser = (): User | null => {
  const raw = localStorage.getItem('user');
  if (!raw) return null;

  try {
    const user = JSON.parse(raw) as User;
    if (!user.token || !user.role) return null;
    return user;
  } catch {
    localStorage.removeItem('user');
    return null;
  }
};

export const storeUserFromTokenResponse = (tokenResponse: TokenResponse): User => {
  const user = toStoredUser(tokenResponse);
  localStorage.setItem('user', JSON.stringify(user));
  return user;
};

export const authHeaders = (): Record<string, string> => {
  const user = getStoredUser();
  return user?.token ? { Authorization: `Bearer ${user.token}` } : {};
};

export const apiFetch = async (path: string, init: RequestInit = {}) => {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json');
  }

  const auth = authHeaders();
  Object.entries(auth).forEach(([key, value]) => headers.set(key, value));

  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers
  });
};

export const createJob = (payload: JobCreatePayload) =>
  apiFetch('/jobs/', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

export const listJobs = async (): Promise<BackendJob[]> => {
  const response = await apiFetch('/jobs/');
  if (!response.ok) throw new Error('Unable to load jobs');
  return (await response.json()) as BackendJob[];
};

export const listJobExecutions = async (
  jobId: number,
  params = ''
): Promise<ExecutionHistoryResponse> => {
  const suffix = params ? `?${params}` : '';
  const response = await apiFetch(`/jobs/${jobId}/executions${suffix}`);
  if (!response.ok) throw new Error('Unable to load executions');
  return (await response.json()) as ExecutionHistoryResponse;
};

export const triggerJob = (jobId: number) => apiFetch(`/jobs/${jobId}/trigger`, { method: 'POST' });

export const updateJobStatus = (jobId: number, status: 'Active' | 'Disabled') =>
  apiFetch(`/jobs/${jobId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status })
  });

export const rerunExecution = (executionId: number) =>
  apiFetch(`/executions/${executionId}/rerun`, { method: 'POST' });

export const getExecutionLogContent = async (executionId: number) => {
  const response = await apiFetch(`/executions/${executionId}/logs/content`);
  if (!response.ok) throw new Error('No log content available');
  return response.text();
};
