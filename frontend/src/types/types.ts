export type Role = 'developer' | 'operator' | 'admin';

export interface User {
  id: string;
  role: Role;
  token?: string;
}

// export interface JobPayload {
//     method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
//     endpoint: string;
//     headers: string;
//     body: string;
// }

export interface JobBody {
  command: string;
  schedule: string;
  retry_policy: number;
  dependencies: string[];
  timeout_seconds: number;
}

export interface JobCreate {
  method: string;
  endpoint: string;
  headers: Record<string, string>;
  body: JobBody;
}

export interface Job {
  job_id: string;
  owner: string;
  details: JobCreate;
  status: 'pending' | 'running' | 'success' | 'failed';
}
