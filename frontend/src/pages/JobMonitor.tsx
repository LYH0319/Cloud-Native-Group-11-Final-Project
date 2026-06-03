import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  getExecutionLogContent,
  getStoredUser,
  listJobExecutions,
  listJobs,
  rerunExecution,
  triggerJob,
  updateJobStatus
} from '../api';
import { type BackendJob, type ExecutionRecord } from '../types/types';
import { operatorStyles } from './Style';

type Scope = 'developer' | 'operator';

interface JobMonitorProps {
  scope: Scope;
}

const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

const parseBackendDate = (value: string) => {
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
};

const formatDate = (value?: string | null) => {
  if (!value) return '-';
  const date = parseBackendDate(value);
  if (Number.isNaN(date.getTime())) return '-';

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: userTimeZone
  }).format(date);
};

const latestExecution = (items: ExecutionRecord[] = []) => items[0] || null;

const executionRows = (execution: ExecutionRecord) =>
  [
    ['Execution ID', execution.execution_id],
    ['Job ID', execution.job_id],
    ['觸發方式', execution.trigger_type],
    ['狀態', execution.status],
    ['排入時間', formatDate(execution.created_at)],
    ['開始時間', formatDate(execution.start_time)],
    ['結束時間', formatDate(execution.end_time)],
    ['執行秒數', execution.duration ?? '-'],
    ['Worker', execution.worker_id || '-'],
    ['重試次數', execution.retry_count],
    ['錯誤訊息', execution.error_message || '-']
  ] as const;

export const JobMonitor = ({ scope }: JobMonitorProps) => {
  const [jobs, setJobs] = useState<BackendJob[]>([]);
  const [executionsByJob, setExecutionsByJob] = useState<Record<number, ExecutionRecord[]>>({});
  const [jobStatusFilter, setJobStatusFilter] = useState('');
  const [scheduleFilter, setScheduleFilter] = useState('');
  const [resultFilter, setResultFilter] = useState('');
  const [search, setSearch] = useState('');
  const [logContent, setLogContent] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [modalJob, setModalJob] = useState<BackendJob | null>(null);
  const user = getStoredUser();
  const isOperator = scope === 'operator';

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const latest = latestExecution(executionsByJob[job.job_id]);
      const matchesStatus = !jobStatusFilter || job.status === jobStatusFilter;
      const matchesSchedule = !scheduleFilter || job.schedule_type === scheduleFilter;
      const matchesResult = !resultFilter || latest?.status === resultFilter;
      const matchesSearch =
        !search ||
        `${job.job_name} ${job.endpoint} ${job.job_id}`
          .toLowerCase()
          .includes(search.toLowerCase());
      return matchesStatus && matchesSchedule && matchesResult && matchesSearch;
    });
  }, [executionsByJob, jobs, jobStatusFilter, resultFilter, scheduleFilter, search]);

  const loadExecutionsForJobs = useCallback(async (jobList: BackendJob[]) => {
    const pairs = await Promise.all(
      jobList.map(async (job) => {
        try {
          const history = await listJobExecutions(job.job_id);
          return [job.job_id, history.items] as const;
        } catch {
          return [job.job_id, []] as const;
        }
      })
    );
    setExecutionsByJob(Object.fromEntries(pairs));
  }, []);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      const data = await listJobs();
      setJobs(data);
      await loadExecutionsForJobs(data);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '無法載入 Job');
    } finally {
      setLoading(false);
    }
  }, [loadExecutionsForJobs]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const handleTrigger = async (jobId: number) => {
    const response = await triggerJob(jobId);
    if (!response.ok) {
      const data = await response.json();
      setMessage(data.detail || '手動觸發失敗');
      return;
    }
    setMessage(`Job ${jobId} 已送出手動觸發`);
    loadJobs();
  };

  const handleStatusChange = async (job: BackendJob) => {
    const nextStatus = job.status === 'Active' ? 'Disabled' : 'Active';
    const response = await updateJobStatus(job.job_id, nextStatus);
    if (!response.ok) {
      const data = await response.json();
      setMessage(data.detail || '狀態更新失敗');
      return;
    }
    setMessage(`Job ${job.job_id} 已更新為 ${nextStatus}`);
    loadJobs();
  };

  const handleRerun = async (execution: ExecutionRecord) => {
    const response = await rerunExecution(execution.execution_id);
    if (!response.ok) {
      const data = await response.json();
      setMessage(data.detail || '重跑失敗');
      return;
    }
    setMessage(`Execution ${execution.execution_id} 已排入重跑`);
    loadJobs();
  };

  const openResultModal = async (job: BackendJob) => {
    setModalJob(job);
    setLogContent('');
    const latest = latestExecution(executionsByJob[job.job_id]);
    if (!latest) return;

    try {
      const content = await getExecutionLogContent(latest.execution_id);
      setLogContent(isOperator ? content : content.split('\n').slice(0, 20).join('\n'));
    } catch {
      setLogContent(latest.error_message || 'No log content available');
    }
  };

  const closeModal = () => {
    setModalJob(null);
    setLogContent('');
  };

  const modalExecutions = modalJob ? executionsByJob[modalJob.job_id] || [] : [];
  const modalLatest = latestExecution(modalExecutions);

  return (
    <div style={operatorStyles.container}>
      <div style={operatorStyles.dashboardCard}>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <div>
            <h2 style={operatorStyles.title}>
              {isOperator ? '維運人員專區 / 維運監控儀表板' : '內部開發者專區 / 我的 Job'}
            </h2>
            <p style={operatorStyles.subtitle}>
              {isOperator
                ? '查看 Job 狀態、手動觸發 Job、重新整理 Job 清單。'
                : `查看自己建立的 Job、執行狀態與基本 log${user ? ` - ${user.username}` : ''}。`}
            </p>
            <p style={{ ...operatorStyles.detailText, margin: 0 }}>
              顯示時間依照你的瀏覽器時區：{userTimeZone}
            </p>
          </div>
          <button className="btn btn-outline-secondary btn-sm" onClick={loadJobs}>
            {loading ? '載入中...' : '重新整理'}
          </button>
        </div>

        <div className="row g-2 mb-3">
          <div className="col-md-3">
            <input
              className="form-control"
              placeholder="搜尋名稱、Endpoint、ID"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <div className="col-md-3">
            <select
              className="form-select"
              value={jobStatusFilter}
              onChange={(event) => setJobStatusFilter(event.target.value)}
            >
              <option value="">所有 Job 狀態</option>
              <option value="Active">Active</option>
              <option value="Disabled">Disabled</option>
              <option value="Deleted">Deleted</option>
            </select>
          </div>
          <div className="col-md-3">
            <select
              className="form-select"
              value={scheduleFilter}
              onChange={(event) => setScheduleFilter(event.target.value)}
            >
              <option value="">所有排程類型</option>
              <option value="One-time">One-time</option>
              <option value="Recurring">Recurring</option>
            </select>
          </div>
          <div className="col-md-3">
            <select
              className="form-select"
              value={resultFilter}
              onChange={(event) => setResultFilter(event.target.value)}
            >
              <option value="">所有最新結果</option>
              <option value="Pending">Pending</option>
              <option value="Running">Running</option>
              <option value="Success">Success</option>
              <option value="Failed">Failed</option>
              <option value="Timeout">Timeout</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {message && <div className="alert alert-info py-2">{message}</div>}

        <div className="table-responsive">
          <table style={operatorStyles.jobTable}>
            <thead>
              <tr>
                <th style={operatorStyles.th}>ID</th>
                <th style={operatorStyles.th}>Job 名稱</th>
                <th style={operatorStyles.th}>Endpoint</th>
                <th style={operatorStyles.th}>排程</th>
                <th style={operatorStyles.th}>Job 狀態</th>
                <th style={operatorStyles.th}>最新結果</th>
                <th style={operatorStyles.th}>下次執行</th>
                <th style={{ ...operatorStyles.th, width: '160px' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredJobs.map((job) => {
                const latest = latestExecution(executionsByJob[job.job_id]);
                return (
                  <tr key={job.job_id}>
                    <td style={operatorStyles.td}>{job.job_id}</td>
                    <td style={operatorStyles.td}>{job.job_name}</td>
                    <td style={operatorStyles.td}>
                      <span style={operatorStyles.badge(job.method)}>{job.method}</span>
                      <span style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                        {job.endpoint}
                      </span>
                    </td>
                    <td style={operatorStyles.td}>
                      {job.schedule_type}
                      <div style={operatorStyles.detailText}>{job.cron_expression || '-'}</div>
                    </td>
                    <td style={operatorStyles.td}>{job.status}</td>
                    <td style={operatorStyles.td}>
                      {latest ? (
                        <>
                          <strong>{latest.status}</strong>
                          <div style={operatorStyles.detailText}>
                            {formatDate(latest.created_at)}
                          </div>
                        </>
                      ) : (
                        '尚無結果'
                      )}
                    </td>
                    <td style={operatorStyles.td}>{formatDate(job.next_run_time)}</td>
                    <td style={operatorStyles.td}>
                      <div className="d-flex flex-wrap gap-1">
                        <button
                          className="btn btn-primary btn-sm"
                          disabled={job.status !== 'Active'}
                          onClick={() => handleTrigger(job.job_id)}
                        >
                          手動觸發
                        </button>
                        <button
                          className="btn btn-outline-secondary btn-sm"
                          onClick={() => openResultModal(job)}
                        >
                          顯示結果
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {filteredJobs.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ ...operatorStyles.td, textAlign: 'center' }}>
                    目前沒有符合條件的 Job。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {modalJob && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            zIndex: 1000
          }}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '8px',
              width: 'min(900px, 100%)',
              maxHeight: '85vh',
              overflow: 'auto',
              padding: '24px',
              boxShadow: '0 8px 30px rgba(0,0,0,0.2)'
            }}
          >
            <div className="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h3 style={{ margin: 0 }}>{modalJob.job_name}</h3>
                <div style={operatorStyles.detailText}>
                  Job #{modalJob.job_id} | {modalJob.method} {modalJob.endpoint}
                </div>
              </div>
              <button className="btn btn-outline-secondary btn-sm" onClick={closeModal}>
                關閉
              </button>
            </div>

            <div className="row g-3 mb-3">
              <div className="col-md-4">
                <strong>Job 狀態</strong>
                <div>{modalJob.status}</div>
              </div>
              <div className="col-md-4">
                <strong>最新結果</strong>
                <div>{modalLatest?.status || '尚無結果'}</div>
              </div>
              <div className="col-md-4">
                <strong>Job 建立時間</strong>
                <div>{formatDate(modalJob.created_at)}</div>
              </div>
            </div>

            {modalLatest && (
              <div className="mb-3">
                <strong>Execution 資訊</strong>
                <table className="table table-sm mt-2 mb-0">
                  <tbody>
                    {executionRows(modalLatest).map(([label, value]) => (
                      <tr key={label}>
                        <th style={{ width: '140px' }}>{label}</th>
                        <td>{value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mb-3">
              <strong>{isOperator ? '完整 log' : '基本 log'}</strong>
              <pre style={operatorStyles.codeBlock}>{logContent || 'No log content available'}</pre>
            </div>

            {isOperator && (
              <div className="d-flex flex-wrap gap-2">
                <button
                  className="btn btn-outline-warning btn-sm"
                  onClick={() => handleStatusChange(modalJob)}
                >
                  {modalJob.status === 'Active' ? '停用 Job' : '恢復 Job'}
                </button>
                {modalLatest && (
                  <button
                    className="btn btn-outline-primary btn-sm"
                    onClick={() => handleRerun(modalLatest)}
                  >
                    重跑最新 Execution
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
