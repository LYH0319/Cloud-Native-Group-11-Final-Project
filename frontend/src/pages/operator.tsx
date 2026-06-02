import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { operatorStyles, homeLoginLogoutStyles } from './Style';

interface JobDetail {
  scheduleRule: string;
  retryStrategy: string;
  dependencies: string[];
  eta: string;
  timeout: string;
  commandType: 'REST API' | 'Shell Script';
  command: string;
}

interface Job {
  job_id: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  endpoint: string;
  headers: {
    'Content-Type': string;
    Authorization: string;
  };
  details: JobDetail;
  status: '閒置中' | '執行中' | '執行成功' | '執行失敗';
  owner: string;
}

export const Operator = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const API_BASE_URL = 'http://localhost:8000/api';

  const fetchJobs = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/jobs`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'x-emp-id': user.id || ''
        }
      });

      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || data);
      } else {
        console.error('無法從資料庫取得 Job 狀態');
      }
    } catch (error) {
      console.error('連接後端伺服器失敗:', error);
    } finally {
      setLoading(false);
    }
  }, [user.id]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleManualTrigger = async (jobId: string) => {
    setJobs((prevJobs) =>
      prevJobs.map((job) => (job.job_id === jobId ? { ...job, status: '執行中' } : job))
    );

    try {
      const res = await fetch(`${API_BASE_URL}/jobs/${jobId}/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-emp-id': user.id || ''
        }
      });

      if (res.ok) {
        alert(`任務 ${jobId} 已成功手動觸發！`);
        fetchJobs();
      } else {
        alert('向後端發送觸發請求失敗，請重新確認伺服器狀態。');
        fetchJobs();
      }
    } catch (error) {
      console.error('手動觸發請求連線失敗:', error);
      alert('連線外網或後端失敗，無法觸發維運任務！');
      fetchJobs();
    }
  };

  return (
    <div className="bg-light min-vh-100">
      <div style={operatorStyles.header}>
        <span>Job scheduler System</span>

        <div className="d-flex flex-column align-items-end">
          <button
            className="btn btn-light btn-sm px-3 mb-2"
            onClick={() => {
              alert('登出成功！');
              localStorage.removeItem('user');
              navigate('/');
            }}
            style={homeLoginLogoutStyles.style}
          >
            登出
          </button>

          <h2 className="fs-5 m-0 font-weight-bold">維運人員專區</h2>
        </div>
      </div>

      <div style={operatorStyles.container}>
        <div style={operatorStyles.dashboardCard}>
          <h2 style={operatorStyles.title}>維運監控儀表板</h2>
          <p style={operatorStyles.subtitle}>
            負責系統排程監控、任務狀態查閱與手動緊急觸發維運工作
          </p>

          <div style={operatorStyles.systemStatus}>
            <div>
              運作狀態：正常 | 系統目前負載: <span style={{ color: '#1A73E8' }}>45%</span> | Worker
              節點數: 3 個
            </div>
            <button
              style={{
                ...operatorStyles.triggerBtn,
                backgroundColor: '#3c4043',
                borderRadius: '20px'
              }}
              onClick={() => alert('已發送擴充節點請求')}
            >
              擴充節點 (+)
            </button>
          </div>

          <div className="d-flex justify-content-between align-items-center mb-2">
            <h3 style={{ fontSize: '18px', color: '#00007A', margin: 0 }}>
              所有 Job 註冊與執行現況
            </h3>
            <button
              className="btn btn-outline-secondary btn-sm"
              onClick={fetchJobs}
              disabled={loading}
            >
              {loading ? '同步中...' : '🔄 手動重新整理'}
            </button>
          </div>

          <table style={operatorStyles.jobTable}>
            <thead>
              <tr>
                <th style={{ ...operatorStyles.th, width: '100px' }}>任務編號</th>
                <th style={{ ...operatorStyles.th, width: '280px' }}>API 節點資訊 (Endpoint)</th>
                <th style={{ ...operatorStyles.th, width: '22px' }}>標頭 (Headers)</th>
                <th style={{ ...operatorStyles.th, width: '260px' }}>核心執行配置 (Body Rules)</th>
                <th style={{ ...operatorStyles.th, width: '90px' }}>當前狀態</th>
                <th style={{ ...operatorStyles.th, width: '100px', textAlign: 'center' }}>
                  操作動作
                </th>
              </tr>
            </thead>
            <tbody>
              {loading && jobs.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    style={{ ...operatorStyles.td, textAlign: 'center', padding: '40px' }}
                  >
                    正在從後端資料庫載入數據中...
                  </td>
                </tr>
              ) : jobs.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    style={{
                      ...operatorStyles.td,
                      textAlign: 'center',
                      padding: '40px',
                      color: '#888'
                    }}
                  >
                    目前資料庫中無任何已註冊的 Job 任務。
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr key={job.job_id}>
                    <td style={operatorStyles.td}>
                      <strong style={{ fontSize: '15px' }}>{job.job_id}</strong>
                      <div
                        style={{ ...operatorStyles.detailText, fontSize: '11px', color: '#888' }}
                      >
                        建立者:
                        <br />
                        {job.owner}
                      </div>
                    </td>

                    <td style={operatorStyles.td}>
                      <span style={operatorStyles.badge(job.method)}>{job.method}</span>
                      <span style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                        {job.endpoint}
                      </span>
                    </td>

                    <td style={operatorStyles.td}>
                      <div style={operatorStyles.detailText}>
                        <strong>Content-Type:</strong> {job.headers?.['Content-Type'] || 'N/A'}
                      </div>
                      <div style={operatorStyles.detailText}>
                        <strong>Auth:</strong>{' '}
                        <span style={{ fontSize: '11px', color: '#999' }}>
                          {job.headers?.['Authorization'] ? '已配置' : '無'}
                        </span>
                      </div>
                    </td>

                    <td style={operatorStyles.td}>
                      <div style={operatorStyles.detailText}>
                        <strong>類型:</strong> {job.details?.commandType}
                      </div>
                      <div style={operatorStyles.detailText}>
                        <strong>指令內容:</strong>
                      </div>
                      <div style={operatorStyles.codeBlock}>{job.details?.command}</div>

                      <div style={{ ...operatorStyles.detailText, marginTop: '8px' }}>
                        ⏱️ <strong>排程規則:</strong> {job.details?.scheduleRule}
                      </div>
                      <div style={operatorStyles.detailText}>
                        🔄 <strong>重試策略:</strong> {job.details?.retryStrategy}
                      </div>
                      <div style={operatorStyles.detailText}>
                        ⏳ <strong>預估/超時:</strong> {job.details?.eta} / {job.details?.timeout}
                      </div>
                      {job.details?.dependencies && job.details.dependencies.length > 0 && (
                        <div style={{ ...operatorStyles.detailText, color: '#b06000' }}>
                          🔗 <strong>相依任務:</strong> {job.details.dependencies.join(', ')}
                        </div>
                      )}
                    </td>

                    <td style={operatorStyles.td}>
                      <span style={operatorStyles.statusBadge(job.status)}>{job.status}</span>
                    </td>

                    <td style={{ ...operatorStyles.td, textAlign: 'center' }}>
                      <button
                        style={{
                          ...operatorStyles.triggerBtn,
                          opacity: job.status === '執行中' ? 0.6 : 1,
                          cursor: job.status === '執行中' ? 'not-allowed' : 'pointer'
                        }}
                        disabled={job.status === '執行中'}
                        onClick={() => handleManualTrigger(job.job_id)}
                      >
                        {job.status === '執行中' ? '執行中...' : '手動觸發'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
