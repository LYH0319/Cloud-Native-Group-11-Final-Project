import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Styles from './Style';
import { createJob } from '../api';
import { type JobCreatePayload } from '../types/types';

type ScheduleType = JobCreatePayload['schedule_type'];

export const DeveloperAddShellScript = () => {
  const [jobName, setJobName] = useState('Shell Script Job');
  const [command, setCommand] = useState('echo hello');
  const [scheduleType, setScheduleType] = useState<ScheduleType>('One-time');
  const [cronExpression, setCronExpression] = useState('*/5 * * * *');
  const [timeoutSeconds, setTimeoutSeconds] = useState(60);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const payload: JobCreatePayload = {
        job_name: jobName,
        method: 'POST',
        endpoint: 'shell://local',
        schedule_type: scheduleType,
        headers: { task_type: 'shell' },
        body: {
          command,
          timeout_seconds: timeoutSeconds
        }
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
      alert(err instanceof Error ? err.message : '連線失敗');
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
        <h4>新增 Shell Script 任務</h4>
        <input
          type="text"
          className="form-control mb-2"
          placeholder="Job name"
          value={jobName}
          onChange={(e) => setJobName(e.target.value)}
        />
        <textarea
          className="form-control mb-2"
          rows={5}
          placeholder="Shell command"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
        />
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
          <div className="col-md-5">
            <input
              type="text"
              className="form-control mb-2"
              placeholder="Cron expression"
              value={cronExpression}
              disabled={scheduleType !== 'Recurring'}
              onChange={(e) => setCronExpression(e.target.value)}
            />
          </div>
          <div className="col-md-3">
            <input
              type="number"
              className="form-control mb-2"
              min={1}
              value={timeoutSeconds}
              onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
            />
          </div>
        </div>
        <button onClick={handleSubmit} className="btn btn-success" disabled={loading}>
          {loading ? '建立中...' : '註冊 Shell Script Job'}
        </button>
      </div>
    </div>
  );
};
