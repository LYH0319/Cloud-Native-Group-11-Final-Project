import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Styles from './Style';
import { createJob } from '../api';
import { type JobBody, type JobCreatePayload } from '../types/types';

type HttpMethod = JobCreatePayload['method'];
type ScheduleType = JobCreatePayload['schedule_type'];

export const DeveloperAddRESTfulAPI = () => {
  const [jobName, setJobName] = useState('REST API Job');
  const [method, setMethod] = useState<HttpMethod>('GET');
  const [endpoint, setEndpoint] = useState('http://backend:8000/api/health');
  const [scheduleType, setScheduleType] = useState<ScheduleType>('One-time');
  const [cronExpression, setCronExpression] = useState('*/5 * * * *');
  const [headersJson, setHeadersJson] = useState('{}');
  const [bodyJson, setBodyJson] = useState('{}');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const headers = JSON.parse(headersJson || '{}') as Record<string, unknown>;
      const body = JSON.parse(bodyJson || '{}') as JobBody;
      const payload: JobCreatePayload = {
        job_name: jobName,
        method,
        endpoint,
        schedule_type: scheduleType,
        headers,
        body
      };

      if (scheduleType === 'Recurring') {
        payload.cron_expression = cronExpression;
      }

      const res = await createJob(payload);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || '建立失敗');
      }
      alert(data.message || '建立成功');
      navigate('/developer');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'JSON 格式錯誤或連線失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-light min-vh-100">
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>
        <div className="d-flex flex-column align-items-end">
          <div className="d-flex gap-2">
            <button
              className="btn btn-light btn-sm px-3 mb-2"
              onClick={() => navigate('/developer')}
              style={Styles.homeLoginLogoutStyles.style}
            >
              上一頁
            </button>
            <button
              className="btn btn-light btn-sm px-3 mb-2"
              onClick={() => navigate('/')}
              style={Styles.homeLoginLogoutStyles.style}
            >
              回首頁
            </button>
          </div>
          <h2 className="fs-5 m-0 font-weight-bold">內部開發者專區</h2>
        </div>
      </div>

      <div className="container mt-4" style={{ maxWidth: '760px' }}>
        <h4>新增 RESTful API 任務</h4>
        <input
          type="text"
          className="form-control mb-2"
          placeholder="Job name"
          value={jobName}
          onChange={(e) => setJobName(e.target.value)}
        />
        <div className="row">
          <div className="col-md-4">
            <select
              className="form-select mb-2"
              value={method}
              onChange={(e) => setMethod(e.target.value as HttpMethod)}
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
          <div className="col-md-8">
            <input
              type="text"
              className="form-control mb-2"
              placeholder="Endpoint URL"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
            />
          </div>
        </div>
        <div className="row">
          <div className="col-md-4">
            <select
              className="form-select mb-2"
              value={scheduleType}
              onChange={(e) => setScheduleType(e.target.value as ScheduleType)}
            >
              <option value="One-time">One-time</option>
              <option value="Recurring">Recurring</option>
            </select>
          </div>
          <div className="col-md-8">
            <input
              type="text"
              className="form-control mb-2"
              placeholder="Cron expression"
              value={cronExpression}
              disabled={scheduleType !== 'Recurring'}
              onChange={(e) => setCronExpression(e.target.value)}
            />
          </div>
        </div>
        <label htmlFor="headers-json" className="form-label">
          Headers JSON
        </label>
        <textarea
          className="form-control mb-2"
          rows={4}
          value={headersJson}
          onChange={(e) => setHeadersJson(e.target.value)}
        />
        <label htmlFor="body-json" className="form-label">
          Body JSON
        </label>
        <textarea
          className="form-control mb-3"
          rows={6}
          value={bodyJson}
          onChange={(e) => setBodyJson(e.target.value)}
        />
        <button onClick={handleSubmit} className="btn btn-success" disabled={loading}>
          {loading ? '建立中...' : '註冊 REST API Job'}
        </button>
      </div>
    </div>
  );
};
