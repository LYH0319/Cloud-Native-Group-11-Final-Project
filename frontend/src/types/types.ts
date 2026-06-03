export type Role = 'developer' | 'operator' | 'admin';

export interface User {
  id: string;
  userId: number;
  username: string;
  employeeId: string;
  role: Role;
  token: string;
}

export interface BackendUser {
  user_id: number;
  employee_id: string;
  username: string;
  role: 'Admin' | 'Developer' | 'Operator' | string;
  email?: string | null;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: BackendUser;
}

export interface JobBody {
  [key: string]: unknown;
}

export interface JobCreatePayload {
  job_name: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  endpoint: string;
  schedule_type: 'One-time' | 'Recurring';
  headers?: Record<string, unknown>;
  body?: JobBody;
  cron_expression?: string;
  depends_on?: number[];
}

export interface BackendJob {
  job_id: number;
  owner_id: number;
  job_name: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  endpoint: string;
  schedule_type: 'One-time' | 'Recurring';
  has_dependency: boolean;
  headers?: Record<string, unknown> | null;
  body?: JobBody | null;
  cron_expression?: string | null;
  status: 'Active' | 'Disabled' | 'Deleted' | string;
  next_run_time?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExecutionRecord {
  execution_id: number;
  job_id: number;
  trigger_type: 'Scheduler' | 'Manual' | string;
  status: 'Pending' | 'Running' | 'Success' | 'Failed' | 'Timeout' | 'Cancelled' | string;
  start_time?: string | null;
  end_time?: string | null;
  duration?: number | null;
  worker_id?: string | null;
  retry_count: number;
  error_message?: string | null;
  created_at: string;
}

export interface ExecutionHistoryResponse {
  items: ExecutionRecord[];
  skip: number;
  limit: number;
  count: number;
}

export interface LogReference {
  log_id: number;
  execution_id: number;
  log_path: string;
  log_size: number;
  created_at: string;
}
