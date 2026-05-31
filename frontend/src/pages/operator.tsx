import { useEffect, useState } from 'react';
import { type User, type Job } from '../types/types';

export const Operator = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const user: User = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    const fetchJobs = async () => {
      const res = await fetch('http://localhost:8000/api/jobs', {
        headers: { 'x-emp-id': user.id }
      });
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs);
      }
    };
    fetchJobs();
  }, [user.id]);

  return (
    <div className="p-4">
      <h2>維運監控儀表板</h2>
      <hr />
      <div className="alert alert-info">
        系統目前負載: 45% | Worker 節點: 3
        <button className="btn btn-sm btn-outline-dark float-end">擴充節點 (+)</button>
      </div>

      <h4>所有 Job 執行狀況</h4>
      <ul className="list-group mt-3">
        {jobs.map((job) => (
          <li
            key={job.job_id}
            className="list-group-item d-flex justify-content-between align-items-center"
          >
            <div>
              <strong>{job.job_id}</strong> - 路由: {job.details.endpoint} (建立者: {job.owner})
              <span className="badge bg-secondary ms-2">狀態: {job.status}</span>
            </div>
            <button className="btn btn-sm btn-warning">手動觸發</button>
          </li>
        ))}
      </ul>
    </div>
  );
};
