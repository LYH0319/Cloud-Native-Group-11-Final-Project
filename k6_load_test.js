import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 5 },
    { duration: '45s', target: 20 },
    { duration: '30s', target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  },
};

const API_BASE = __ENV.API_BASE || 'http://host.docker.internal:8000/api';
const JOB_TARGET = __ENV.JOB_TARGET || `${API_BASE}/health`;

function randomSuffix() {
  return Math.random().toString(36).substring(2, 8);
}

export function setup() {
  const suffix = randomSuffix();
  const registerPayload = {
    employee_id: `k6user-${suffix}`,
    username: `k6user-${suffix}`,
    password: 'Password123!',
  };

  const headers = { 'Content-Type': 'application/json' };
  const registerRes = http.post(
    `${API_BASE}/auth/register`,
    JSON.stringify(registerPayload),
    { headers }
  );

  check(registerRes, {
    'user registered or already exists': (r) => r.status === 201 || r.status === 409,
  });

  const loginRes = http.post(
    `${API_BASE}/auth/login`,
    JSON.stringify({ identifier: registerPayload.username, password: registerPayload.password }),
    { headers }
  );

  check(loginRes, {
    'login successful': (r) => r.status === 200,
  });

  const token = loginRes.json('access_token');
  const authHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const jobPayload = {
    job_name: `k6-health-check-${suffix}`,
    method: 'GET',
    endpoint: JOB_TARGET,
    schedule_type: 'One-time',
    has_dependency: false,
  };

  const createJobRes = http.post(
    `${API_BASE}/jobs`,
    JSON.stringify(jobPayload),
    { headers: authHeaders }
  );

  check(createJobRes, {
    'job created': (r) => r.status === 201,
  });

  const jobId = createJobRes.json('job_id');
  return { token, jobId };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };

  const triggerRes = http.post(`${API_BASE}/jobs/${data.jobId}/trigger`, null, {
    headers,
  });

  check(triggerRes, {
    'trigger accepted': (r) => r.status === 201,
  });

  sleep(1);
}
