import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Styles from './Style';
import { type User, type JobBody } from '../types/types';

export const DeveloperAddRESTfulAPI = () => {
  const [method, setMethod] = useState('POST');
  const [endpoint, setEndpoint] = useState('');
  const [jsonBody, setJsonBody] = useState(
    '{\n  "command": "echo hello",\n  "schedule": "0 0 * * *",\n  "retry_policy": 3,\n  "timeout_seconds": 60\n}'
  );
  const navigate = useNavigate();

  const user: User = JSON.parse(localStorage.getItem('user') || '{}');

  const handleSubmit = async () => {
    try {
      const parsedBody: JobBody = JSON.parse(jsonBody);
      const payload = {
        method,
        endpoint,
        headers: { 'Content-Type': 'application/json' },
        body: parsedBody
      };

      const res = await fetch('http://localhost:8000/api/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-emp-id': user.id
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      alert(data.message || '建立成功');
    } catch (err) {
      alert('JSON 格式錯誤或連線失敗！');
    }
  };

  return (
    <div className="bg-light min-vh-100">
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>

        <div className="d-flex flex-column align-item-center">
          <div className="d-flex flex-raw">
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

      <div className="container mt-4">
        <h4>新增 RESTful API 任務</h4>
        <div className="row">
          <div>
            <input
              type="text"
              className="form-control mb-2"
              placeholder="Method (ex: POST)"
              value={method}
              onChange={(e) => setMethod(e.target.value)}
            />
            <input
              type="text"
              className="form-control mb-2"
              placeholder="Endpoint (ex: /v1/run)"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
            />
            <textarea
              className="form-control mb-2"
              rows={6}
              placeholder={`填入 JobBody JSON，例如:\n{\n  "command": "echo hello",\n  "schedule": "0 0 * * *",\n  "retry_policy": 3,\n  "timeout_seconds": 60\n}`}
              value={jsonBody}
              onChange={(e) => setJsonBody(e.target.value)}
            />
            <button onClick={handleSubmit} className="btn btn-success">
              註冊 Job
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
